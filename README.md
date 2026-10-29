# pi-is-ephemeral

A minimal Pi extension that displays `ephemeral` in Pi's built-in footer whenever the current session is non-persistent. It adds its own named status entry and does not replace the built-in footer or overwrite other extensions' statuses.

The extension checks `ctx.sessionManager.getSessionFile()` on every `session_start`, so it updates after startup, `/new`, session resume or switching, and reload. It uses the session manager as the source of truth rather than inspecting CLI flags.

## Install

```sh
pi install npm:pi-is-ephemeral
```

## Try temporarily

```sh
pi -e npm:pi-is-ephemeral --no-session
```

## Remove

```sh
pi remove npm:pi-is-ephemeral
```

## Test

Unit tests require Node.js 22.19+; no dependency installation is needed.

```sh
npm test
```

### Latest Pi compatibility

The [compatibility workflow](.github/workflows/latest-pi.yml) runs on the 1st of every month at 15:00 UTC (00:00 KST on the 2nd), or manually from the Actions tab. Each run installs the current npm `latest` Pi release without a lockfile, logs its version, and runs both the unit and integration tests on the latest Node.js LTS. No API keys, automatic fixes, or PR creation are involved.

The integration tests launch the real Pi CLI in RPC mode and load this package through its manifest. They verify status updates for ephemeral and persistent startup, new sessions, and resuming a saved session (including clearing a stale `ephemeral` label). They use isolated temporary settings and sessions, run Pi offline, and make no model requests. They check Pi's actual status API output, not terminal pixel rendering; the unit test additionally checks that other extensions' statuses are preserved.

To run the same checks locally (macOS/Linux):

```sh
npm install --no-save --package-lock=false --ignore-scripts @earendil-works/pi-coding-agent@latest
npm test
npm run test:integration
```

GitHub schedules run from the default branch and can be delayed. For public repositories, GitHub automatically disables scheduled workflows after 60 days without repository activity; re-enable the workflow in Actions if needed.
