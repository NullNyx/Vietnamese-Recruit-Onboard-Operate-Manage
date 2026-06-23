# Gap Analysis — Hệ thống hiện tại vs Foundation

## Mục tiêu

Tài liệu này so sánh Vroom HR hiện tại (code + architecture) với tầm nhìn foundation đã định nghĩa. Mỗi gap là một hướng cần điều chỉnh.

---

## Cách đọc

| Ký hiệu | Ý nghĩa |
|---------|---------|
| ✅ | Đã có |
| ⚠️ | Có nhưng chưa đúng |
| ❌ | Chưa có |
| ➖ | Không áp dụng |

---

## 1. Product Statement

| Yêu cầu | Trạng thái | Ghi chú |
|---------|------------|---------|
| Backbone (recruit → onboard → employee) | ⚠️ | Backbone có nhưng onboarding chưa kết nối end-to-end |
| Câu chuyện sản phẩm rõ | ❌ | Chưa có product narrative cho người dùng |
| HR / Employee / Owner phân biệt | ⚠️ | ESS và HR admin đã tách nhưng UX chưa khác biệt rõ |
| Open-source stance | ✅ | AGPL, repo public |

**Gap chính**: thiếu product narrative. Code có backbone logic, nhưng chưa kể thành câu chuyện người dùng.

---

## 2. Target User Personas

| Yêu cầu | Trạng thái | Ghi chú |
|---------|------------|---------|
| HR queue / review | ✅ | Employee request, candidate review có |
| Employee self-service | ⚠️ | ESS có nhưng còn mỏng so với tầm nhìn |
| Organization self-host | ✅ | Docker Compose có |
| Employee permission boundary | ✅ | ESS đã tách khỏi admin |
| UX khác nhau cho HR và Employee | ❌ | Cả hai đang dùng cùng design system |

**Gap chính**: HR và Employee UX chưa có identity riêng.

---

## 3. User Journey

| Yêu cầu | Trạng thái | Ghi chú |
|---------|------------|---------|
| Email → AI classify | ✅ | Có trong recruitment |
| CV parse → Candidate | ✅ | Có |
| HR review pipeline | ✅ | Có |
| Interview scheduling | ✅ | Có synchronous + Google Calendar |
| Accept → Onboarding | ❌ | Có event nhưng chưa có consumer rõ |
| Onboarding → Employee active | ⚠️ | Module có nhưng chưa hoàn thiện |
| Employee → ESS | ⚠️ | ESS có nhưng còn hạn chế |
| Status / Next action / Trust visible | ❌ | Chưa có UX pattern thống nhất |

**Gap chính**: onboarding consumer missing, UX chưa phản ánh journey.

---

## 4. Core Requirements

| Yêu cầu | Trạng thái | Ghi chú |
|---------|------------|---------|
| Backbone flow | ⚠️ | Thiếu landing cho accepted→onboarding |
| Auth + authorization | ✅ | Google OAuth, cookie JWT, domain gate |
| Employee management | ✅ | CRUD departments, positions, employees |
| Audit | ✅ | Có audit_log table |
| AI Assistant | ✅ | Tool-calling, read + draft |
| Attendance | ✅ | Check-in/out, leave, overtime, holiday |
| Payroll | ✅ | Salary config, payslip, tax, insurance |
| ESS | ⚠️ | Payslip view, request, assistant |
| Self-host | ✅ | Docker Compose |
| Out of scope (policy engine) | ✅ | Đã remove |

**Gap chính**: core module có đủ nhưng backbone connection còn thiếu.

---

## 5. System Architecture

| Yêu cầu | Trạng thái | Ghi chú |
|---------|------------|---------|
| Domain-first | ✅ | SQLModel entities, domain exceptions |
| Module boundaries | ✅ | Mỗi module có api / application / domain / infrastructure |
| Async-first | ✅ | AsyncSession, async services |
| Atomic state transitions | ✅ | Interview scheduling atomic |
| Cross-module events | ⚠️ | Có event (accepted) nhưng onboarding consumer chưa active |
| Audit by design | ✅ | Audit log trong mọi module |
| Security boundary | ✅ | Cookie JWT, domain gate, role check |
| Self-host architecture | ✅ | Docker, env config |

**Gap chính**: event consumer cho onboarding cần hoàn thiện.

---

## 6. AI Boundary

| Yêu cầu | Trạng thái | Ghi chú |
|---------|------------|---------|
| Read-Tool | ✅ | Có |
| Draft-Tool | ✅ | Có |
| Không write tool cho LLM | ✅ | Đúng |
| Human-in-the-loop | ✅ | Draft → confirm |
| Employee assistant | ✅ | Có employee_assistant_router |
| AI không phá audit | ✅ | Cấu trúc an toàn |

**Gap chính**: AI boundary đã làm đúng. Không cần sửa.

---

## 7. UX Design

| Yêu cầu | Trạng thái | Ghi chú |
|---------|------------|---------|
| Status first | ❌ | UI chưa tập trung vào trạng thái |
| Next action first | ❌ | Chưa có queue / next action pattern |
| Queue over clutter | ⚠️ | Có review queue nhưng chưa ưu tiên pending items |
| Context-rich detail | ⚠️ | Candidate detail có nhưng chưa phải context kể chuyện |
| HR UX ≠ Employee UX | ❌ | Cùng design system, chưa có identity khác nhau |
| Trust visible | ❌ | Audit chưa visible trong UI |
| Vietnamese-first | ❌ | UI đang tiếng Anh, chưa có tiếng Việt |

**Gap chính**: UX là gap lớn nhất. Chưa có design identity, chưa có Vietnamese, chưa có status/next action pattern.

---

## 8. Deployment / Trust / Security

| Yêu cầu | Trạng thái | Ghi chú |
|---------|------------|---------|
| Self-host first-class | ✅ | Docker Compose, env config |
| One company per deployment | ✅ | Single org |
| Trust by control | ⚠️ | Có audit nhưng chưa visible cho user |
| Auth boundary | ✅ | Google OAuth, cookie, domain gate |
| Security by design | ✅ | Encrypt tokens, audit, no AI write |
| Backup / restore | ❌ | Chưa có docs hoặc script |

**Gap chính**: backup/restore chưa có, trust chưa visible trong UI.

---

## 9. Data Model

| Yêu cầu | Trạng thái | Ghi chú |
|---------|------------|---------|
| Candidate lifecycle | ✅ | new → reviewing → interview_scheduled → accepted/rejected/archived |
| Onboarding process | ⚠️ | Module có, nhưng connection từ candidate accept chưa hoàn |
| Employee lifecycle | ⚠️ | is_active flag, nhưng onboarding trigger chưa active |
| Audit log | ✅ | Có |
| State transitions atomic | ✅ | Interview scheduling có |

**Gap chính**: onboarding data connection.

---

## 10. Open-Source Strategy

| Yêu cầu | Trạng thái | Ghi chú |
|---------|------------|---------|
| AGPL license | ✅ | Có |
| Public repo | ✅ | GitHub |
| Community contribution | ⚠️ | Có thể contribute nhưng chưa có contribution guide rõ |
| Docs public | ✅ | Có docs/ |
| Commercial layer | ❌ | Chưa có |

**Gap chính**: commercial layer chưa có, contribution guide cần rõ hơn.

---

## Tổng quan gap priority

| Gap | Mức độ | Module | Action |
|-----|--------|--------|--------|
| UX: status/next action/trust visible | 🔴 Cao | UI (frontend) | Redesign UX theo tenets |
| UX: Vietnamese-first | 🔴 Cao | UI (frontend) | Localize UI |
| UX: HR ≠ Employee khác nhau | 🔴 Cao | UI (frontend) | Tách identity UI |
| Onboarding consumer | 🔴 Cao | onboarding | Kết nối accepted event → tạo process |
| Product narrative cho người dùng | 🟡 Trung | Docs / Marketing | Viết landing / intro |
| Backup/restore | 🟡 Trung | Infrastructure | Viết script + docs |
| Contribution guide | 🟢 Thấp | Docs | Viết CONTRIBUTING.md |
| Event consumer cho các module khác | 🟢 Thấp | Backend | Củng cố event system |

---

## Kết luận

Hệ thống hiện tại có nền kỹ thuật khá tốt: module separation, AI boundary, audit, auth, async.

Gap lớn nhất không phải ở backend, mà ở:
1. **UX**: chưa có status/next action/trust visible, chưa tiếng Việt, chưa tách HR/Employee
2. **Product narrative**: chưa kể được câu chuyện sản phẩm
3. **Onboarding connection**: backbone còn đứt đoạn
4. **Open-source readiness**: thiếu contribution guide, backup

Foundation đã viết xong. Gap analysis này là kim chỉ nam cho ưu tiên thay đổi.
