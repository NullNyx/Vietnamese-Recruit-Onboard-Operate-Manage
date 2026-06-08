"""AI-based email classifier using LLM (Gemma 4) for the Gmail module.

Handles ambiguous emails that the rule-based classifier cannot confidently
categorize. Uses an OpenAI-compatible API endpoint with structured prompts
designed for Vietnamese HR email context.

Features:
- Retry with exponential backoff (1s, 2s, 4s) up to 3 attempts
- 15-second timeout per request
- Token usage tracking for cost monitoring
- Graceful fallback to uncategorized on failure
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI

from src.modules.gmail.domain.enums import EmailCategory
from src.modules.gmail.infrastructure.config import GmailSettings

logger = logging.getLogger(__name__)

_BACKOFF_DELAYS = [1, 2, 4]

# System prompt for email classification
_SYSTEM_PROMPT = """\
Bạn là hệ thống phân loại email cho phòng Nhân sự (HR) doanh nghiệp Việt Nam.

Phân loại email vào ĐÚNG MỘT category dưới đây:
- recruitment: CV ứng tuyển, giới thiệu ứng viên, headhunter, job board
- interview: Lịch phỏng vấn, xác nhận, feedback phỏng vấn
- offer: Offer letter, thương lượng lương, chấp nhận/từ chối offer
- onboarding: Nhân viên mới, tài liệu onboarding, ngày đầu làm việc
- leave_request: Xin nghỉ phép, nghỉ ốm, nghỉ thai sản, nghỉ không lương
- payroll: Hỏi lương, payslip, thuế TNCN, thưởng, phúc lợi, khấu trừ
- employee_request: Xin xác nhận, đổi thông tin, hỏi chính sách, đăng ký đào tạo
- resignation: Đơn nghỉ việc, offboarding, bàn giao, thông báo nghỉ việc
- complaint: Khiếu nại, phản ánh, conflict nội bộ, quấy rối
- vendor: Nhà cung cấp dịch vụ HR, training, event, teambuilding, báo giá
- insurance: BHXH, BHYT, bảo hiểm tư nhân, quyền lợi bảo hiểm
- internal: Thông báo nội bộ, phê duyệt, báo cáo quản lý, cuộc họp
- compliance: Thanh tra, kiểm toán, pháp lý lao động, quy định nhà nước
- notification: Thông báo hệ thống tự động, alerts, reminders
- uncategorized: Không xác định được loại email

Trả về ĐÚNG MỘT từ category (không giải thích, không dấu chấm, không ngoặc kép).\
"""


@dataclass
class ClassificationResult:
    """Result of AI email classification.

    Attributes:
        category: The assigned email category.
        confidence: Confidence score (0.0 - 1.0).
        source: Classification source ("rules" or "ai").
        matched_signals: Signals that contributed to classification.
        token_usage: Token usage from LLM call.
    """

    category: EmailCategory
    confidence: float
    source: str = "ai"
    matched_signals: list[str] = field(default_factory=list)
    token_usage: dict[str, int] = field(default_factory=dict)


class AIClassifier:
    """LLM-based email classifier using Gemma 4 via OpenAI-compatible API.

    Sends email metadata (subject, sender, snippet) to the LLM and parses
    the single-word category response. Implements retry with exponential
    backoff for transient failures.

    Args:
        settings: GmailSettings with LLM connection configuration.
    """

    def __init__(self, settings: GmailSettings) -> None:
        """Initialize the AI classifier with LLM client.

        Args:
            settings: Gmail module configuration with LLM settings.
        """
        self._settings = settings
        self._client = AsyncOpenAI(
            base_url=settings.classification_llm_base_url,
            api_key=settings.classification_llm_api_key or "not-needed",
            timeout=settings.classification_llm_timeout_seconds,
        )
        self._model = settings.classification_llm_model

    async def classify(
        self,
        subject: str,
        sender_email: str,
        sender_name: str,
        snippet: str,
        has_attachments: bool = False,
    ) -> ClassificationResult:
        """Classify an email using LLM.

        Constructs a prompt with email metadata and asks the LLM to
        classify into one of the valid HR email categories.

        Args:
            subject: Email subject line.
            sender_email: Sender's email address.
            sender_name: Sender's display name.
            snippet: First 200 characters of email body.
            has_attachments: Whether the email has attachments.

        Returns:
            ClassificationResult with the classified category.

        Raises:
            AIClassificationError: If all retry attempts are exhausted.
        """
        user_prompt = self._build_prompt(
            subject, sender_email, sender_name, snippet, has_attachments
        )
        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        logger.info(
            "AI classify input: subject=%r sender=%r snippet=%r",
            subject[:60],
            sender_email,
            snippet[:80],
        )

        last_error: Exception | None = None
        max_retries = self._settings.classification_llm_max_retries

        for attempt in range(max_retries):
            try:
                response = await asyncio.wait_for(
                    self._client.chat.completions.create(
                        model=self._model,
                        messages=messages,  # type: ignore[arg-type]
                        temperature=0.0,
                        max_tokens=1000,
                    ),
                    timeout=self._settings.classification_llm_timeout_seconds,
                )

                # Handle reasoning models (e.g., MiMo) where the answer
                # may be in content or reasoning_content
                message = response.choices[0].message
                raw_content = (message.content or "").strip().lower()

                # If content is empty, try to extract category from reasoning_content
                if not raw_content:
                    reasoning = getattr(message, "reasoning_content", None) or ""
                    logger.info(
                        "AI content empty, extracting from reasoning (%d chars): %s",
                        len(reasoning),
                        reasoning[:200] if reasoning else "(empty)",
                    )
                    raw_content = self._extract_category_from_reasoning(reasoning)

                token_usage = self._extract_token_usage(response)

                logger.info(
                    "AI classification result: raw=%r, tokens=%s",
                    raw_content[:50] if raw_content else "(empty)",
                    token_usage,
                )

                category = self._parse_category(raw_content)
                confidence = 0.85 if category != EmailCategory.uncategorized else 0.3

                return ClassificationResult(
                    category=category,
                    confidence=confidence,
                    source="ai",
                    matched_signals=[f"llm_response:{raw_content}"],
                    token_usage=token_usage,
                )

            except TimeoutError as exc:
                last_error = exc
                logger.warning(
                    "AI classification timeout on attempt %d/%d",
                    attempt + 1,
                    max_retries,
                )
            except (APITimeoutError, APIConnectionError, APIStatusError) as exc:
                last_error = exc
                logger.warning(
                    "AI classification error on attempt %d/%d: %s",
                    attempt + 1,
                    max_retries,
                    str(exc),
                )

            # Exponential backoff before retry
            if attempt < max_retries - 1:
                delay = _BACKOFF_DELAYS[min(attempt, len(_BACKOFF_DELAYS) - 1)]
                await asyncio.sleep(delay)

        raise AIClassificationError(
            f"AI classification failed after {max_retries} attempts: {last_error}"
        )

    def _extract_category_from_reasoning(self, reasoning: str) -> str:
        """Extract a category keyword from reasoning_content.

        Reasoning models like MiMo may put the final answer inside their
        reasoning chain rather than in the content field. This method
        searches the reasoning text for any valid category keyword.

        Args:
            reasoning: The reasoning_content string from the model.

        Returns:
            The extracted category string (lowercase), or empty string if not found.
        """
        reasoning_lower = reasoning.lower()

        # Look for category keywords in the reasoning, prioritize exact matches
        for category in EmailCategory:
            # Look for patterns like "category: recruitment" or "→ recruitment"
            # or the category appearing as a standalone word near the end
            if category.value in reasoning_lower:
                return category.value

        return ""

    def _build_prompt(
        self,
        subject: str,
        sender_email: str,
        sender_name: str,
        snippet: str,
        has_attachments: bool,
    ) -> str:
        """Build the classification prompt with email metadata.

        Args:
            subject: Email subject line.
            sender_email: Sender's email address.
            sender_name: Sender's display name.
            snippet: Email body preview.
            has_attachments: Whether email has attachments.

        Returns:
            Formatted prompt string.
        """
        attachment_info = "Có" if has_attachments else "Không"
        sender_display = f"{sender_name} <{sender_email}>" if sender_name else sender_email

        return (
            f"Phân loại email sau:\n\n"
            f"Từ: {sender_display}\n"
            f"Tiêu đề: {subject}\n"
            f"Nội dung: {snippet}\n"
            f"Đính kèm: {attachment_info}\n\n"
            f"Category:"
        )

    def _parse_category(self, raw_response: str) -> EmailCategory:
        """Parse the LLM response into an EmailCategory enum value.

        Handles common LLM response artifacts (quotes, periods, extra text).
        Defaults to uncategorized if response cannot be parsed.

        Args:
            raw_response: Raw lowercase response from the LLM.

        Returns:
            The parsed EmailCategory value.
        """
        # Clean up common LLM artifacts
        cleaned = raw_response.strip().strip('"').strip("'").strip(".").lower()

        # Remove any text after the first word/underscore-word
        # e.g., "recruitment - this is a CV" → "recruitment"
        cleaned = cleaned.split(" ")[0].split("\n")[0]

        try:
            return EmailCategory(cleaned)
        except ValueError:
            pass

        # Try matching as substring
        for category in EmailCategory:
            if category.value in cleaned:
                return category

        logger.warning(
            "AI returned unparseable category, defaulting to uncategorized: %r",
            raw_response,
        )
        return EmailCategory.uncategorized

    @staticmethod
    def _extract_token_usage(response: Any) -> dict[str, int]:
        """Extract token usage from the API response.

        Args:
            response: The chat completion response object.

        Returns:
            Dictionary with prompt_tokens, completion_tokens, total_tokens.
        """
        usage = getattr(response, "usage", None)
        if usage is None:
            return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        return {
            "prompt_tokens": getattr(usage, "prompt_tokens", 0) or 0,
            "completion_tokens": getattr(usage, "completion_tokens", 0) or 0,
            "total_tokens": getattr(usage, "total_tokens", 0) or 0,
        }


class AIClassificationError(Exception):
    """Raised when AI classification fails after all retries."""

    pass
