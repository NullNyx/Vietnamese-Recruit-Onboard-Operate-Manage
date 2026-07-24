"""Seed Google connection audit logs with Vietnamese descriptions.

Tạo dữ liệu mẫu audit log tiếng Việt cho tất cả action type Google connection,
bao gồm cả ``org_google_calendar_select`` (action type mới).

Dữ liệu sinh ra dùng để verify frontend hiển thị audit log tiếng Việt
và backward compatibility của ``valueMap`` với bản ghi cũ (English format).

Usage:
    cd backend
    python -m scripts.seed_google_audit_logs

Hoặc dùng trực tiếp SQL:
    docker exec -i vroom-postgres psql -U postgres -d vroom_hr < backend/scripts/seed_google_audit_logs.sql
"""

from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_SQL_FILE = _SCRIPT_DIR / "seed_google_audit_logs.sql"


async def seed_google_audit_logs() -> bool:
    """Run the idempotent SQL seed via psql in the vroom-postgres container."""
    if not _SQL_FILE.exists():
        print(f"❌ Không tìm thấy {_SQL_FILE}", file=sys.stderr)
        return False

    result = subprocess.run(
        [
            "docker",
            "exec",
            "-i",
            "vroom-postgres",
            "psql",
            "-U",
            "postgres",
            "-d",
            "vroom_hr",
        ],
        stdin=_SQL_FILE.open("rb"),
        capture_output=True,
        text=False,
    )

    # psql outputs notices to stderr
    stderr_text = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""
    stdout_text = result.stdout.decode("utf-8", errors="replace") if result.stdout else ""

    if result.returncode != 0:
        print(f"❌ psql exited with {result.returncode}", file=sys.stderr)
        if stderr_text:
            print(stderr_text, file=sys.stderr)
        return False

    # Print psql notices (RAISE NOTICE messages come via stderr)
    for line in stderr_text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("psql:"):
            print(stripped)

    if stdout_text.strip():
        print(stdout_text.strip())

    return True


def main() -> None:
    success = asyncio.run(seed_google_audit_logs())
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
