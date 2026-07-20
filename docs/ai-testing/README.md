# AI Testing — Vroom HR

Tài liệu này liệt kê tất cả test case cho các tính năng AI trong Vroom HR, tổ chức theo nhóm để agent có thể đọc từng thư mục và thực hiện test độc lập.

## Cấu trúc

Mỗi thư mục chứa:
- `README.md`: tổng quan nhóm test, danh sách test case
- Các file `XX-ten-test-case.md`: mô tả chi tiết từng test case

## Cách dùng với Agent

```
# Test toàn bộ email classification
Đọc thư mục docs/ai-testing/01-email-classification/ và chạy test từng case

# Test riêng HR Assistant
Đọc thư mục docs/ai-testing/04-hr-assistant/ và chạy test từng case
```

## Danh sách nhóm

| # | Nhóm | Số test case | Mức ưu tiên |
|---|------|-------------|-------------|
| 01 | Email Classification | 7 | 🔴 Critical |
| 02 | Job Application Ingestion | 4 | 🔴 Critical |
| 03 | CV Parsing | 3 | 🟡 High |
| 04 | HR Assistant | 5 | 🟡 High |
| 05 | Employee Assistant | 4 | 🟡 High |
| 06 | Safety & Security | 4 | 🔴 Critical |
| 07 | Recovery & Resilience | 4 | 🔴 Critical |
| 08 | Rollout & Telemetry | 4 | 🟢 Medium |
| 09 | Quality & Feedback | 3 | 🟢 Medium |
| 10 | Organization AI Config | 4 | 🟢 Medium |

**Tổng: 42 test case**

## Module map

- **Gmail Classification**: `backend/src/modules/gmail/`
- **Recruitment AI**: `backend/src/modules/recruitment/`
- **HR Assistant**: `backend/src/modules/assistant/` + `frontend/app/(dashboard)/assistant/`
- **Employee Assistant**: `backend/src/modules/assistant/` + `frontend/app/(employee)/employee/assistant/`
- **Organization AI Config**: `backend/src/modules/identity/` (Organization service)
- **Test files**: `backend/tests/modules/`

## Quy ước file test case

Mỗi file test case theo format:

```markdown
# [Tên test case]

## Mục tiêu
...

## Mức độ ưu tiên
Critical / High / Medium

## Module liên quan
...

## Điều kiện tiên quyết
...

## Các bước thực hiện
1. ...
2. ...

## Kết quả mong đợi
...

## Code/File liên quan
...

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
```
