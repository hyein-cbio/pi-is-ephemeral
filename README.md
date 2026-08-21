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
