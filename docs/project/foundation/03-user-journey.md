# User Journey

## Mục tiêu

Tài liệu này mô tả hành trình người dùng cốt lõi của Vroom HR. Không đi theo màn hình, mà đi theo trạng thái và hành động thật của người dùng.

---

## Journey 1 — HR path (inbox → candidate → employee)

### Bước 1: Email vào hệ thống

- HR (hoặc mail integration) nhận email ứng tuyển
- AI classify email: cv / partner / event / internal / other
- Nếu là CV, hệ thống lưu lại và đẩy vào pipeline

### Bước 2: CV parsing

- OCR + LLM trích xuất thông tin
- Tạo Candidate mới với confidence score
- HR thấy candidate trong review queue

### Bước 3: HR review

- HR mở Candidate detail
- Xem CV summary, pipeline state, notes
- Đánh dấu reviewing / shortlist / reject / schedule interview

### Bước 4: Interview scheduling

- HR chọn thời gian interview
- Google Calendar event được tạo ngay trong request
- Meet link sinh ra
- Nếu thất bại, trạng thái không đổi

### Bước 5: Accept

- HR accept candidate
- hệ thống gửi congratulations email
- accepted event được phát ra cho onboarding

### Bước 6: Onboarding

- Onboarding process được tạo
- HR xử lý checklist task: contract, documents, department, position, start date
- Khi tất cả task done, Candidate chuyển sang Employee active

### Điểm chính của HR journey

- HR không đi tìm thông tin ở nhiều nơi
- Hệ thống phải cho thấy rõ ai đang chờ mình làm gì
- Mỗi bước đều có trạng thái và audit

---

## Journey 2 — Employee path (access → self-service → active)

### Bước 1: Login bằng domain hợp lệ

- Employee đăng nhập bằng Google OAuth
- Domain phải nằm trong allowlist của Organization
- Nếu hợp lệ, user vào ESS

### Bước 2: Nhìn trạng thái cá nhân

- Xem profile, payslip, attendance / leave / request status
- Nếu đang onboarding, thấy tasks cần làm
- Nếu active, thấy self-service dashboard

### Bước 3: Thực hiện request

- Gửi leave request / overtime request khi cần
- Theo dõi trạng thái phê duyệt
- Chỉ thao tác trong phạm vi dữ liệu của mình

### Điểm chính của Employee journey

- Employee không cần hiểu structure nội bộ của HR
- Chỉ cần biết: tôi đang ở đâu, cần làm gì, request của tôi tới đâu

---

## Journey 3 — Organization / Owner path (deploy → trust → control)

### Bước 1: Deploy

- Cài bằng Docker / self-host
- Chọn domain, auth, storage, db, redis

### Bước 2: Trust setup

- Kiểm tra audit
- Chọn allowed domain
- Bảo đảm access control và security settings

### Bước 3: Control

- Theo dõi dữ liệu, backup, restore, compliance
- Biết hệ thống có thể mở rộng hay không

### Điểm chính của Owner journey

- Không phải dùng sản phẩm mỗi ngày
- Nhưng phải đủ tin để cho HR / Employee dùng thật

---

## Backbone journey map

```text
Incoming email
  → AI classify
  → CV parse
  → Candidate created
  → HR review
  → Interview scheduled
  → Candidate accepted
  → Onboarding created
  → Tasks completed
  → Employee active
  → ESS usage
```

## Design principles từ journey

1. **Status first**: luôn biết đang ở bước nào
2. **Next action first**: luôn biết cần làm gì tiếp theo
3. **Boundary first**: ai được thấy gì, ai được sửa gì
4. **Audit first**: thay đổi quan trọng phải trace được
5. **Single narrative**: journey phải kể cùng một câu chuyện từ đầu tới cuối

## Cái gì không nên xảy ra trong journey

- HR phải hỏi lại hệ thống nhiều lần chỉ để biết trạng thái
- Employee thấy màn hình admin
- AI tự ý viết vào DB
- interview scheduling fail nhưng trạng thái vẫn update
- onboarding xong mà Employee chưa active

