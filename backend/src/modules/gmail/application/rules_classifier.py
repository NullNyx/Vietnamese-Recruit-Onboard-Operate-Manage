"""Rule-based email classifier for the Gmail module.

Provides fast, free classification for emails with obvious patterns
(known sender domains, keyword matches in subject/snippet, attachment
indicators). Handles ~60% of HR emails without needing LLM calls.

Designed for HR context with bilingual keyword support.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from src.modules.gmail.domain.enums import EmailCategory
from src.modules.gmail.infrastructure.ai_classifier import ClassificationResult

logger = logging.getLogger(__name__)


@dataclass
class ClassificationRule:
    """A single classification rule with weighted signals.

    Attributes:
        category: The email category this rule maps to.
        sender_domains: Domains that strongly indicate this category.
        sender_patterns: Regex patterns for sender email matching.
        subject_keywords: Keywords in subject that indicate this category.
        snippet_keywords: Keywords in snippet/body preview.
        has_attachments: If True, presence of attachments boosts confidence.
        base_confidence: Base confidence when any signal matches.
    """

    category: EmailCategory
    sender_domains: list[str] = field(default_factory=list)
    sender_patterns: list[str] = field(default_factory=list)
    subject_keywords: list[str] = field(default_factory=list)
    snippet_keywords: list[str] = field(default_factory=list)
    has_attachments: bool | None = None
    base_confidence: float = 0.7


# --- HR Classification Rules ────────────────────────────────

CLASSIFICATION_RULES: list[ClassificationRule] = [
    # === TUYỂN DỤNG ===
    ClassificationRule(
        category=EmailCategory.recruitment,
        sender_domains=[
            "vietnamworks.com",
            "topcv.vn",
            "careerbuilder.vn",
            "linkedin.com",
            "indeed.com",
            "glints.com",
            "jobstreet.com",
            "timviecnhanh.com",
            "vieclam24h.vn",
        ],
        subject_keywords=[
            "ứng tuyển",
            "apply",
            "cv",
            "resume",
            "hồ sơ ứng tuyển",
            "nộp đơn",
            "job application",
            "vị trí",
            "position",
            "giới thiệu ứng viên",
            "candidate",
            "ứng viên",
            "tuyển dụng",
            "headhunter",
            "referral",
        ],
        snippet_keywords=[
            "kinh nghiệm",
            "kỹ năng",
            "trình độ",
            "bằng cấp",
            "mong muốn ứng tuyển",
            "xin gửi cv",
            "attached my resume",
            "cover letter",
        ],
        has_attachments=True,
        base_confidence=0.75,
    ),
    # === PHỎNG VẤN ===
    ClassificationRule(
        category=EmailCategory.interview,
        subject_keywords=[
            "phỏng vấn",
            "interview",
            "lịch pv",
            "xác nhận phỏng vấn",
            "interview schedule",
            "interview invitation",
            "mời phỏng vấn",
            "lịch hẹn",
            "buổi phỏng vấn",
        ],
        snippet_keywords=[
            "phỏng vấn vào",
            "interview on",
            "please confirm",
            "xác nhận tham dự",
            "vòng phỏng vấn",
        ],
        base_confidence=0.85,
    ),
    # === OFFER ===
    ClassificationRule(
        category=EmailCategory.offer,
        subject_keywords=[
            "offer letter",
            "thư mời làm việc",
            "job offer",
            "thỏa thuận lương",
            "salary negotiation",
            "đề xuất lương",
            "compensation",
            "offer",
        ],
        snippet_keywords=[
            "mức lương",
            "chế độ đãi ngộ",
            "ngày bắt đầu",
            "start date",
            "chấp nhận offer",
            "accept the offer",
            "từ chối offer",
        ],
        base_confidence=0.80,
    ),
    # === ONBOARDING ===
    ClassificationRule(
        category=EmailCategory.onboarding,
        subject_keywords=[
            "onboarding",
            "nhân viên mới",
            "new hire",
            "ngày đầu",
            "first day",
            "welcome",
            "chào mừng",
            "tài liệu nhập việc",
            "orientation",
            "hội nhập",
        ],
        snippet_keywords=[
            "ngày đầu tiên",
            "chuẩn bị",
            "tài liệu cần mang",
            "welcome pack",
            "buddy",
            "mentor",
        ],
        base_confidence=0.80,
    ),
    # === NGHỈ VIỆC (checked before leave_request to avoid overlap) ===
    ClassificationRule(
        category=EmailCategory.resignation,
        subject_keywords=[
            "nghỉ việc",
            "resign",
            "resignation",
            "thôi việc",
            "chấm dứt hợp đồng",
            "termination",
            "đơn xin thôi việc",
            "notice period",
            "thời gian báo trước",
            "last working day",
            "đơn xin nghỉ việc",
        ],
        snippet_keywords=[
            "xin nghỉ việc",
            "ngày làm việc cuối",
            "bàn giao công việc",
            "handover",
            "lý do nghỉ việc",
        ],
        base_confidence=0.92,
    ),
    # === NGHỈ PHÉP ===
    ClassificationRule(
        category=EmailCategory.leave_request,
        subject_keywords=[
            "nghỉ phép",
            "xin nghỉ phép",
            "leave request",
            "nghỉ ốm",
            "sick leave",
            "nghỉ thai sản",
            "maternity",
            "annual leave",
            "đơn xin nghỉ phép",
            "personal leave",
            "nghỉ việc riêng",
            "nghỉ không lương",
            "unpaid leave",
        ],
        snippet_keywords=[
            "xin phép nghỉ",
            "từ ngày",
            "đến ngày",
            "lý do nghỉ",
            "số ngày nghỉ",
            "leave balance",
        ],
        base_confidence=0.90,
    ),
    # === LƯƠNG / PAYROLL ===
    ClassificationRule(
        category=EmailCategory.payroll,
        subject_keywords=[
            "lương",
            "salary",
            "payslip",
            "phiếu lương",
            "thuế tncn",
            "thưởng",
            "bonus",
            "payroll",
            "bảng lương",
            "tăng lương",
            "truy lĩnh",
            "khấu trừ",
            "deduction",
        ],
        snippet_keywords=[
            "lương tháng",
            "chuyển khoản",
            "tài khoản ngân hàng",
            "net salary",
            "gross",
            "thuế thu nhập",
        ],
        base_confidence=0.85,
    ),
    # === YÊU CẦU NHÂN VIÊN ===
    ClassificationRule(
        category=EmailCategory.employee_request,
        subject_keywords=[
            "xin xác nhận",
            "confirmation letter",
            "giấy xác nhận",
            "đổi thông tin",
            "update information",
            "chính sách",
            "policy",
            "hỏi về",
            "inquiry",
            "đăng ký",
            "registration",
            "training",
            "đào tạo",
        ],
        snippet_keywords=[
            "xin được",
            "nhờ phòng hr",
            "xin hỏi",
            "cho tôi hỏi",
            "cần xác nhận",
            "giấy tờ",
        ],
        base_confidence=0.70,
    ),
    # === KHIẾU NẠI ===
    ClassificationRule(
        category=EmailCategory.complaint,
        subject_keywords=[
            "khiếu nại",
            "complaint",
            "phản ánh",
            "report",
            "tố cáo",
            "grievance",
            "conflict",
            "xung đột",
            "quấy rối",
            "harassment",
        ],
        snippet_keywords=[
            "không hài lòng",
            "vấn đề",
            "issue",
            "vi phạm",
            "violation",
            "unfair",
            "không công bằng",
        ],
        base_confidence=0.80,
    ),
    # === NHÀ CUNG CẤP / VENDOR ===
    ClassificationRule(
        category=EmailCategory.vendor,
        subject_keywords=[
            "báo giá",
            "quotation",
            "proposal",
            "đề xuất hợp tác",
            "partnership",
            "dịch vụ",
            "service",
            "hợp đồng",
            "contract",
            "teambuilding",
            "event",
            "sự kiện",
        ],
        snippet_keywords=[
            "kính gửi",
            "chào giá",
            "giải pháp",
            "solution",
            "demo",
            "trial",
            "package",
            "gói dịch vụ",
        ],
        base_confidence=0.70,
    ),
    # === BẢO HIỂM ===
    ClassificationRule(
        category=EmailCategory.insurance,
        sender_domains=[
            "baoviet.com.vn",
            "pvi.com.vn",
            "bhxh.gov.vn",
            "prudential.com.vn",
            "manulife.com.vn",
            "aia.com.vn",
            "dai-ichi-life.com.vn",
            "fwd.com.vn",
        ],
        subject_keywords=[
            "bảo hiểm",
            "bhxh",
            "bhyt",
            "bhtn",
            "insurance",
            "social insurance",
            "quyết toán bảo hiểm",
            "sổ bảo hiểm",
            "thẻ bhyt",
        ],
        snippet_keywords=[
            "đóng bảo hiểm",
            "mức đóng",
            "quyền lợi bảo hiểm",
            "claim",
            "bồi thường",
        ],
        base_confidence=0.85,
    ),
    # === NỘI BỘ ===
    ClassificationRule(
        category=EmailCategory.internal,
        subject_keywords=[
            "thông báo",
            "announcement",
            "nội bộ",
            "internal",
            "phê duyệt",
            "approval",
            "báo cáo",
            "report",
            "meeting",
            "họp",
            "cuộc họp",
            "bổ nhiệm",
            "điều chuyển",
            "transfer",
        ],
        snippet_keywords=[
            "kính gửi toàn thể",
            "thông báo đến",
            "all staff",
            "toàn công ty",
            "ban giám đốc",
        ],
        base_confidence=0.65,
    ),
    # === COMPLIANCE ===
    ClassificationRule(
        category=EmailCategory.compliance,
        sender_domains=[
            "molisa.gov.vn",
            "gdt.gov.vn",
            "customs.gov.vn",
        ],
        subject_keywords=[
            "thanh tra",
            "inspection",
            "kiểm toán",
            "audit",
            "compliance",
            "quy định",
            "regulation",
            "báo cáo lao động",
            "labor report",
            "thuế",
            "tax",
        ],
        snippet_keywords=[
            "theo quy định",
            "luật lao động",
            "labor law",
            "nghị định",
            "decree",
            "thông tư",
            "circular",
        ],
        base_confidence=0.80,
    ),
    # === THÔNG BÁO HỆ THỐNG ===
    ClassificationRule(
        category=EmailCategory.notification,
        sender_patterns=[
            r"^(no-?reply|noreply|notifications?|mailer-daemon|system)@",
            r"@(notifications\.|alerts\.|noreply\.)",
        ],
        subject_keywords=[
            "notification",
            "alert",
            "automated",
            "system",
            "reminder",
            "nhắc nhở",
        ],
        base_confidence=0.85,
    ),
]


class RulesClassifier:
    """Rule-based email classifier using keyword and domain matching.

    Evaluates emails against a set of classification rules, scoring
    each rule based on the number and type of matching signals.
    Returns the highest-scoring category with a confidence score.

    Signal weights:
    - Sender domain match: +0.3
    - Sender pattern match: +0.25
    - Subject keyword match: +0.2 per keyword (max 0.4)
    - Snippet keyword match: +0.1 per keyword (max 0.2)
    - Attachment indicator: +0.1
    """

    def __init__(self, rules: list[ClassificationRule] | None = None) -> None:
        """Initialize with classification rules.

        Args:
            rules: Custom rules list. Defaults to CLASSIFICATION_RULES.
        """
        self._rules = rules or CLASSIFICATION_RULES

    def classify(
        self,
        subject: str,
        sender_email: str,
        snippet: str,
        has_attachments: bool = False,
    ) -> ClassificationResult:
        """Classify an email using rule-based matching.

        Evaluates all rules and returns the best match. If no rule
        matches with sufficient confidence, returns uncategorized.

        Args:
            subject: Email subject line.
            sender_email: Sender's email address.
            snippet: First 200 characters of email body.
            has_attachments: Whether the email has attachments.

        Returns:
            ClassificationResult with the best matching category.
        """
        best_result = ClassificationResult(
            category=EmailCategory.uncategorized,
            confidence=0.0,
            source="rules",
        )

        subject_lower = subject.lower()
        sender_lower = sender_email.lower()
        snippet_lower = snippet.lower()

        for rule in self._rules:
            score, signals = self._evaluate_rule(
                rule, subject_lower, sender_lower, snippet_lower, has_attachments
            )

            if score > best_result.confidence:
                # Apply base confidence scaling
                final_confidence = min(score * rule.base_confidence / 0.5, 1.0)
                best_result = ClassificationResult(
                    category=rule.category,
                    confidence=final_confidence,
                    source="rules",
                    matched_signals=signals,
                )

        return best_result

    def _evaluate_rule(
        self,
        rule: ClassificationRule,
        subject_lower: str,
        sender_lower: str,
        snippet_lower: str,
        has_attachments: bool,
    ) -> tuple[float, list[str]]:
        """Evaluate a single rule against email data.

        Args:
            rule: The classification rule to evaluate.
            subject_lower: Lowercased subject.
            sender_lower: Lowercased sender email.
            snippet_lower: Lowercased snippet.
            has_attachments: Whether email has attachments.

        Returns:
            Tuple of (score, list of matched signal descriptions).
        """
        score = 0.0
        signals: list[str] = []

        # Check sender domain
        sender_domain = sender_lower.split("@")[-1] if "@" in sender_lower else ""
        for domain in rule.sender_domains:
            if domain in sender_domain:
                score += 0.3
                signals.append(f"sender_domain:{domain}")
                break

        # Check sender patterns (regex)
        for pattern in rule.sender_patterns:
            try:
                if re.search(pattern, sender_lower):
                    score += 0.25
                    signals.append(f"sender_pattern:{pattern}")
                    break
            except re.error:
                continue

        # Check subject keywords (max 2 matches counted)
        subject_matches = 0
        for keyword in rule.subject_keywords:
            if keyword in subject_lower:
                subject_matches += 1
                signals.append(f"subject:{keyword}")
                if subject_matches >= 2:
                    break
        score += min(subject_matches * 0.2, 0.4)

        # Check snippet keywords (max 2 matches counted)
        snippet_matches = 0
        for keyword in rule.snippet_keywords:
            if keyword in snippet_lower:
                snippet_matches += 1
                signals.append(f"snippet:{keyword}")
                if snippet_matches >= 2:
                    break
        score += min(snippet_matches * 0.1, 0.2)

        # Check attachment indicator
        if rule.has_attachments is True and has_attachments:
            score += 0.1
            signals.append("has_attachments")

        return score, signals
