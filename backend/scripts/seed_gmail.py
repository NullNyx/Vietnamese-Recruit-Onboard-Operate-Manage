"""Seed a Gmail inbox with realistic Vietnamese HR emails for testing.

Inserts emails via Gmail API ``messages.insert`` so they appear as
regular incoming mail that the sync → classify → CV-parse pipeline picks up.

Usage::

    cd backend

    # Dry-run — preview what will be created
    python -m scripts.seed_gmail --dry-run

    # Insert the full seed set (one pass)
    python -m scripts.seed_gmail

    # Only recruitment CVs (with attachments)
    python -m scripts.seed_gmail --categories recruitment

    # Specific categories, multiple copies
    python -m scripts.seed_gmail --categories leave_request payroll --count 3

Requirements:
    - Gmail connected in the app (OrganizationGoogleConnection row exists)
    - OAuth scope ``https://www.googleapis.com/auth/gmail.modify`` granted
    - ``AUTH_OAUTH_TOKEN_ENCRYPTION_KEY`` set in ``.env``
    - ``reportlab`` installed (already in pyproject.toml)
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
import io
import logging
import os
import random
import sys
import textwrap
from datetime import UTC, datetime, timedelta
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any
from uuid import uuid4

import httpx
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.modules.identity.domain.entities import OrganizationGoogleConnection
from src.modules.identity.infrastructure.config import AuthSettings
from src.modules.identity.infrastructure.crypto_utils import CryptoUtils

logger = logging.getLogger(__name__)

GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me/"

# ═══════════════════════════════════════════════════════════════════════════
# Candidate profiles for CV generation (10+ diverse profiles)
# ═══════════════════════════════════════════════════════════════════════════

_CANDIDATE_PROFILES: list[dict[str, Any]] = [
    # 1 — Senior Software Engineer, chronological, English-heavy
    {
        "name": "Nguyễn Văn An",
        "email": "an.nguyen.dev@gmail.com",
        "phone": "0912345678",
        "objective": "Senior Software Engineer với 7+ năm kinh nghiệm phát triển backend, "
                     "mong muốn ứng tuyển vị trí Technical Lead tại công ty.",
        "skills": [
            "Python", "Go", "PostgreSQL", "Docker", "Kubernetes", "AWS",
            "Microservices", "CI/CD", "Redis", "Kafka", "System Design",
        ],
        "experience": [
            {
                "company": "FPT Software",
                "title": "Senior Software Engineer",
                "duration": "03/2020 – nay",
                "description": "Thiết kế và phát triển hệ thống microservices cho nền tảng thanh toán. "
                               "Dẫn dắt team 5 người, áp dụng Scrum. Giảm 40% latency qua tối ưu query PostgreSQL.",
            },
            {
                "company": "VNG Corporation",
                "title": "Software Engineer",
                "duration": "06/2017 – 02/2020",
                "description": "Phát triển backend cho ZaloPay sử dụng Java Spring Boot. "
                               "Xây dựng hệ thống xử lý 10K transaction/giây.",
            },
        ],
        "education": [
            {
                "institution": "Đại học Bách Khoa Hà Nội",
                "degree": "Kỹ sư",
                "field": "Công nghệ Thông tin",
                "year": "2017",
            },
        ],
        "certifications": ["AWS Solutions Architect Professional", "CKAD"],
        "languages": "Tiếng Anh (IELTS 7.5), Tiếng Việt (bản địa)",
        "salary_note": "Mức lương mong đợi: 45,000,000 VND",
    },
    # 2 — Marketing Manager, Vietnamese-heavy, with salary & CCCD
    {
        "name": "Trần Thị Bình",
        "email": "binh.tran.marketing@outlook.com",
        "phone": "0987-654-321",
        "objective": "Hơn 8 năm kinh nghiệm trong lĩnh vực Digital Marketing và Brand Management.",
        "skills": [
            "Digital Marketing", "SEO/SEM", "Content Strategy", "Google Analytics",
            "Facebook Ads", "TikTok Marketing", "Brand Management", "Team Leadership",
        ],
        "experience": [
            {
                "company": "Công ty Cổ phần Sữa Việt Nam (Vinamilk)",
                "title": "Brand Manager",
                "duration": "01/2019 – nay",
                "description": "Quản lý chiến lược thương hiệu cho dòng sản phẩm sữa organic. "
                               "Ngân sách marketing: 20 tỷ/năm. Tăng 35% thị phần trong 2 năm.",
            },
            {
                "company": "Công ty TNHH Truyền thông Goldsun",
                "title": "Digital Marketing Specialist",
                "duration": "07/2015 – 12/2018",
                "description": "Lập kế hoạch và triển khai chiến dịch quảng cáo đa kênh.",
            },
        ],
        "education": [
            {
                "institution": "Đại học Kinh tế TP. Hồ Chí Minh",
                "degree": "Cử nhân",
                "field": "Marketing",
                "year": "2015",
            },
        ],
        "certifications": ["Google Ads Certified", "Facebook Blueprint"],
        "languages": "Tiếng Anh (TOEIC 850), Tiếng Việt",
        "salary_note": "Mức lương hiện tại: 35,000,000 VND/tháng",
        "cccd": "001098765432",  # PII redaction test
    },
    # 3 — Fresh Graduate, education-heavy, minimal experience
    {
        "name": "Lê Hoàng Dũng",
        "email": "dunglh1912@gmail.com",
        "phone": "0321456987",
        "objective": "Sinh viên mới tốt nghiệp ngành Khoa học Dữ liệu mong muốn tìm kiếm "
                     "cơ hội thực tập hoặc Fresher tại công ty công nghệ.",
        "skills": [
            "Python", "SQL", "Pandas", "NumPy", "Machine Learning",
            "Data Visualization", "Jupyter", "Git", "Excel",
        ],
        "experience": [
            {
                "company": "Đại học Quốc gia Hà Nội",
                "title": "Research Assistant",
                "duration": "06/2024 – 12/2024",
                "description": "Hỗ trợ nghiên cứu về ứng dụng ML trong phân tích dữ liệu y tế. "
                               "Xây dựng pipeline xử lý dữ liệu với Python.",
            },
        ],
        "education": [
            {
                "institution": "Đại học Công nghệ - ĐHQGHN",
                "degree": "Cử nhân",
                "field": "Khoa học Dữ liệu",
                "year": "2024",
            },
        ],
        "certifications": ["Google Data Analytics Professional Certificate"],
        "languages": "Tiếng Anh (IELTS 6.5), Tiếng Việt",
        "gpa": "GPA: 3.4/4.0",
    },
    # 4 — Accountant, functional CV, with MST (tax code — PII test)
    {
        "name": "Phạm Minh Hà",
        "email": "hapham.accounting@gmail.com",
        "phone": "+84 90 123 45 67",
        "objective": "Kế toán trưởng với 10 năm kinh nghiệm trong lĩnh vực tài chính doanh nghiệp.",
        "skills": [
            "Kế toán tổng hợp", "Thuế TNCN", "Thuế TNDN", "Báo cáo tài chính",
            "MISA", "Fast Accounting", "IFRS", "VAS", "Excel nâng cao",
        ],
        "experience": [
            {
                "company": "Công ty TNHH Kiểm toán Ernst & Young Việt Nam",
                "title": "Senior Auditor",
                "duration": "06/2017 – nay",
                "description": "Phụ trách kiểm toán báo cáo tài chính cho các tập đoàn đa quốc gia.",
            },
            {
                "company": "Công ty TNHH Dịch vụ Kế toán ABC",
                "title": "Kế toán tổng hợp",
                "duration": "03/2013 – 05/2017",
                "description": "Quản lý sổ sách kế toán, kê khai thuế, lập BCTC cho 15+ doanh nghiệp.",
            },
        ],
        "education": [
            {
                "institution": "Học viện Tài chính",
                "degree": "Cử nhân",
                "field": "Kế toán - Kiểm toán",
                "year": "2013",
            },
        ],
        "certifications": ["CPA Việt Nam", "Chứng chỉ Kế toán trưởng"],
        "languages": "Tiếng Anh (TOEIC 780), Tiếng Việt",
        "salary_note": "Mong muốn: 25,000,000 - 30,000,000 VND",
        "mst": "1234567890123",  # PII: tax code
    },
    # 5 — Sales Representative, chronological, achievement-heavy
    {
        "name": "Hoàng Văn Khánh",
        "email": "khanh.sales@gmail.com",
        "phone": "0978123456",
        "objective": "Chuyên viên kinh doanh B2B với thành tích vượt KPI liên tục 3 năm.",
        "skills": [
            "B2B Sales", "CRM (Salesforce)", "Negotiation", "Account Management",
            "Market Research", "Presentation", "Contract Management",
        ],
        "experience": [
            {
                "company": "Tập đoàn Viettel",
                "title": "Senior B2B Sales Executive",
                "duration": "04/2020 – nay",
                "description": "Quản lý danh mục 50+ khách hàng doanh nghiệp lớn. "
                               "Doanh thu: 120 tỷ/năm. Vượt 130% KPI năm 2023.",
            },
            {
                "company": "Công ty Cổ phần Viễn thông FPT",
                "title": "Sales Representative",
                "duration": "08/2017 – 03/2020",
                "description": "Phát triển thị trường miền Bắc, đạt 105% KPI.",
            },
        ],
        "education": [
            {
                "institution": "Đại học Ngoại thương",
                "degree": "Cử nhân",
                "field": "Kinh doanh Quốc tế",
                "year": "2017",
            },
        ],
        "languages": "Tiếng Anh (IELTS 7.0), Tiếng Trung (HSK 4)",
    },
    # 6 — HR Specialist, combined format, with references
    {
        "name": "Nguyễn Thị Hồng",
        "email": "hongnguyen.hr@yahoo.com",
        "phone": "0904567890",
        "objective": "HRBP với 6 năm kinh nghiệm trong lĩnh vực nhân sự cho công ty công nghệ.",
        "skills": [
            "Tuyển dụng IT", "Employee Relations", "Performance Management",
            "HRIS", "Training & Development", "Labor Law", "Compensation & Benefits",
        ],
        "experience": [
            {
                "company": "Công ty Cổ phần VNG",
                "title": "HR Business Partner",
                "duration": "09/2020 – nay",
                "description": "Đối tác nhân sự cho khối Engineering (300+ nhân viên). "
                               "Triển khai OKR, xây dựng lộ trình thăng tiến.",
            },
            {
                "company": "Shopee Vietnam",
                "title": "Senior HR Specialist",
                "duration": "03/2018 – 08/2020",
                "description": "Phụ trách tuyển dụng khối Operations. Tuyển 200+ vị trí/năm.",
            },
        ],
        "education": [
            {
                "institution": "Đại học Lao động - Xã hội",
                "degree": "Cử nhân",
                "field": "Quản trị Nhân lực",
                "year": "2017",
            },
            {
                "institution": "Đại học Kinh tế Quốc dân",
                "degree": "Thạc sĩ",
                "field": "Quản trị Kinh doanh",
                "year": "2022",
            },
        ],
        "certifications": ["SHRM-CP", "LinkedIn Talent Assessment Certified"],
        "languages": "Tiếng Anh (IELTS 7.5), Tiếng Việt",
        "references_note": "Người tham chiếu: Ông Trần Văn Nam, HR Director, VNG — 090xxxxxxx",
    },
    # 7 — Data Analyst, skills-heavy, with projects section
    {
        "name": "Đỗ Quỳnh Nga",
        "email": "nga.do.data@gmail.com",
        "phone": "0387654321",
        "objective": "Data Analyst với khả năng chuyển đổi dữ liệu thô thành insight kinh doanh.",
        "skills": [
            "SQL", "Python", "Tableau", "Power BI", "Looker Studio",
            "A/B Testing", "Statistical Analysis", "ETL", "dbt",
        ],
        "experience": [
            {
                "company": "Tập đoàn Masan",
                "title": "Data Analyst",
                "duration": "05/2021 – nay",
                "description": "Xây dựng dashboard theo dõi KPI kinh doanh cho 10 thương hiệu. "
                               "Phân tích cohort, RFM để tối ưu retention.",
            },
        ],
        "education": [
            {
                "institution": "Đại học Bách Khoa TP. Hồ Chí Minh",
                "degree": "Kỹ sư",
                "field": "Hệ thống Thông tin",
                "year": "2021",
            },
        ],
        "projects": [
            "Customer Segmentation Model: Phân cụm 2M khách hàng bằng K-Means, "
            "giúp tăng 15% tỉ lệ chuyển đổi campaign.",
            "Sales Forecasting Dashboard: Dự báo doanh thu 6 tháng với độ chính xác 85%.",
        ],
        "languages": "Tiếng Anh (IELTS 7.0), Tiếng Việt",
    },
    # 8 — UX Designer, creative, with portfolio
    {
        "name": "Bùi Thanh Phong",
        "email": "phong.design@gmail.com",
        "phone": "0968123456",
        "objective": "Product Designer với thế mạnh về UX Research và Design System.",
        "skills": [
            "Figma", "Sketch", "Adobe XD", "Prototyping", "User Research",
            "Usability Testing", "Design Systems", "HTML/CSS cơ bản",
        ],
        "experience": [
            {
                "company": "Tiki Corporation",
                "title": "Product Designer",
                "duration": "02/2022 – nay",
                "description": "Thiết kế trải nghiệm người dùng cho ứng dụng Tiki (10M+ users). "
                               "Xây dựng Design System cho toàn bộ sản phẩm.",
            },
            {
                "company": "Công ty TNHH Thiết kế Sáng tạo Pixel",
                "title": "UI/UX Designer",
                "duration": "06/2019 – 01/2022",
                "description": "Thiết kế giao diện cho 20+ dự án web và mobile app.",
            },
        ],
        "education": [
            {
                "institution": "Đại học Kiến trúc TP. Hồ Chí Minh",
                "degree": "Cử nhân",
                "field": "Thiết kế Đồ họa",
                "year": "2019",
            },
        ],
        "languages": "Tiếng Anh (IELTS 6.5), Tiếng Việt",
        "portfolio_note": "Portfolio: behance.net/phongdesign",
    },
    # 9 — Operations Manager, executive CV with summary
    {
        "name": "Vũ Đức Mạnh",
        "email": "manh.vu.ops@gmail.com",
        "phone": "0915-678-901",
        "summary": "Giám đốc Vận hành với 12+ năm kinh nghiệm quản lý chuỗi cung ứng và logistics. "
                   "Đã dẫn dắt đội ngũ 200+ nhân viên, tối ưu chi phí vận hành 30%.",
        "skills": [
            "Supply Chain Management", "Logistics", "Warehouse Operations",
            "Process Optimization", "P&L Management", "Team Leadership",
            "Lean Six Sigma", "ERP Implementation",
        ],
        "experience": [
            {
                "company": "Công ty Cổ phần Giao hàng Nhanh",
                "title": "Operations Director",
                "duration": "06/2018 – nay",
                "description": "Quản lý toàn bộ hoạt động vận hành cho khu vực miền Nam. "
                               "Tối ưu chi phí logistics giảm 30%, cải thiện SLA từ 85% lên 97%.",
            },
            {
                "company": "Lazada Vietnam",
                "title": "Senior Operations Manager",
                "duration": "03/2013 – 05/2018",
                "description": "Quản lý 3 trung tâm phân phối, đội ngũ 150+ nhân viên.",
            },
        ],
        "education": [
            {
                "institution": "Đại học Quốc gia Singapore (NUS)",
                "degree": "MBA",
                "field": "Quản trị Kinh doanh",
                "year": "2013",
            },
            {
                "institution": "Đại học Ngoại thương",
                "degree": "Cử nhân",
                "field": "Kinh tế Đối ngoại",
                "year": "2009",
            },
        ],
        "certifications": ["Lean Six Sigma Black Belt", "PMP"],
        "languages": "Tiếng Anh (IELTS 8.0), Tiếng Trung (HSK 5), Tiếng Việt",
        "salary_note": "Mức lương hiện tại: 80,000,000 VND/tháng + thưởng",
    },
    # 10 — Intern/Fresher, very minimal
    {
        "name": "Ngô Hải Quỳnh",
        "email": "quynh.sea@gmail.com",
        "phone": "0355112233",
        "objective": "Sinh viên năm 3 ngành CNTT tìm kiếm vị trí thực tập sinh phần mềm.",
        "skills": ["Java", "Spring Boot", "MySQL", "Git", "REST API"],
        "experience": [],
        "education": [
            {
                "institution": "Đại học FPT",
                "degree": "Đang học",
                "field": "Kỹ thuật phần mềm",
                "year": "Dự kiến 2026",
            },
        ],
        "languages": "Tiếng Anh (IELTS 6.0), Tiếng Việt",
    },
    # 11 — Career changer, unrelated past
    {
        "name": "Đinh Xuân Sơn",
        "email": "son.dinh.tech@gmail.com",
        "phone": "0932-111-222",
        "objective": "Chuyển từ lĩnh vực Ngân hàng sang Công nghệ sau khi hoàn thành "
                     "khóa đào tạo lập trình full-stack.",
        "skills": [
            "JavaScript", "React", "Node.js", "MongoDB", "Express",
            "HTML/CSS", "TailwindCSS", "Git",
        ],
        "experience": [
            {
                "company": "Ngân hàng TMCP Ngoại thương Việt Nam (Vietcombank)",
                "title": "Chuyên viên Quan hệ Khách hàng",
                "duration": "06/2018 – 12/2023",
                "description": "Quản lý danh mục 100+ khách hàng doanh nghiệp vừa và nhỏ.",
            },
        ],
        "education": [
            {
                "institution": "Học viện Ngân hàng",
                "degree": "Cử nhân",
                "field": "Tài chính - Ngân hàng",
                "year": "2018",
            },
        ],
        "certifications": ["Full-Stack Web Development Bootcamp (Funix)"],
        "languages": "Tiếng Anh (TOEIC 750), Tiếng Việt",
    },
    # 12 — DevOps Engineer, skills + tools heavy
    {
        "name": "Lý Minh Tuấn",
        "email": "tuanly.devops@gmail.com",
        "phone": "0944556677",
        "objective": "DevOps Engineer chuyên về cloud infrastructure và tự động hóa.",
        "skills": [
            "AWS", "GCP", "Terraform", "Ansible", "Kubernetes", "Docker",
            "Jenkins", "GitLab CI", "Prometheus", "Grafana", "ELK Stack",
            "Python", "Bash", "Linux Administration",
        ],
        "experience": [
            {
                "company": "ShopBack Vietnam",
                "title": "Senior DevOps Engineer",
                "duration": "11/2021 – nay",
                "description": "Quản lý infrastructure trên AWS (EKS, RDS, ElastiCache). "
                               "Xây dựng CI/CD pipeline với GitLab CI và ArgoCD. "
                               "Giảm 60% chi phí cloud qua right-sizing và reserved instances.",
            },
            {
                "company": "Tiki Corporation",
                "title": "DevOps Engineer",
                "duration": "05/2019 – 10/2021",
                "description": "Vận hành Kubernetes cluster 50+ nodes. "
                               "Triển khai monitoring stack và hệ thống alerting.",
            },
        ],
        "education": [
            {
                "institution": "Đại học Bách Khoa Đà Nẵng",
                "degree": "Kỹ sư",
                "field": "Khoa học Máy tính",
                "year": "2019",
            },
        ],
        "certifications": ["AWS Certified DevOps Engineer", "CKA", "HashiCorp Terraform Associate"],
        "languages": "Tiếng Anh (IELTS 7.5), Tiếng Việt",
        "salary_note": "Mong đợi: 50,000,000 - 60,000,000 VND",
    },
]

# ═══════════════════════════════════════════════════════════════════════════
# PDF CV generator — reportlab
# ═══════════════════════════════════════════════════════════════════════════

# Vietnamese-safe style helpers
_BLACK = colors.HexColor("#1a1a1a")
_DARK_BLUE = colors.HexColor("#1a3a5c")
_LIGHT_GRAY = colors.HexColor("#f0f0f0")
_ACCENT = colors.HexColor("#2c5f8a")


def _cv_style() -> dict[str, ParagraphStyle]:
    """Shared CV styles with generous line-height for OCR readability."""
    base = getSampleStyleSheet()
    return {
        "name": ParagraphStyle("cv_name", fontSize=18, leading=22, textColor=_DARK_BLUE, spaceAfter=4),
        "section": ParagraphStyle("cv_section", fontSize=12, leading=16, textColor=_DARK_BLUE,
                                  spaceBefore=10, spaceAfter=4, borderPadding=(0, 0, 1, 0)),
        "body": ParagraphStyle("cv_body", fontSize=9, leading=13, textColor=_BLACK),
        "small": ParagraphStyle("cv_small", fontSize=8, leading=11, textColor=colors.HexColor("#555")),
    }


def _p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def _section_heading(text: str, styles: dict[str, ParagraphStyle]) -> Paragraph:
    return Paragraph(f"<b>{text}</b>", styles["section"])


def _generate_cv_pdf(profile: dict[str, Any]) -> bytes:
    """Generate a realistic A4 CV PDF for a candidate profile."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    styles = _cv_style()
    story: list[Any] = []

    # ── Header ──
    story.append(_p(profile["name"], styles["name"]))
    header_info = " | ".join(
        x for x in [profile.get("email"), profile.get("phone")] if x
    )
    story.append(_p(header_info, styles["small"]))
    if profile.get("portfolio_note"):
        story.append(_p(profile["portfolio_note"], styles["small"]))
    story.append(Spacer(1, 4*mm))

    # ── Objective or Summary ──
    objective = profile.get("objective") or profile.get("summary") or ""
    if objective:
        story.append(_section_heading(
            "MỤC TIÊU NGHỀ NGHIỆP" if profile.get("objective") else "TÓM TẮT CHUYÊN MÔN",
            styles))
        story.append(_p(objective, styles["body"]))
        story.append(Spacer(1, 2*mm))

    # ── Skills ──
    skills = profile.get("skills") or []
    if skills:
        story.append(_section_heading("KỸ NĂNG", styles))
        story.append(_p(" • " + "\n • ".join(skills), styles["body"]))
        story.append(Spacer(1, 2*mm))

    if profile.get("languages"):
        story.append(_p(f"<b>Ngôn ngữ:</b> {profile['languages']}", styles["small"]))

    if profile.get("certifications"):
        certs = profile["certifications"]
        if isinstance(certs, list):
            story.append(_p(f"<b>Chứng chỉ:</b> {', '.join(certs)}", styles["small"]))
        else:
            story.append(_p(f"<b>Chứng chỉ:</b> {certs}", styles["small"]))

    story.append(Spacer(1, 4*mm))

    # ── Experience ──
    experience = profile.get("experience") or []
    if experience:
        story.append(_section_heading("KINH NGHIỆM LÀM VIỆC", styles))
        for exp in experience:
            title_line = f"<b>{exp['title']}</b> — {exp['company']} <i>({exp['duration']})</i>"
            story.append(_p(title_line, styles["body"]))
            if exp.get("description"):
                story.append(_p(exp["description"], styles["body"]))
            story.append(Spacer(1, 1.5*mm))
        story.append(Spacer(1, 2*mm))

    # ── Education ──
    education = profile.get("education") or []
    if education:
        story.append(_section_heading("HỌC VẤN", styles))
        for edu in education:
            line = f"<b>{edu['institution']}</b> — {edu.get('degree','')} {edu.get('field','')} ({edu.get('year','')})"
            story.append(_p(line, styles["body"]))
        story.append(Spacer(1, 2*mm))

    # ── Projects (optional) ──
    if profile.get("projects"):
        story.append(_section_heading("DỰ ÁN", styles))
        for proj in profile["projects"]:
            story.append(_p(f"• {proj}", styles["body"]))
        story.append(Spacer(1, 2*mm))

    # ── Additional info (PII test) ──
    extras: list[str] = []
    if profile.get("salary_note"):
        extras.append(profile["salary_note"])
    if profile.get("gpa"):
        extras.append(profile["gpa"])
    if profile.get("cccd"):
        extras.append(f"CCCD: {profile['cccd']}")
    if profile.get("mst"):
        extras.append(f"MST: {profile['mst']}")
    if profile.get("references_note"):
        extras.append(profile["references_note"])
    if extras:
        story.append(_section_heading("THÔNG TIN BỔ SUNG", styles))
        story.append(_p("\n".join(extras), styles["small"]))

    doc.build(story)
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════════
# Realistic sender pools
# ═══════════════════════════════════════════════════════════════════════════

_CANDIDATE_NAMES_POOL = [
    "Nguyễn Văn Tâm", "Trần Thị Mai", "Lê Hoàng Phúc", "Phạm Quỳnh Anh",
    "Đặng Minh Triết", "Bùi Thanh Hà", "Ngô Đức Thắng", "Vũ Hải Yến",
    "Đỗ Thành Nam", "Hoàng Ngọc Diệp", "Dương Quốc Huy", "Lý Thu Hương",
]

_EMPLOYEE_NAMES = ["Trần Văn Hùng", "Lê Thị Hương", "Phạm Tuấn Kiệt", "Hoàng Minh Tuấn",
                   "Vũ Thị Thanh", "Nguyễn Thị Mai", "Đỗ Văn Bình"]

_VENDOR_CONTACTS = [
    ("Nguyễn Văn Nam", "namnv@hrsolutions.vn", "HR Solutions Vietnam"),
    ("Trần Thị Hoa", "hoa.tran@teambuildingplus.com", "Teambuilding Plus"),
    ("Lê Quang Bảo", "bao@recruitment-partners.vn", "Recruitment Partners Vietnam"),
]

_GOV_SENDERS = [
    ("Đoàn Thanh tra Sở LĐTBXH", "thanhtra@soldtbxh.gov.vn"),
    ("Bảo hiểm Xã hội Việt Nam", "cskh@vss.gov.vn"),
    ("Cục Thuế TP. Hà Nội", "thuehn@gdt.gov.vn"),
]

# ═══════════════════════════════════════════════════════════════════════════
# MIME builder
# ═══════════════════════════════════════════════════════════════════════════

def _build_mime(sender_name: str, sender_email: str, subject: str,
                body: str, *, recipient: str = "org@placeholder.invalid",
                attachments: list[tuple[str, str, bytes]] | None = None
                ) -> bytes:
    """Build multipart MIME message with optional attachments."""
    msg = MIMEMultipart()
    msg["From"] = f"{sender_name} <{sender_email}>"
    msg["To"] = recipient
    msg["Subject"] = subject
    msg["Date"] = datetime.now(UTC).strftime("%a, %d %b %Y %H:%M:%S +0000")
    msg["Message-ID"] = f"<{uuid4().hex}@seed.vroom.local>"
    msg.attach(MIMEText(body, "plain", "utf-8"))
    if attachments:
        for filename, mime_type, data in attachments:
            part = MIMEApplication(data, _subtype=mime_type.split("/")[-1])
            part.add_header("Content-Disposition", "attachment", filename=filename)
            msg.attach(part)
    return msg.as_bytes()


# ═══════════════════════════════════════════════════════════════════════════
# Category email generators (2-3 each, 10+ for recruitment)
# ═══════════════════════════════════════════════════════════════════════════

# ── Recruitment (12 CVs) ──

def _emails_recruitment() -> list[tuple[str, bytes]]:
    """12 realistic job application emails with diverse CV PDFs."""
    results: list[tuple[str, bytes]] = []
    for profile in _CANDIDATE_PROFILES:
        name = profile["name"]
        email_sender = profile["email"]
        exp_list = profile.get("experience") or []
        role = exp_list[0]["title"] if exp_list else "Nhân viên"
        subject = f"Ứng tuyển vị trí {role} — {name}"
        body = (
            f"Kính gửi Bộ phận Tuyển dụng,\n\n"
            f"Tôi là {name}, hiện đang tìm kiếm cơ hội mới trong lĩnh vực "
            f"{profile.get('skills', [''])[0] if profile.get('skills') else 'chuyên môn của tôi'}.\n\n"
            f"Tôi đã đính kèm CV để Quý công ty tham khảo. "
            f"Rất mong nhận được phản hồi.\n\n"
            f"Trân trọng,\n{name}\n"
            f"{email_sender}\n"
            f"{profile.get('phone', '')}"
        )
        cv_bytes = _generate_cv_pdf(profile)
        safe_name = name.replace(" ", "_")
        mime = _build_mime(
            name, email_sender, subject, body,
            attachments=[(f"CV_{safe_name}.pdf", "application/pdf", cv_bytes)],
        )
        results.append(("recruitment", mime))
    return results


# ── Interview (3 variants) ──

def _emails_interview() -> list[tuple[str, bytes]]:
    name = random.choice(_CANDIDATE_NAMES_POOL)
    email = name.lower().replace(" ", ".") + "@gmail.com"
    return [
        ("interview", _build_mime(name, email,
            "Xác nhận tham gia phỏng vấn ngày 25/07/2025",
            f"Chào anh/chị,\n\nTôi xác nhận sẽ tham gia buổi phỏng vấn "
            f"vào lúc 9h00 ngày 25/07/2025 tại văn phòng công ty.\n\n"
            f"Tôi sẽ có mặt trước 15 phút.\n\nTrân trọng,\n{name}")),
        ("interview", _build_mime(
            "HR Team", "hr@company.vn",
            "Phỏng vấn vòng 2 — Feedback từ Technical Lead",
            f"Chào em,\n\nSau vòng phỏng vấn kỹ thuật, team đánh giá cao "
            f"kỹ năng của em. Chúng ta sẽ sắp xếp vòng phỏng vấn với CTO "
            f"vào tuần sau. HR sẽ gửi calendar invite.\n\n"
            f"Thân ái,\nHR Team")),
        ("interview", _build_mime(
            "Nguyễn Thị Phương", "phuong.nguyen@recruitment-firm.vn",
            "Yêu cầu đổi lịch phỏng vấn — Ứng viên Nguyễn Văn Tâm",
            f"Chào chị,\n\nỨng viên Nguyễn Văn Tâm có việc đột xuất, "
            f"xin đổi lịch phỏng vấn từ 9h00 sang 14h00 cùng ngày 25/07.\n\n"
            f"Nhờ chị xác nhận giúp.\n\nCảm ơn chị,\nPhương")),
    ]


# ── Offer (2 variants) ──

def _emails_offer() -> list[tuple[str, bytes]]:
    name = random.choice(_CANDIDATE_NAMES_POOL)
    return [
        ("offer", _build_mime(name, name.lower().replace(" ", ".") + "@gmail.com",
            "Đồng ý Offer Letter — Ngày bắt đầu 01/08/2025",
            f"Kính gửi Anh/Chị Phụ trách,\n\nTôi đã nhận được offer letter và "
            f"đồng ý với các điều khoản. Tôi sẽ bắt đầu làm việc vào ngày 01/08/2025.\n\n"
            f"Xin cảm ơn cơ hội này.\n\nTrân trọng,\n{name}")),
        ("offer", _build_mime(name, name.lower().replace(" ", ".") + "@gmail.com",
            "Thương lượng lương — Offer vị trí Senior Developer",
            f"Kính gửi HR,\n\nCảm ơn quý công ty đã gửi offer. Tôi rất hào hứng với "
            f"cơ hội này. Tuy nhiên, tôi muốn thương lượng lại mức lương: "
            f"mong muốn 45,000,000 VND thay vì 40,000,000 VND như offer.\n\n"
            f"Rất mong nhận được phản hồi.\n\nTrân trọng,\n{name}")),
    ]


# ── Onboarding (2 variants) ──

def _emails_onboarding() -> list[tuple[str, bytes]]:
    return [
        ("onboarding", _build_mime("Nguyễn Thị Mai", "nguyenthimai@gmail.com",
            "Hỏi về thủ tục onboarding — Ngày đầu làm việc",
            f"Kính gửi Phòng HR,\n\nTôi là Nguyễn Thị Mai, nhân viên mới. "
            f"Tôi muốn hỏi về thủ tục nộp giấy tờ trong ngày đầu làm việc. "
            f"Tôi cần chuẩn bị những giấy tờ gì?\n\nXin cảm ơn.\n\nMai")),
        ("onboarding", _build_mime("Đỗ Văn Bình", "binhdv@outlook.com",
            "Gửi giấy tờ onboarding — Hồ sơ cá nhân",
            f"Kính gửi HR,\n\nTôi gửi kèm hồ sơ cá nhân theo yêu cầu onboarding: "
            f"CCCD, sổ BHXH, giấy khám sức khỏe (đính kèm file scan).\n\n"
            f"Vui lòng kiểm tra và xác nhận giúp tôi.\n\nTrân trọng,\nBình")),
    ]


# ── Leave Request (3 variants) ──

def _emails_leave_request() -> list[tuple[str, bytes]]:
    return [
        ("leave_request", _build_mime("Trần Văn Hùng", "hung.tran@company.vn",
            "Xin nghỉ phép 3 ngày — Lý do gia đình",
            f"Kính gửi Trưởng phòng,\n\nTôi viết email này để xin nghỉ phép 3 ngày "
            f"từ 20/07/2025 đến 22/07/2025 vì lý do gia đình.\n\n"
            f"Tôi đã bàn giao công việc cho anh Minh.\n\n"
            f"Xin chân thành cảm ơn.\n\nTrần Văn Hùng")),
        ("leave_request", _build_mime("Lê Thị Hương", "huongle@company.vn",
            "Xin nghỉ ốm hôm nay 19/07/2025",
            f"Chào anh/chị,\n\nHôm nay tôi bị sốt không thể đi làm được. "
            f"Tôi xin nghỉ ốm 1 ngày 19/07/2025.\n\n"
            f"Tôi sẽ gửi giấy khám bệnh sau.\n\nCảm ơn.\nHương")),
        ("leave_request", _build_mime("Phạm Tuấn Kiệt", "kietpt@company.vn",
            "Xin nghỉ thai sản — Dự sinh 15/08/2025",
            f"Kính gửi Phòng HR và Trưởng phòng,\n\nTôi viết email để thông báo "
            f"về việc xin nghỉ thai sản. Ngày dự sinh của vợ tôi là 15/08/2025. "
            f"Tôi dự kiến nghỉ 5 ngày từ 14/08 đến 20/08/2025.\n\n"
            f"Xin cảm ơn.\n\nPhạm Tuấn Kiệt")),
    ]


# ── Payroll (2 variants) ──

def _emails_payroll() -> list[tuple[str, bytes]]:
    return [
        ("payroll", _build_mime("Lê Thị Hương", "huongle@company.vn",
            "Thắc mắc về bảng lương tháng 6 — Thuế TNCN",
            f"Chào Phòng HR,\n\nTôi có thắc mắc về bảng lương tháng 6. "
            f"Khoản giảm trừ thuế TNCN của tôi hình như cao hơn bình thường. "
            f"Nhờ anh/chị kiểm tra lại giúp tôi.\n\nMã NV: EMP042\n\nCảm ơn.\nHương")),
        ("payroll", _build_mime("Trần Văn Hùng", "hung.tran@company.vn",
            "Hỏi về thưởng quý 2/2025",
            f"Chào HR,\n\nTôi muốn hỏi về chính sách thưởng quý 2. "
            f"Không biết công ty đã có thông báo chính thức chưa?\n\n"
            f"Cảm ơn anh/chị.\n\nHùng")),
    ]


# ── Employee Request (3 variants) ──

def _emails_employee_request() -> list[tuple[str, bytes]]:
    return [
        ("employee_request", _build_mime("Phạm Tuấn Kiệt", "kietpt@company.vn",
            "Xin giấy xác nhận công tác — Đi Singapore",
            f"Kính gửi Phòng HCNS,\n\nTôi cần xin giấy xác nhận công tác để làm "
            f"thủ tục visa đi Singapore cho chuyến công tác tháng 8.\n\n"
            f"Nhờ anh/chị hỗ trợ trong tuần này.\n\nCảm ơn.\nKiệt")),
        ("employee_request", _build_mime("Vũ Thị Thanh", "thanhvt@company.vn",
            "Đăng ký khóa đào tạo — Kỹ năng lãnh đạo",
            f"Chào HR,\n\nTôi muốn đăng ký tham gia khóa đào tạo "
            f"\"Kỹ năng Lãnh đạo\" tổ chức vào tháng 9/2025.\n\n"
            f"Nhờ anh/chị gửi thông tin chi tiết và form đăng ký.\n\nThanh")),
        ("employee_request", _build_mime("Hoàng Minh Tuấn", "tuanhm@company.vn",
            "Xin đổi thông tin cá nhân — Số tài khoản ngân hàng",
            f"Chào HR,\n\nTôi muốn cập nhật số tài khoản ngân hàng để nhận lương. "
            f"Số tài khoản mới: 1234567890123 — Ngân hàng Vietcombank, CN Hà Nội.\n\n"
            f"Nhờ anh/chị cập nhật giúp. (Đây là dữ liệu test — không phải thật)\n\n"
            f"Trân trọng,\nTuấn")),
    ]


# ── Resignation (2 variants) ──

def _emails_resignation() -> list[tuple[str, bytes]]:
    return [
        ("resignation", _build_mime("Hoàng Minh Tuấn", "tuanhm@company.vn",
            "Đơn xin nghỉ việc — Ngày cuối 15/08/2025",
            f"Kính gửi Trưởng phòng và Phòng HR,\n\n"
            f"Tôi viết email này để chính thức nộp đơn xin nghỉ việc. "
            f"Ngày làm việc cuối cùng của tôi là 15/08/2025.\n\n"
            f"Tôi sẽ hoàn thành bàn giao công việc đầy đủ. Xin cảm ơn công ty "
            f"đã tạo điều kiện làm việc trong 3 năm qua.\n\n"
            f"Trân trọng,\nHoàng Minh Tuấn")),
        ("resignation", _build_mime("Đỗ Văn Bình", "binhdv@outlook.com",
            "Thông báo nghỉ việc — Offboarding",
            f"Dear HR,\n\nTôi gửi thông báo chính thức về việc nghỉ việc. "
            f"Last working day: 31/08/2025.\n\n"
            f"Nhờ HR hướng dẫn quy trình offboarding và các thủ tục liên quan "
            f"(bảo hiểm, thuế, hoàn trả thiết bị).\n\nBest regards,\nBình")),
    ]


# ── Complaint (2 variants) ──

def _emails_complaint() -> list[tuple[str, bytes]]:
    return [
        ("complaint", _build_mime("Nhân viên ẩn danh", "anonymous.worker@gmail.com",
            "Phản ánh về vấn đề quấy rối nơi làm việc",
            f"Kính gửi Phòng HR,\n\nTôi muốn phản ánh về vấn đề quấy rối từ "
            f"đồng nghiệp trong nhóm dự án. Sự việc đã diễn ra nhiều lần "
            f"và ảnh hưởng nghiêm trọng đến hiệu suất làm việc của tôi.\n\n"
            f"Mong Quý phòng xem xét và giải quyết.\n\nTrân trọng.")),
        ("complaint", _build_mime("Trần Thị Mai", "mai.tran@company.vn",
            "Khiếu nại về quyết định kỷ luật không công bằng",
            f"Kính gửi Ban Giám đốc và Phòng HR,\n\nTôi viết email này để khiếu nại "
            f"về quyết định kỷ luật ngày 15/07/2025. Tôi cho rằng quyết định này "
            f"chưa dựa trên bằng chứng khách quan và đề nghị được xem xét lại.\n\n"
            f"Tôi sẵn sàng gặp trực tiếp để làm rõ.\n\nTrân trọng,\nTrần Thị Mai")),
    ]


# ── Vendor (3 variants) ──

def _emails_vendor() -> list[tuple[str, bytes]]:
    return [
        ("vendor", _build_mime("Nguyễn Văn Nam", "namnv@hrsolutions.vn",
            "Báo giá dịch vụ đào tạo doanh nghiệp 2025",
            f"Kính gửi Quý Công ty,\n\nHR Solutions Vietnam xin gửi báo giá "
            f"dịch vụ đào tạo:\n"
            f"1. Kỹ năng Lãnh đạo: 40,000,000 VND/khóa (3 ngày)\n"
            f"2. Kỹ năng Giao tiếp: 25,000,000 VND/khóa (2 ngày)\n"
            f"3. Team Building: 50,000,000 VND/ngày\n\n"
            f"Trân trọng,\nNguyễn Văn Nam\nSales Manager, HR Solutions Vietnam")),
        ("vendor", _build_mime("Trần Thị Hoa", "hoa.tran@teambuildingplus.com",
            "Chương trình Team Building 2025 — Ưu đãi đặc biệt",
            f"Chào HR,\n\nTeambuilding Plus xin giới thiệu chương trình Team Building "
            f"2025 với chủ đề \"Kết nối & Bứt phá\". Giá ưu đãi từ 2,000,000 "
            f"đồng/người cho đoàn trên 100 người.\n\n"
            f"Liên hệ: 090xxxxxxx\n\nTrân trọng,\nHoa")),
        ("vendor", _build_mime("Lê Quang Bảo", "bao@recruitment-partners.vn",
            "Dịch vụ headhunt — Gói Premium",
            f"Kính gửi HR Director,\n\nRecruitment Partners Vietnam cung cấp "
            f"dịch vụ headhunt chuyên biệt cho vị trí C-level và quản lý cấp cao. "
            f"Phí dịch vụ: 20% annual salary của ứng viên.\n\n"
            f"Hân hạnh được hợp tác.\nLê Quang Bảo")),
    ]


# ── Insurance (2 variants) ──

def _emails_insurance() -> list[tuple[str, bytes]]:
    return [
        ("insurance", _build_mime("Vũ Thị Thanh", "thanhvt@company.vn",
            "Hỏi về bảo hiểm sức khỏe — Khám chuyên khoa",
            f"Chào HR,\n\nTôi muốn hỏi về quyền lợi bảo hiểm sức khỏe. "
            f"Tôi cần khám chuyên khoa tại Vinmec, không biết bảo hiểm "
            f"có chi trả không và thủ tục như thế nào?\n\n"
            f"Nhờ anh/chị hướng dẫn.\n\nThanh")),
        ("insurance", _build_mime(employee_name := random.choice(_EMPLOYEE_NAMES),
            employee_name.lower().replace(" ", "") + "@company.vn",
            "Hỏi về chế độ BHXH — Nghỉ thai sản",
            f"Chào HR,\n\nTôi sắp đến kỳ nghỉ thai sản và muốn hỏi về chế độ BHXH. "
            f"Tôi cần chuẩn bị giấy tờ gì và mức hưởng như thế nào?\n\n"
            f"Cảm ơn chị.")),
    ]


# ── Internal (2 variants) ──

def _emails_internal() -> list[tuple[str, bytes]]:
    return [
        ("internal", _build_mime("Phòng Nhân sự", "hr@company.vn",
            "[Internal] All-hands Meeting Q3 — 28/07/2025",
            f"Chào tất cả mọi người,\n\nPhòng HR thông báo lịch họp All-hands quý 3:\n"
            f"- Thời gian: 14h00, Thứ Sáu, 28/07/2025\n"
            f"- Địa điểm: Phòng họp A, tầng 3\n\n"
            f"Đề nghị tất cả nhân viên tham gia đầy đủ.\n\nTrân trọng,\nPhòng Nhân sự")),
        ("internal", _build_mime("Ban Giám đốc", "bod@company.vn",
            "[Internal] Phê duyệt ngân sách Marketing Q3/2025",
            f"Kính gửi các Trưởng phòng,\n\nBan Giám đốc đã phê duyệt ngân sách "
            f"Marketing Q3/2025 như đề xuất. Chi tiết trong file đính kèm.\n\n"
            f"Đề nghị triển khai theo kế hoạch.\n\nTrân trọng,\nBan Giám đốc")),
    ]


# ── Compliance (2 variants) ──

def _emails_compliance() -> list[tuple[str, bytes]]:
    return [
        ("compliance", _build_mime("Đoàn Thanh tra Sở LĐTBXH", "thanhtra@soldtbxh.gov.vn",
            "Thông báo thanh tra định kỳ — 05/08/2025",
            f"Kính gửi Quý Công ty,\n\nĐoàn Thanh tra Sở LĐTBXH sẽ tiến hành "
            f"thanh tra định kỳ vào ngày 05/08/2025.\n\n"
            f"Đề nghị chuẩn bị: Hợp đồng lao động, Sổ BHXH, Bảng chấm công, "
            f"Quy chế trả lương.\n\nTrân trọng,\nĐoàn Thanh tra")),
        ("compliance", _build_mime("Cục Thuế TP. Hà Nội", "thuehn@gdt.gov.vn",
            "Yêu cầu báo cáo thuế TNCN — Quý 2/2025",
            f"Kính gửi Doanh nghiệp,\n\nCục Thuế TP. Hà Nội yêu cầu nộp báo cáo "
            f"thuế TNCN quý 2/2025 trước ngày 30/07/2025.\n\n"
            f"Mọi thắc mắc liên hệ: 024.xxxxxxx\n\nTrân trọng.")),
    ]


# ── Notification (2 variants) ──

def _emails_notification() -> list[tuple[str, bytes]]:
    return [
        ("notification", _build_mime("Vroom HR System", "noreply@vroom.vn",
            "[System] Sao lưu dữ liệu hoàn tất — 19/07/2025",
            f"Hệ thống Vroom HR thông báo:\n\n"
            f"Lịch sao lưu dữ liệu đã hoàn tất lúc 02:00 AM 19/07/2025.\n"
            f"Dung lượng: 1.2 GB. Trạng thái: Thành công.\n\n"
            f"Đây là email tự động, vui lòng không trả lời.")),
        ("notification", _build_mime("GitHub", "noreply@github.com",
            "[GitHub] Security alert — Dependabot found 2 vulnerabilities",
            f"Hi team,\n\nDependabot found 2 vulnerabilities in your repository:\n"
            f"- CVE-2025-xxxx (High) in package requests==2.28.1\n"
            f"- CVE-2025-yyyy (Medium) in package certifi==2023.5.7\n\n"
            f"View alerts: https://github.com/org/repo/security\n\nGitHub")),
    ]


# ── Uncategorized (2 variants) ──

def _emails_uncategorized() -> list[tuple[str, bytes]]:
    return [
        ("uncategorized", _build_mime("Nguyễn Quang Huy", "huybff@gmail.com",
            "Cuối tuần đi cafe nhé!",
            f"Hi em,\n\nCuối tuần này đi cafe không? Lâu quá không gặp. "
            f"Nhớ mang theo cuốn sách anh mượn nhé.\n\nHẹn gặp lại,\nHuy")),
        ("uncategorized", _build_mime("Mẹ", "me@gmail.com",
            "Nhớ ăn uống đầy đủ nhé con",
            f"Con ơi,\n\nDạo này con có khỏe không? Nhớ ăn uống đầy đủ, "
            f"đừng thức khuya quá. Cuối tuần về nhà mẹ nấu cháo gà cho ăn.\n\n"
            f"Thương con,\nMẹ")),
    ]


# ═══════════════════════════════════════════════════════════════════════════
# Master registry
# ═══════════════════════════════════════════════════════════════════════════

_ALL_GENERATORS: dict[str, callable] = {
    "recruitment": _emails_recruitment,
    "interview": _emails_interview,
    "offer": _emails_offer,
    "onboarding": _emails_onboarding,
    "leave_request": _emails_leave_request,
    "payroll": _emails_payroll,
    "employee_request": _emails_employee_request,
    "resignation": _emails_resignation,
    "complaint": _emails_complaint,
    "vendor": _emails_vendor,
    "insurance": _emails_insurance,
    "internal": _emails_internal,
    "compliance": _emails_compliance,
    "notification": _emails_notification,
    "uncategorized": _emails_uncategorized,
}


# ═══════════════════════════════════════════════════════════════════════════
# Gmail insert
# ═══════════════════════════════════════════════════════════════════════════

async def _send_email(http_client: httpx.AsyncClient, access_token: str,
                     mime_bytes: bytes) -> dict[str, str]:
    encoded = base64.urlsafe_b64encode(mime_bytes).decode("ascii")
    response = await http_client.post(
        f"{GMAIL_API_BASE}messages/send",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"raw": encoded},
    )
    response.raise_for_status()
    return response.json()  # type: ignore[no-any-return]


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

async def _get_access_token(settings: AuthSettings) -> str:
    """Read and decrypt the Gmail access token from the database."""
    engine = create_async_engine(settings.database_url, echo=False)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        result = await session.execute(
            select(OrganizationGoogleConnection).where(
                OrganizationGoogleConnection.organization_singleton_key == "default"
            )
        )
        conn = result.scalar_one_or_none()
        if conn is None or conn.status == "disconnected":
            await engine.dispose()
            raise RuntimeError("Gmail not connected. Connect in the app first.")
        if not conn.access_token_enc:
            await engine.dispose()
            raise RuntimeError("No access token found.")
        crypto = CryptoUtils(settings.oauth_token_encryption_key)
        try:
            token = crypto.decrypt(conn.access_token_enc)
        except Exception as exc:
            await engine.dispose()
            raise RuntimeError(f"Failed to decrypt token: {exc}") from exc
        email = conn.email or "unknown@gmail.com"
        print(f"✓ Gmail connected as: {email}")
    await engine.dispose()
    return token, email


async def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Gmail inbox with test HR emails")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print email list without inserting")
    parser.add_argument("--categories", type=str, nargs="*",
                        help="Specific categories (default: all)")
    parser.add_argument("--count", type=int, default=0,
                        help="Generate N extra random emails (0 = use built-in templates)")
    args = parser.parse_args()

    selected = set(args.categories) if args.categories else set(_ALL_GENERATORS)
    if not selected:
        print("No matching categories.", file=sys.stderr)
        sys.exit(1)

    # Build email list
    def build_emails(recipient: str) -> list[tuple[str, str, bytes]]:
        generators = {k: v for k, v in _ALL_GENERATORS.items() if k in selected}
        emails: list[tuple[str, str, bytes]] = []
        for cat, gen in generators.items():
            batch = gen()
            for _, mime in batch:
                emails.append((cat, cat, mime))
        if args.count > 0:
            for _ in range(args.count):
                cat = random.choice(list(generators))
                _, mime = random.choice(generators[cat]())
                emails.append((cat, cat, mime))
        # Dedup
        seen: set[str] = set()
        deduped: list[tuple[str, str, bytes]] = []
        for cat, label, mime in emails:
            h = hashlib.sha256(mime).hexdigest()
            if h not in seen:
                seen.add(h)
                deduped.append((cat, label, mime))
        return deduped

    if args.dry_run:
        all_emails = build_emails("recipient@example.com")
        for cat, label, _ in all_emails:
            print(f"[DRY-RUN] {cat:20s} | {label}")
        print(f"\nWould insert {len(all_emails)} emails.")
        return

    # Load settings and get access token + connected email
    settings = AuthSettings()  # type: ignore[call-arg]
    try:
        access_token, connected_email = await _get_access_token(settings)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    all_emails = build_emails(connected_email)

    async with httpx.AsyncClient(timeout=30.0) as http_client:
        success, failed = 0, 0
        for i, (cat, label, mime) in enumerate(all_emails, 1):
            try:
                result = await _send_email(http_client, access_token, mime)
                msg_id = result.get("id", "?")
                print(f"[{i:3d}/{len(all_emails)}] \u2713 {cat:20s} | {label:45s} | id={msg_id[:20]}...")
                success += 1
            except httpx.HTTPStatusError as exc:
                print(f"[{i:3d}/{len(all_emails)}] \u2717 {cat:20s} | {label:45s} | HTTP {exc.response.status_code}")
                if exc.response.status_code == 403:
                    print("  \u2192 Enable 'gmail.modify' scope in OAuth consent screen")
                failed += 1
            except Exception as exc:
                print(f"[{i:3d}/{len(all_emails)}] \u2717 {cat:20s} | {label:45s} | {exc}")
                failed += 1
            await asyncio.sleep(0.15)

    print(f"\nDone: {success} inserted, {failed} failed.")
    if success > 0:
        print("Next: trigger manual sync in the app or wait for poll cycle.")


if __name__ == "__main__":
    asyncio.run(main())
