# Authentication & Initial Setup

## Goal

The system is designed for **self-hosted deployment**. It is an **internal HR platform**, not a public SaaS application.

Only **HR/Admin** users access the system. **Employees do not have accounts and cannot log in.**

## Authentication

### Initial Setup

When the system starts for the first time and no administrator exists:

* Redirect all requests to the **Initial Setup Wizard**.
* Allow creation of the **first administrator account**.
* The first account is assigned the `SUPER_ADMIN` role.
* After setup completes, the setup endpoint is permanently disabled unless explicitly reset by the system owner.

### Login

After initialization:

* Authentication is available only through the **Login** page.
* Users authenticate with **username/email + password**.
* Public registration is **not supported**.

### User Management

Only `SUPER_ADMIN` can create additional system users.

Suggested roles:

* `SUPER_ADMIN`
* `HR_ADMIN`
* `HR_STAFF`
* `READ_ONLY` (optional for future expansion)

## Initial Setup Wizard

Recommended setup flow:

1. Create first administrator account
2. Configure company information
3. Configure AI provider (OpenAI, Gemini, OpenAI-compatible endpoint, Local LLM, or Disabled)
4. Configure default contract templates (optional)
5. Import or create initial employee records (optional)
6. Finish setup and enter the dashboard

## Design Rules

* No public sign-up.
* No employee-facing accounts.
* HR/Admin are the only system actors.
* Every additional user must be created by an administrator.
* AI provider configuration is optional and can be modified later.
* The system must remain usable even when no AI provider is configured.
