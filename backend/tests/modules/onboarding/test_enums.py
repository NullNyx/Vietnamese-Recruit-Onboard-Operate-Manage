"""Unit tests for onboarding domain enums and the checklist template.

Validates Requirements 3.1, 3.2, 3.3:
- The checklist has exactly four tasks in the fixed order with correct names.
- New onboarding tasks are created ``pending`` (the template only carries the
  task identity; ``pending`` is its initial status, enforced here via the enum).
- Task and process status enums contain only their allowed values.
"""

from src.modules.onboarding.domain.enums import (
    CHECKLIST_TEMPLATE,
    OnboardingStatus,
    OnboardingTaskKey,
    OnboardingTaskStatus,
)


class TestOnboardingStatus:
    """Tests for the OnboardingStatus enum (Requirement 6.x process status)."""

    def test_contains_only_allowed_values(self):
        """OnboardingStatus has exactly the two allowed values."""
        assert {s.value for s in OnboardingStatus} == {"in_progress", "complete"}

    def test_exactly_two_members(self):
        """OnboardingStatus defines exactly two members."""
        assert len(list(OnboardingStatus)) == 2

    def test_member_values(self):
        """Each member maps to its expected string value."""
        assert OnboardingStatus.IN_PROGRESS == "in_progress"
        assert OnboardingStatus.COMPLETE == "complete"

    def test_is_str_enum(self):
        """Members are plain strings (StrEnum) for DB storage / serialization."""
        assert isinstance(OnboardingStatus.IN_PROGRESS, str)
        assert OnboardingStatus.COMPLETE.value == "complete"


class TestOnboardingTaskStatus:
    """Tests for the OnboardingTaskStatus enum (Requirement 3.3)."""

    def test_contains_only_allowed_values(self):
        """Task status is restricted to exactly ``pending`` and ``done``."""
        assert {s.value for s in OnboardingTaskStatus} == {"pending", "done"}

    def test_exactly_two_members(self):
        """OnboardingTaskStatus defines exactly two members."""
        assert len(list(OnboardingTaskStatus)) == 2

    def test_member_values(self):
        """Each member maps to its expected string value."""
        assert OnboardingTaskStatus.PENDING == "pending"
        assert OnboardingTaskStatus.DONE == "done"

    def test_is_str_enum(self):
        """Members are plain strings (StrEnum) for DB storage / serialization."""
        assert isinstance(OnboardingTaskStatus.PENDING, str)
        assert OnboardingTaskStatus.DONE.value == "done"


class TestOnboardingTaskKey:
    """Tests for the OnboardingTaskKey enum (the four fixed checklist keys)."""

    def test_contains_only_allowed_values(self):
        """Task keys are exactly the four fixed checklist keys."""
        assert {k.value for k in OnboardingTaskKey} == {
            "sign_contract",
            "submit_documents",
            "assign_department_position_manager",
            "set_start_date",
        }

    def test_exactly_four_members(self):
        """OnboardingTaskKey defines exactly four members."""
        assert len(list(OnboardingTaskKey)) == 4

    def test_is_str_enum(self):
        """Members are plain strings (StrEnum) for DB storage / serialization."""
        assert isinstance(OnboardingTaskKey.SIGN_CONTRACT, str)
        assert OnboardingTaskKey.SET_START_DATE.value == "set_start_date"


class TestChecklistTemplate:
    """Tests for the CHECKLIST_TEMPLATE constant (Requirements 3.1, 3.2)."""

    def test_has_exactly_four_entries(self):
        """The checklist template contains exactly four tasks (R3.1)."""
        assert len(CHECKLIST_TEMPLATE) == 4

    def test_order_indexes_are_zero_to_three_in_sequence(self):
        """Order indexes run 0, 1, 2, 3 matching the entry position (R3.1)."""
        order_indexes = [order_index for order_index, _, _ in CHECKLIST_TEMPLATE]
        assert order_indexes == [0, 1, 2, 3]

    def test_task_keys_in_required_order(self):
        """Task keys appear in the fixed required order (R3.1)."""
        task_keys = [task_key for _, task_key, _ in CHECKLIST_TEMPLATE]
        assert task_keys == [
            OnboardingTaskKey.SIGN_CONTRACT,
            OnboardingTaskKey.SUBMIT_DOCUMENTS,
            OnboardingTaskKey.ASSIGN_DEPARTMENT_POSITION_MANAGER,
            OnboardingTaskKey.SET_START_DATE,
        ]

    def test_display_names_in_required_order(self):
        """Display names match the spec, in the required order (R3.1)."""
        display_names = [display_name for _, _, display_name in CHECKLIST_TEMPLATE]
        assert display_names == [
            "Sign Contract",
            "Submit Documents",
            "Assign Department Position Manager",
            "Set Start Date",
        ]

    def test_full_template_structure(self):
        """The complete template matches the canonical (index, key, name) tuples."""
        assert CHECKLIST_TEMPLATE == [
            (0, OnboardingTaskKey.SIGN_CONTRACT, "Sign Contract"),
            (1, OnboardingTaskKey.SUBMIT_DOCUMENTS, "Submit Documents"),
            (
                2,
                OnboardingTaskKey.ASSIGN_DEPARTMENT_POSITION_MANAGER,
                "Assign Department Position Manager",
            ),
            (3, OnboardingTaskKey.SET_START_DATE, "Set Start Date"),
        ]

    def test_task_keys_are_unique(self):
        """No task key is repeated within the checklist."""
        task_keys = [task_key for _, task_key, _ in CHECKLIST_TEMPLATE]
        assert len(set(task_keys)) == len(task_keys)

    def test_template_covers_every_task_key(self):
        """Every defined OnboardingTaskKey appears exactly once in the template."""
        task_keys = {task_key for _, task_key, _ in CHECKLIST_TEMPLATE}
        assert task_keys == set(OnboardingTaskKey)
