# Target User Personas

## Giới thiệu

Tài liệu này mô tả 3 nhóm người dùng chính của Vroom HR. Mỗi nhóm có motivation riêng, pain riêng, cách nhìn hệ thống riêng. Tất cả quyết định về UX, feature, permission, và deployment đều phải quay về đây.

---

## 1. HR / Admin (Người vận hành)

### Định danh

- Người trực tiếp dùng Vroom HR hàng ngày
- Chịu trách nhiệm tuyển dụng, onboarding, quản lý hồ sơ, phê duyệt
- Không nhất thiết rành kỹ thuật, nhưng rành quy trình HR

### Mục tiêu

- Tuyển đúng người nhanh
- Onboarding không bị sót bước
- Mỗi action đều có audit
- Dễ review, dễ approve, ít thao tác lặp
- Biết chính xác trạng thái pipeline đang ở đâu

### Pain

- Dữ liệu rải rác: email inbox, Excel, chat, giấy
- Scheduling interview lộn xộn
- Không biết candidate nào đang chờ mình
- Không nhìn thấy onboarding đang tắc ở đâu
- Sợ sai quy trình, thiếu audit khi cần đối soát

### Cần từ hệ thống

- Một nơi duy nhất để xem toàn bộ candidate lifecycle
- Queue rõ ràng: ai cần xử lý, ai đang chờ, ai sắp tới hạn
- Interview scheduling gắn với calendar thật
- Onboarding checklist có trạng thái, có người chịu trách nhiệm
- Audit log đầy đủ, không thể tắt
- AI giúp tóm tắt CV, draft email, nhưng không tự quyết định

### Họ không muốn

- Hệ thống phức tạp hơn vấn đề của họ
- Click nhiều lần chỉ để xem trạng thái
- Phải nhập lại dữ liệu đã có
- AI làm sai rồi họ phải đi sửa

---

## 2. Employee / ESS (Người được quản lý)

### Định danh

- Là nhân viên đang active trong công ty
- Dùng Vroom HR để xem thông tin cá nhân, tự phục vụ các nhu cầu cơ bản
- Không có quyền HR, không cần nhìn thấy phần HR

### Mục tiêu

- Xem thông tin cá nhân, hợp đồng, payslip
- Gửi request nghỉ phép / overtime
- Biết tiến trình onboarding của bản thân (nếu đang trong giai đoạn này)
- Biết mình cần làm gì tiếp theo

### Pain

- Không biết tình trạng hồ sơ của mình
- Phải hỏi HR cho mọi thứ
- Giao diện quá phức tạp giống admin
- Sợ làm sai, sợ ảnh hưởng quyền lợi

### Cần từ hệ thống

- Dashboard đơn giản: cá nhân tôi đang ở đâu
- Xem nhanh: thông tin, lương, phép, payslip
- Gửi request: giao diện rõ, biết được xử lý tới đâu
- Chỉ thấy dữ liệu của mình, không thấy dữ liệu người khác
- Đọc trước, ghi sau: ưu tiên xem hơn là thao tác

### Họ không muốn

- Nhìn thấy phần admin
- Phải hiểu quy trình nội bộ của HR
- Bắt buộc tương tác quá nhiều

---

## 3. Organization / Owner (Người quyết định)

### Định danh

- Là người quyết định triển khai Vroom HR
- Có thể là founder, CTO, COO, hoặc HR head
- Quan tâm đến bức tranh lớn, không phải từng feature

### Mục tiêu

- Dữ liệu nhân sự an toàn, không bị phụ thuộc vendor
- Hệ thống dễ triển khai, dễ vận hành
- Có audit đủ để đối soát khi cần
- Có thể mở rộng khi công ty lớn hơn
- Chi phí hợp lý, không bị lock-in

### Pain

- Mua phần mềm HR đắt, bị phụ thuộc vendor
- Nhân viên IT phải lo nhiều thứ, không muốn thêm gánh nặng
- Sợ data nhạy cảm bị lộ
- Sợ sản phẩm không theo kịp luật pháp Việt Nam
- Sợ mua giải pháp nước ngoài không phù hợp văn hóa / luật

### Cần từ hệ thống

- Self-host được
- Docker / Kubernetes deploy
- Có audit trail đầy đủ
- Mã nguồn mở để kiểm tra, tùy chỉnh
- AI có boundary rõ, không tự ý ghi
- SSO / access control tốt
- Backup / restore rõ

### Họ không muốn

- Vendor lock-in
- Phí ẩn, phí theo đầu người tăng không kiểm soát
- Hệ thống không deploy được trong môi trường họ kiểm soát
- Data nhạy cảm gửi lên cloud không rõ ràng

---

## Tổng quan mối quan hệ giữa các nhóm

```
Organization / Owner
    │
    ▼
HR / Admin ──────────► Employee
( vận hành )        ( tự phục vụ )
    │
    ▼
   Audit / control luôn hiện diện
   AI chỉ hỗ trợ, không quyết định
   Open-source đảm bảo trust cho Owner
```

## Nguyên tắc khi thiết kế cho từng nhóm

| Khía cạnh      | HR                               | Employee                 | Owner                       |
| -------------- | -------------------------------- | ------------------------ | --------------------------- |
| Ngôn ngữ       | Tiếng Việt + thuật ngữ nghiệp vụ | Tiếng Việt đơn giản      | Tiếng Anh / Việt + kỹ thuật |
| Mức ưu tiên    | Queue + next action              | Read + self-service      | Deploy + control            |
| Permission     | Full HR scope                    | Chỉ dữ liệu cá nhân      | Admin / super admin         |
| AI interaction | Tool-calling assistant           | Employee assistant       | Không cần AI                |
| UX density     | Cao (nhiều dữ liệu cùng lúc)     | Thấp (đơn giản, rõ ràng) | Dashboard tổng quan         |
