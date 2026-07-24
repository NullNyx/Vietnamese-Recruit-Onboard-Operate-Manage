"""Override admin credentials to match E2E test expectations.

Run after seed_all.py to set the admin email/password that
login-setup.spec.ts expects.

Usage:
    cd backend && python scripts/override_admin_for_e2e.py
"""
from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from sqlalchemy import create_engine, text

from src.modules.identity.infrastructure.config import AuthSettings
from src.modules.identity.infrastructure.password_utils import hash_password


def main() -> None:
    settings = AuthSettings()
    url = settings.database_url
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("+asyncpg", "", 1)

    engine = create_engine(url)
    conn = engine.connect()
    conn.execute(
        text(
            "UPDATE users SET email=:email, name=:name, password_hash=:pwd WHERE role='admin'"
        ),
        {
            "email": "hr.qa@vroom.example.com",
            "name": "HR QA",
            "pwd": hash_password("VroomQA!148#2026"),
        },
    )
    conn.commit()
    conn.close()
    print("Admin credentials updated for E2E tests.")


if __name__ == "__main__":
    main()
