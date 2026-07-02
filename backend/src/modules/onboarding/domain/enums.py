"""Domain enums and the checklist template for the Onboarding module.

Defines the enumeration types used across the onboarding module for the
overall onboarding process status, individual onboarding task status, and the
stable keys identifying each task in the fixed checklist. Also defines the
canonical ``CHECKLIST_TEMPLATE`` describing the four onboarding tasks created
for every onboarding process, in their fixed order.
"""

from enum import StrEnum
from typing import Final


class OnboardingStatus(StrEnum):
    """Overall status of an onboarding process.

    An onboarding process starts ``in_progress``, becomes
    ``ready_for_completion`` when every task is done and setup is complete,
    and reaches ``complete`` only after HR explicitly confirms completion.
    """

    IN_PROGRESS = "in_progress"
    READY_FOR_COMPLETION = "ready_for_completion"
    COMPLETE = "complete"


class OnboardingTaskStatus(StrEnum):
    """Status of a single onboarding task.

    Each onboarding task is restricted to exactly one of these two values.
    """

    PENDING = "pending"
    DONE = "done"


class OnboardingContractStatus(StrEnum):
    """Status of onboarding contract draft."""

    DRAFT = "draft"
    READY = "ready"
    SENT = "sent"
    SIGNED = "signed"


class OnboardingTaskKey(StrEnum):
    """Stable keys for the four fixed onboarding checklist tasks.

    The keys are fixed and ordered; they identify each task independently of
    its human-readable display name.
    """

    SIGN_CONTRACT = "sign_contract"
    SUBMIT_DOCUMENTS = "submit_documents"
    ASSIGN_DEPARTMENT_POSITION_MANAGER = "assign_department_position_manager"
    SET_START_DATE = "set_start_date"


# The canonical onboarding checklist: an ordered list of
# (order_index, task_key, display_name) tuples. Every onboarding process is
# created with exactly these four tasks, in this exact order.
CHECKLIST_TEMPLATE: Final[list[tuple[int, OnboardingTaskKey, str]]] = [
    (0, OnboardingTaskKey.SIGN_CONTRACT, "Sign Contract"),
    (1, OnboardingTaskKey.SUBMIT_DOCUMENTS, "Submit Documents"),
    (2, OnboardingTaskKey.ASSIGN_DEPARTMENT_POSITION_MANAGER, "Assign Department Position Manager"),
    (3, OnboardingTaskKey.SET_START_DATE, "Set Start Date"),
]

# ─── Document Types ───────────────────────────────────────────────────────
# The canonical onboarding document checklist: an ordered list of
# (document_type, display_name, is_required) tuples. Each process is created
# with exactly these document items, in this order.

DOCUMENT_TEMPLATE: Final[list[tuple[str, str, bool]]] = [
    ("cccd", "Căn cước công dân", True),
    ("degree", "Bằng cấp / Chứng chỉ", True),
    ("health_cert", "Giấy khám sức khỏe", True),
    ("resume", "Sơ yếu lý lịch", True),
    ("photo", "Ảnh thẻ", False),
    ("insurance", "Sổ bảo hiểm xã hội", True),
    ("diploma", "Bằng tốt nghiệp", True),
    ("other", "Giấy tờ khác", False),
]
