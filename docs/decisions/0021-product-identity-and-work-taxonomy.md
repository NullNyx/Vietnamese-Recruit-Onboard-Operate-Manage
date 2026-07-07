# 0021 Product Identity + Work Taxonomy

Date: 2026-07-04

## Status

Accepted — Product Identity layer.

## Context

Phiên `grill-with-docs` làm rõ: product cần bắt đầu từ identity, không phải
data model hay module list. Hội thoại dần chuyển từ "HR Toolbox" sang **HR work
system** — HR sống bằng xử lý công việc song song mỗi ngày, không chạy pipeline
tuyến tính.

File ghi lại **Product Identity** + **3-tầng Work Taxonomy**: Action Types,
Work Types, AI Capabilities. Phase 1, Domain Model, Vertical Slices sẽ quyết
định sau.

## Decision

### 1. Product Identity

> HR Space là **HR operations work system** — nơi HR thực hiện công việc
> hằng ngày trong một giao diện duy nhất, giảm chuyển ngữ cảnh, giảm thao tác
> lặp, giảm lỗi thủ công, với AI hỗ trợ draft/extract/summarize/remind
> và human-in-loop trên mọi hành động ghi.

| Góc | Nội dung |
|-----|----------|
| Nhóm sản phẩm | Vertical HR operations software — giữa point solution rời rạc và HRM suite |
| Người dùng chính | HR generalist, HR ops, HR admin trong doanh nghiệp Việt Nam |
| Pain points | Việc rải nhiều tool; copy-paste; thiếu traceability; quên deadline; AI cần human-in-loop |
| Core value | Một nơi duy nhất làm việc HR — giảm chuyển ngữ cảnh, thao tác lặp, lỗi thủ công |
| Khác biệt | Nhẹ hơn HRM suite, đủ chuyên cho HR work, AI-first không auto mù, modular, self-host, audit |
| Không phải | HRM suite, ATS, ERP, recruitment pipeline, employee self-service platform |

### 2. Product Principles

Các đặc tính "AI-powered", "workflow-first", "modular", "HR-only" là
**product principles** — mô tả _how_, không phải _what_.

Tách rõ: **Product Identity** (bản chất), **Product Vision** (câu nén ngắn —
sau này), **Product Principles** (cách xây).

### 3. Work Taxonomy — 3 tầng

#### Tầng 1: Action Types

Thao tác xử lý việc. Độc lập domain — Intake là Intake cho cả Contract,
Onboarding, Request.

| Action | Mô tả |
|--------|-------|
| Intake | Nhận, phân loại, gắn ngữ cảnh |
| Review | Kiểm tra trước khi chốt |
| Draft | Tạo nội dung mới từ mẫu/template |
| Update | Sửa dữ liệu hiện tại |
| Coordinate | Chuyển việc, giao việc, xin xác nhận |
| Follow-up | Đẩy việc tới trạng thái xong |
| Monitor | Theo dõi deadline, pending, risk |
| Answer | Trả lời câu hỏi, tổng hợp số liệu |
| Complete | Chốt việc |

Mọi Work Type đều trải qua một subset của action set này.

#### Tầng 2: Work Types

Đơn vị việc HR nhìn thấy trên desk và theo dõi đến khi xong. Mỗi Work Type
có vòng đời rõ (trigger → end), khác biệt với Business Domain.

| # | Work Type | Ví dụ | Bắt đầu | Kết thúc | Action multi-step | Object chính |
|---|-----------|-------|---------|----------|-------------------|--------------|
| W1 | Hồ sơ nhân sự | cập nhật thông tin, thăng chức, nghỉ việc | HR hoặc request tạo | record cập nhật xong, sự kiện ghi | Intake → Update → Complete | Employee |
| W2 | Bộ giấy tờ | thu thập CCCD, bằng cấp, verify tài liệu | upload hoặc template sinh | all verified hoặc case đóng | Intake → Review → Follow-up → Complete | Employee, Onboarding |
| W3 | Chuẩn bị đi làm | onboarding checklist cho employee mới | candidate accepted / HR tạo | HR xác nhận complete | Draft → Coordinate → Review → Follow-up → Complete | Employee |
| W4 | Hợp đồng | tạo mới, gia hạn, chấm dứt, phụ lục | HR tạo / sắp hết hạn / accept | signed hoặc chấm dứt | Draft → Review → Coordinate → Follow-up → Complete | Employee |
| W5 | Tuyển dụng | xử lý CV, sàng lọc, phỏng vấn | email vào / HR tạo | accepted/rejected/archived | Intake → Review → Coordinate → Follow-up → Complete | Candidate |
| W6 | Yêu cầu nội bộ | manager yêu cầu tuyển, transfer, tăng lương | manager gửi | resolved/rejected/chuyển tiếp | Intake → Coordinate → Follow-up → Complete | Employee, none |
| W7 | Tác vụ đơn | nhắc ai đó, một task cụ thể | HR hoặc system sinh | completed/blocked | Monitor → Follow-up → Complete | Employee, any |
| W8 | Hỏi đáp / Báo cáo | ai sắp hết thử việc? tuần này onboard mấy người? | HR hoặc manager hỏi | trả lời xong | Answer | (read-only) |

Lưu ý W3 (Chuẩn bị đi làm) là **super work type** — nó chứa W2 + W4 + W7.
Một số work type gom nhiều work type khác.

#### Tầng 3: AI Capabilities

Hỗ trợ action types — không phải work type, không phải domain.

| AI Cap | Mô tả | Cặp action |
|--------|-------|------------|
| Classify | Phân loại đầu vào | Intake |
| Extract | Lấy thông tin từ file | Review, Complete |
| Summarize | Tóm tắt nội dung/hồ sơ | Review, Answer |
| Fill | Điền template | Draft |
| Suggest | Đề xuất giá trị, hành động | Draft, Review, Update |
| Remind | Nhắc việc, sinh reminder | Monitor, Follow-up |
| Answer | Trả lời tự nhiên từ dữ liệu sống | Answer |
| Rank | Xếp hạng ưu tiên | Monitor |

#### Work Type × Action × AI

| Work Type | Action chính | AI cap chính |
|-----------|-------------|--------------|
| Hồ sơ nhân sự | Intake → Update → Complete | Suggest, Summarize |
| Bộ giấy tờ | Intake → Review → Follow-up → Complete | Extract, Classify, Remind |
| Chuẩn bị đi làm | Draft → Coordinate → Review → Follow-up → Complete | Fill, Suggest, Summarize, Remind |
| Hợp đồng | Draft → Review → Coordinate → Follow-up → Complete | Fill, Summarize, Remind |
| Tuyển dụng | Intake → Review → Coordinate → Follow-up → Complete | Classify, Extract, Summarize, Fill |
| Yêu cầu nội bộ | Intake → Coordinate → Follow-up → Complete | Classify, Summarize |
| Tác vụ đơn | Monitor → Follow-up → Complete | Remind |
| Hỏi đáp / Báo cáo | Answer | Answer, Summarize |

#### Work Types ≠ Business Domains ≠ Modules

Work Type là shape việc HR theo dõi. Business Domain nhóm capability/dữ liệu.
Module là cách implement product.

Không map 1:1. Một work type chạm nhiều domain. Nhiều work type dùng chung
module. Work Type là đơn vị product design, không phải kiến trúc.

### 4. AI Position

AI không phải work type, không phải action. AI là capability xuyên suốt:
classify, extract, summarize, fill, suggest, remind, answer, rank.
Không có module "AI".

### 5. Phase 1 — Chưa chốt

Phase 1 sẽ được quyết định sau khi đánh giá: work type nào xuất hiện thường
xuyên nhất, tạo giá trị lớn nhất, khả thi MVP nhất. Không chốt ở file này.

### 6. Archetype — Giữ mở

HR Workbench / HR Toolbox là ứng viên. Identity hiện tại dẫn tới HR Operations
Work System — có thể đổi archetype sau. Chốt khi Identity + Scope rõ.

### 7. Tên sản phẩm

Tên sản phẩm là **HR Space**.

### 8. Documentation Flow

```
1. Product Identity + Work Taxonomy    ← file này
2. Product Vision (statement ngắn — sau Identity rõ)
3. Product Design: Home screen, IA, Navigation, Work/Detail Views
4. Capabilities → Modules Mapping
5. Domain Model (entity, relationship)
6. Vertical Slice PRDs
```

### 9. Next Phase — Product Design Inputs

Taxonomy đã chốt. Bước kế là **Product Design**, cần trả lời:

**Home screen:**
- Khi mở HR Space, HR nhìn thấy gì đầu tiên?
- Ưu tiên hôm nay / quá hạn / chờ mình / cần phối hợp / cảnh báo.

**Work Types xuất hiện thế nào:**
- Người dùng không cần biết "Work Type" là gì.
- Họ chỉ thấy: "5 việc cần xử lý hôm nay", "3 hợp đồng cần rà soát", v.v.

**Information Architecture cần thiết kế:**
- Navigation
- Dashboard
- Work Views (danh sách work items)
- Detail Views (chi tiết work item + action trail)

Sau IA ổn định mới map: Work Types → Capabilities → Modules → Domain Model → Data Model.

## Consequences

Positive:
- 3 tầng tách biệt: Action là thao tác, Work là đơn vị theo dõi, AI là capability.
- Work Type ≠ Domain ≠ Module — không lẫn product design với kiến trúc.
- Phase 1 chưa chốt — không bị ép bởi module list sớm.
- AI xuyên suốt — không module AI riêng.

Tradeoffs:
- Chưa thể implement — cần product design (home, IA, views) trước.
- W3 (Onboarding) là super work type — cần design hỗ trợ work type chứa work type.
- Taxonomy mới phá vỡ queue model cũ (9 queue) — không compatible với design-docs đã xoá.

## Supersedes

- ADR 0020 (xoá): Phase 1 chốt sai, employee-centric nặng.
- Queue taxonomy cũ (mục 3 của 0021 phiên trước): 9 queue thực chất là
  business domains — thay bằng 3 tầng Action/Work/AI.

## References

- Hội thoại grill-with-docs phiên 2: Work Taxonomy → 3 tầng → Product Design
- ADR-0015, 0018, 0019: giữ nguyên cho tới khi Domain Model quyết định
