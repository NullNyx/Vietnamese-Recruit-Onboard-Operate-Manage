"""Seed the Vroom HR database with realistic test emails for all 15 HR categories.

Inserts EmailMessage records directly into the database (bypassing Gmail sync).
For recruitment emails, also creates CVDocument records and uploads CV PDFs to MinIO.
The classification pipeline picks up ``processing_status = "unprocessed"`` records
on the next poll cycle or manual classify trigger.

Usage::

    cd backend
    python -m scripts.seed_db --dry-run
    python -m scripts.seed_db
    python -m scripts.seed_db --categories recruitment interview
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import io
import os
import random
import sys
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Reuse the CV generators from seed_gmail
from scripts.seed_gmail import (
    _ALL_GENERATORS,
    _CANDIDATE_PROFILES,
    _generate_cv_pdf,
    _build_mime,
)

from src.modules.gmail.domain.entities import EmailMessage
from src.modules.recruitment.domain.entities import CVDocument
from src.modules.recruitment.domain.enums import ProcessingStatus
from src.modules.recruitment.infrastructure.config import RecruitmentSettings
from src.modules.recruitment.infrastructure.minio_client import RecruitmentMinIOClient
from src.modules.identity.infrastructure.config import AuthSettings


async def _get_first_user_id(session: AsyncSession) -> UUID:
    """Get the first user's UUID from the database."""
    from src.modules.identity.domain.entities import User
    result = await session.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    if user is None:
        raise RuntimeError("No users found in database. Create a super admin first.")
    return user.id


def _extract_mime_info(mime_bytes: bytes) -> dict:
    """Extract key fields from a MIME message bytes."""
    from email.parser import BytesParser
    from email.policy import default as default_policy
    import email

    msg = BytesParser(policy=default_policy).parsebytes(mime_bytes)

    sender_name = ""
    sender_email_addr = ""
    if msg["From"]:
        from_addr = email.utils.parseaddr(msg["From"])
        sender_name = from_addr[0] or ""
        sender_email_addr = from_addr[1] or ""

    subject = msg["Subject"] or ""
    body_text = ""
    has_attachments = False

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain" and not body_text:
                payload = part.get_payload(decode=True)
                if payload:
                    body_text = payload.decode("utf-8", errors="replace")
            disp = part.get_content_disposition() or ""
            if disp.startswith("attachment"):
                has_attachments = True
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            body_text = payload.decode("utf-8", errors="replace")

    snippet = body_text[:200].replace("\n", " ").strip() if body_text else ""

    return {
        "subject": subject,
        "sender_name": sender_name,
        "sender_email": sender_email_addr,
        "snippet": snippet,
        "has_attachments": has_attachments,
    }


async def main() -> None:
    parser = argparse.ArgumentParser(description="Seed DB with test HR emails")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would be inserted without writing to DB")
    parser.add_argument("--categories", type=str, nargs="*",
                        help="Specific categories (default: all)")
    parser.add_argument("--skip-minio", action="store_true",
                        help="Skip MinIO CV uploads (CV PDFs not stored)")
    args = parser.parse_args()

    selected = set(args.categories) if args.categories else set(_ALL_GENERATORS)
    generators = {k: v for k, v in _ALL_GENERATORS.items() if k in selected}
    if not generators:
        print("No matching categories.", file=sys.stderr)
        sys.exit(1)

    # Build email list
    all_emails: list[tuple[str, str, bytes]] = []  # (category, label, mime)
    for cat, gen_fn in generators.items():
        batch = gen_fn()
        for _, mime in batch:
            all_emails.append((cat, cat, mime))

    if args.dry_run:
        for cat, _, _ in all_emails:
            print(f"[DRY-RUN] {cat}")
        print(f"\nWould insert {len(all_emails)} EmailMessage records.")
        return

    # Load settings
    auth_settings = AuthSettings()  # type: ignore[call-arg]
    rec_settings = RecruitmentSettings()  # type: ignore[call-arg]

    engine = create_async_engine(auth_settings.database_url, echo=False)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_maker() as session:
        user_id = await _get_first_user_id(session)
        print(f"✓ User: {user_id}")

    # MinIO client for CV uploads
    minio = RecruitmentMinIOClient(rec_settings) if not args.skip_minio else None

    inserted = 0
    cv_uploaded = 0
    errors = 0

    async with session_maker() as session:
        for i, (cat, _, mime_bytes) in enumerate(all_emails, 1):
            try:
                info = _extract_mime_info(mime_bytes)
                now = datetime.now(UTC)
                gmail_msg_id = f"seed-{uuid4().hex[:16]}"
                gmail_thread_id = f"thread-{uuid4().hex[:16]}"

                email = EmailMessage(
                    user_id=user_id,
                    gmail_message_id=gmail_msg_id,
                    gmail_thread_id=gmail_thread_id,
                    subject=info["subject"],
                    sender_email=info["sender_email"],
                    sender_name=info["sender_name"],
                    recipient_emails=["erajewel.dev@gmail.com"],
                    received_at=now,
                    snippet=info["snippet"],
                    label_ids=["INBOX", "UNREAD"],
                    has_attachments=info["has_attachments"],
                    processing_status="unprocessed",
                )
                session.add(email)
                await session.flush()  # Get the email.id

                # For recruitment emails with attachments, create CVDocument + upload to MinIO
                if cat == "recruitment" and info["has_attachments"] and minio is not None:
                    # Extract CV attachment data from MIME
                    from email.parser import BytesParser
                    from email.policy import default as default_policy
                    msg = BytesParser(policy=default_policy).parsebytes(mime_bytes)
                    for part in msg.walk():
                        disp = part.get_content_disposition() or ""
                        if disp.startswith("attachment") and part.get_content_type() == "application/pdf":
                            cv_bytes = part.get_payload(decode=True)
                            if cv_bytes:
                                filename = part.get_filename() or "CV.pdf"
                                checksum = hashlib.sha256(cv_bytes).hexdigest()

                                try:
                                    file_path = await minio.upload_cv(
                                        file_data=cv_bytes,
                                        gmail_message_id=gmail_msg_id,
                                        sanitized_filename=filename,
                                        content_type="application/pdf",
                                    )
                                except Exception as exc:
                                    print(f"  ⚠ MinIO upload failed for {filename}: {exc}")
                                    file_path = f"storage/cv/{gmail_msg_id}/{filename}"

                                cv_doc = CVDocument(
                                    gmail_message_id=gmail_msg_id,
                                    original_filename=filename,
                                    mime_type="application/pdf",
                                    size_bytes=len(cv_bytes),
                                    file_path=file_path,
                                    checksum=checksum,
                                    processing_status=ProcessingStatus.PENDING,
                                )
                                session.add(cv_doc)
                                cv_uploaded += 1
                                break

                await session.commit()
                print(f"[{i:3d}/{len(all_emails)}] ✓ {cat:20s} | {info['sender_email']:40s} | {info['subject'][:50]}")
                inserted += 1

            except Exception as exc:
                await session.rollback()
                print(f"[{i:3d}/{len(all_emails)}] ✗ {cat:20s} | {exc}")
                errors += 1

    await engine.dispose()

    print(f"\nDone: {inserted} emails inserted, {cv_uploaded} CVs uploaded, {errors} errors.")
    if inserted > 0:
        print("Classification pipeline will pick up unprocessed emails on next poll cycle.")
        print("Or trigger manually via the classify API endpoint.")


if __name__ == "__main__":
    asyncio.run(main())
