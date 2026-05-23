"""Unit tests for PayrollService."""

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from unittest.mock import MagicMock

from src.modules.payroll.application.payroll_service import PayrollService
from src.modules.payroll.domain.enums import PayrollStatus


class TestPayrollService:
    @pytest.fixture
    def mock_session(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_session):
        return PayrollService(mock_session)

    def test_confirm_period(self, service, mock_session):
        mock_period = MagicMock()
        mock_period.status = PayrollStatus.DRAFT
        mock_session.get.return_value = mock_period

        service.confirm_period(uuid4(), uuid4())

        assert mock_period.status == PayrollStatus.CONFIRMED

    def test_mark_period_paid_not_confirmed(self, service, mock_session):
        mock_period = MagicMock()
        mock_period.status = PayrollStatus.DRAFT
        mock_session.get.return_value = mock_period

        from src.modules.payroll.domain.exceptions import PeriodAlreadyPaidError

        with pytest.raises(PeriodAlreadyPaidError):
            service.mark_period_paid(uuid4())