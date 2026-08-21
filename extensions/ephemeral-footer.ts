import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
	pi.on("session_start", (_event, ctx) => {
		const isEphemeral = !ctx.sessionManager.getSessionFile();
		ctx.ui.setStatus("ephemeral-session", isEphemeral ? "ephemeral" : undefined);
	});
}
