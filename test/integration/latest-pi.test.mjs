import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { CURRENT_SESSION_VERSION, RpcClient, VERSION } from "@earendil-works/pi-coding-agent";

const packageRoot = fileURLToPath(new URL("../../", import.meta.url));
const cliPath = fileURLToPath(new URL("../../node_modules/.bin/pi", import.meta.url));

for (const ephemeral of [true, false]) {
	test(`Pi ${VERSION}: ${ephemeral ? "ephemeral" : "persistent"} startup, new session, and resume`, { timeout: 90_000 }, async (t) => {
		const dir = await mkdtemp(join(tmpdir(), "pi-is-ephemeral-"));
		const client = new RpcClient({
			cliPath,
			cwd: dir,
			env: { PI_CODING_AGENT_DIR: join(dir, "agent"), PI_OFFLINE: "1" },
			args: [
				"--no-extensions", "--no-skills", "--no-prompt-templates",
				"--no-themes", "--no-context-files",
				"--session-dir", join(dir, "sessions"),
				// Load the package directory, exercising its pi.extensions manifest too.
				"--extension", packageRoot,
				...(ephemeral ? ["--no-session"] : []),
			],
		});
		t.after(async () => {
			try {
				await client.stop();
			} finally {
				await rm(dir, { recursive: true, force: true });
			}
		});

		// Listen before startup: session_start may fire before start() resolves.
		const events = [];
		client.onEvent((event) => events.push(event));
		function assertStatusSince(offset, text) {
			const statuses = events.slice(offset).filter((event) =>
				event.type === "extension_ui_request" && event.method === "setStatus");
			assert.ok(statuses.length > 0, `No status update from Pi. Stderr: ${client.getStderr()}`);
			for (const status of statuses) {
				assert.equal(status.statusKey, "ephemeral-session");
				assert.equal(status.statusText, text);
			}
			assert.deepEqual(events.filter((event) => event.type === "extension_error"), []);
		}

		await client.start();
		// getState is a readiness barrier: Pi binds extensions before serving RPC commands.
		const initial = await client.getState();
		assert.equal(!initial.sessionFile, ephemeral);
		assertStatusSince(0, ephemeral ? "ephemeral" : undefined);

		let offset = events.length;
		assert.equal((await client.newSession()).cancelled, false);
		const fresh = await client.getState();
		assert.notEqual(fresh.sessionId, initial.sessionId);
		assert.equal(!fresh.sessionFile, ephemeral);
		assertStatusSince(offset, ephemeral ? "ephemeral" : undefined);

		// A valid empty saved session; no model request or API key is needed.
		const savedPath = join(dir, "saved.jsonl");
		const savedId = randomUUID();
		await writeFile(savedPath, `${JSON.stringify({
			type: "session", version: CURRENT_SESSION_VERSION, id: savedId,
			timestamp: new Date().toISOString(), cwd: dir,
		})}\n`);
		offset = events.length;
		assert.equal((await client.switchSession(savedPath)).cancelled, false);
		const resumed = await client.getState();
		assert.equal(resumed.sessionId, savedId);
		assert.equal(resumed.sessionFile, savedPath);
		// In particular, resuming a saved session clears a stale ephemeral label.
		assertStatusSince(offset, undefined);
	});
}
