import assert from "node:assert/strict";
import test from "node:test";
import extension from "../extensions/ephemeral-footer.ts";

test("updates ephemeral status across session changes and preserves other statuses", async () => {
	const handlers = new Map();
	extension({
		on(event, handler) {
			handlers.set(event, handler);
		},
	});
	assert.deepEqual([...handlers.keys()], ["session_start"]);

	let sessionFile;
	const statuses = new Map([["other-extension", "keep me"]]);
	const ctx = {
		sessionManager: { getSessionFile: () => sessionFile },
		ui: {
			setStatus(key, text) {
				if (text === undefined) statuses.delete(key);
				else statuses.set(key, text);
			},
		},
	};

	for (const file of [undefined, "/sessions/persistent.jsonl", undefined]) {
		sessionFile = file;
		await handlers.get("session_start")({ type: "session_start" }, ctx);
		const expected = new Map([["other-extension", "keep me"]]);
		if (file === undefined) expected.set("ephemeral-session", "ephemeral");
		assert.deepEqual(statuses, expected);
	}
});
