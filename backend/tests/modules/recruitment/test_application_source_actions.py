"""Integration-style application tests for issue #185 source actions."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.modules.recruitment.application.inbox_service import (
    InboxService,
    SplitApplicant,
)
from src.modules.recruitment.domain.entities import (
    JobApplication,
    JobApplicationLinkProposal,
    RecruitmentInboxItem,
)
from src.modules.recruitment.domain.enums import (
    ApplicationSource,
    InboxStatus,
    LinkProposalStatus,
)
from src.modules.recruitment.infrastructure.repositories import (
    JobApplicationLinkProposalRepository,
    JobApplicationRepository,
    RecruitmentInboxItemRepository,
)


def _inbox_item() -> RecruitmentInboxItem:
    return RecruitmentInboxItem(
        source_email_message_id=uuid4(),
        gmail_message_id="msg_agency_batch",
        gmail_thread_id="thread_agency_batch",
        sender_name="Agency Recruiter",
        sender_email="recruiter@agency.example",
        subject="Two candidates",
        inbox_status=InboxStatus.READY_FOR_REVIEW,
        evidence=[{"signal": "application_language"}],
        source_hints=[{"key": "sender_role", "value": "agency"}],
    )


def _service(
    inbox_repo: MagicMock,
    application_repo: MagicMock,
    proposal_repo: MagicMock,
) -> InboxService:
    return InboxService(
        session=AsyncMock(),
        inbox_repo=inbox_repo,
        job_application_repo=application_repo,
        link_proposal_repo=proposal_repo,
    )


class TestSourceSplitting:
    async def test_hr_splits_one_source_into_multiple_applications(self) -> None:
        item = _inbox_item()
        inbox_repo = MagicMock(spec=RecruitmentInboxItemRepository)
        inbox_repo.get_by_id = AsyncMock(return_value=item)
        inbox_repo.update = AsyncMock(side_effect=lambda value: value)
        application_repo = MagicMock(spec=JobApplicationRepository)
        application_repo.create = AsyncMock(side_effect=lambda value: value)
        proposal_repo = MagicMock(spec=JobApplicationLinkProposalRepository)
        service = _service(inbox_repo, application_repo, proposal_repo)

        applications = await service.split_item(
            item.id,
            applicants=[
                SplitApplicant(name="Nguyen A", email="a@example.com"),
                SplitApplicant(name="Tran B", email="b@example.com"),
            ],
            source=ApplicationSource.AGENCY,
            user_id=uuid4(),
        )

        assert len(applications) == 2
        assert {application.applicant_email for application in applications} == {
            "a@example.com",
            "b@example.com",
        }
        assert {application.source_email_message_id for application in applications} == {
            item.source_email_message_id
        }
        assert {application.gmail_message_id for application in applications} == {
            item.gmail_message_id
        }
        assert all(application.sender_email == item.sender_email for application in applications)
        assert all(application.source == ApplicationSource.AGENCY for application in applications)
        assert all(application.evidence == item.evidence for application in applications)
        assert item.inbox_status == InboxStatus.RESOLVED
        assert application_repo.create.await_count == 2

    async def test_same_sender_can_be_split_across_different_openings(self) -> None:
        item = _inbox_item()
        opening_a = uuid4()
        opening_b = uuid4()
        inbox_repo = MagicMock(spec=RecruitmentInboxItemRepository)
        inbox_repo.get_by_id = AsyncMock(return_value=item)
        inbox_repo.update = AsyncMock(side_effect=lambda value: value)
        application_repo = MagicMock(spec=JobApplicationRepository)
        application_repo.create = AsyncMock(side_effect=lambda value: value)
        service = _service(
            inbox_repo,
            application_repo,
            MagicMock(spec=JobApplicationLinkProposalRepository),
        )

        applications = await service.split_item(
            item.id,
            applicants=[
                SplitApplicant(name="Nguyen A", email="same@example.com", job_opening_id=opening_a),
                SplitApplicant(name="Nguyen A", email="same@example.com", job_opening_id=opening_b),
            ],
            source=ApplicationSource.DIRECT,
            user_id=uuid4(),
        )

        assert [application.job_opening_id for application in applications] == [
            opening_a,
            opening_b,
        ]
        assert applications[0].id != applications[1].id


class TestCrossThreadConfirmation:
    async def test_cross_thread_link_is_pending_until_hr_confirms(self) -> None:
        item = _inbox_item()
        target = JobApplication(
            source_email_message_id=uuid4(),
            gmail_message_id="msg_original",
            gmail_thread_id="thread_original",
            applicant_name="Nguyen A",
            applicant_email="a@example.com",
            message_references=[],
        )
        inbox_repo = MagicMock(spec=RecruitmentInboxItemRepository)
        inbox_repo.get_by_id = AsyncMock(return_value=item)
        inbox_repo.update = AsyncMock(side_effect=lambda value: value)
        application_repo = MagicMock(spec=JobApplicationRepository)
        application_repo.get_by_id = AsyncMock(return_value=target)
        application_repo.update = AsyncMock(side_effect=lambda value: value)
        proposal_repo = MagicMock(spec=JobApplicationLinkProposalRepository)
        proposal_repo.create = AsyncMock(side_effect=lambda value: value)
        proposal_repo.get_by_id = AsyncMock()
        proposal_repo.update = AsyncMock(side_effect=lambda value: value)
        service = _service(inbox_repo, application_repo, proposal_repo)
        hr_user_id = uuid4()

        proposal = await service.propose_cross_thread_link(
            item.id,
            target.id,
            user_id=hr_user_id,
        )

        assert proposal.status == LinkProposalStatus.PENDING
        assert proposal.target_job_application_id == target.id
        assert target.message_references == []
        application_repo.update.assert_not_awaited()

        proposal_repo.get_by_id.return_value = proposal
        confirmed = await service.resolve_link_proposal(
            proposal.id,
            decision=LinkProposalStatus.CONFIRMED,
            user_id=hr_user_id,
        )

        assert confirmed.status == LinkProposalStatus.CONFIRMED
        assert target.message_references == [
            {
                "email_message_id": str(item.source_email_message_id),
                "gmail_message_id": item.gmail_message_id,
                "gmail_thread_id": item.gmail_thread_id,
                "link_type": "hr_confirmed_cross_thread",
            }
        ]
        assert item.inbox_status == InboxStatus.RESOLVED
        application_repo.update.assert_awaited_once_with(target)

    async def test_hr_can_reject_cross_thread_proposal_without_linking(self) -> None:
        item = _inbox_item()
        target = JobApplication(
            source_email_message_id=uuid4(),
            gmail_message_id="msg_original",
            gmail_thread_id="thread_original",
        )
        proposal = JobApplicationLinkProposal(
            recruitment_inbox_item_id=item.id,
            target_job_application_id=target.id,
            status=LinkProposalStatus.PENDING,
        )
        inbox_repo = MagicMock(spec=RecruitmentInboxItemRepository)
        inbox_repo.get_by_id = AsyncMock(return_value=item)
        inbox_repo.update = AsyncMock(side_effect=lambda value: value)
        application_repo = MagicMock(spec=JobApplicationRepository)
        application_repo.get_by_id = AsyncMock(return_value=target)
        application_repo.update = AsyncMock()
        proposal_repo = MagicMock(spec=JobApplicationLinkProposalRepository)
        proposal_repo.get_by_id = AsyncMock(return_value=proposal)
        proposal_repo.update = AsyncMock(side_effect=lambda value: value)
        service = _service(inbox_repo, application_repo, proposal_repo)

        rejected = await service.resolve_link_proposal(
            proposal.id,
            decision=LinkProposalStatus.REJECTED,
            user_id=uuid4(),
        )

        assert rejected.status == LinkProposalStatus.REJECTED
        assert target.message_references == []
        assert item.inbox_status == InboxStatus.READY_FOR_REVIEW
        application_repo.update.assert_not_awaited()
