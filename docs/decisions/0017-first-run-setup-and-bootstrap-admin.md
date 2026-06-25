# 17. First-run setup and bootstrap admin via console token

Date: 2026-06-23

## Status

Accepted

## Context

Vroom HR is a self-hosted single-company platform. Currently, configuring the system for the first time (setting the super admin email, Google OAuth credentials, allowed domains, and whitelist) requires manual edits to environment variables and configuration files (`.env`, `config/whitelist.txt`). This violates our goal of a modern, web-driven deployment trust model where administrators can initialize the system through the UI without manually touching server files.

Furthermore, we need a secure way to identify the true administrator during this first run before any Identity Provider (Google OAuth) is configured.

## Decision

We will implement a web-based Setup Wizard with the following architecture:

1. **SystemSetup Record**: A new entity in the `identity` module tracks `is_setup_completed`.
2. **Setup Gating**: On system startup, if `is_setup_completed` is false, all normal API routes will be blocked by a middleware returning `403 Setup Required`, forcing the frontend to redirect to the `/setup` flow.
3. **Bootstrap Security (Setup Token)**: The backend will generate a random, one-time `SETUP_TOKEN` and print it to the server console log. The admin must enter this token into the web UI. This proves they have access to the host server environment.
4. **Setup Session**: Validating the token grants a temporary, limited Setup Session allowing the admin to call `/api/setup/*` routes to configure Organization details, Access Controls, and Google OAuth credentials.
5. **Test Login Before Lock**: To prevent lockout (e.g., misconfigured OAuth or wrong email), the admin must successfully complete a "Test Login" via Google before the system permits locking the setup.
6. **Lock Setup**: Upon completion, `is_setup_completed` becomes true, the `SETUP_TOKEN` is permanently deleted, the Setup Session is invalidated, and the `/setup` APIs are permanently blocked.

## Consequences

- **Positive**: True web-based initial configuration; eliminates the need to manually edit `.env` for core business config.
- **Positive**: Setup Token provides high deployment trust without requiring local accounts.
- **Positive**: Test Login requirement eliminates the risk of an admin locking themselves out of their newly deployed system.
- **Negative**: Adds a slight complexity to the application startup and routing layers.
- **Backward Compatibility**: A database migration will automatically set `is_setup_completed = True` if existing users or configurations are found, ensuring current deployments are not disrupted.
