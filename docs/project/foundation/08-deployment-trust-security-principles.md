# Deployment, Trust, and Security Principles

## Mục tiêu

Tài liệu này chốt các nguyên tắc để Vroom HR có thể self-host, đủ tin cậy cho company dùng thật, và đủ an toàn cho dữ liệu HR nhạy cảm.

---

## 1. Self-host là first-class

- Vroom HR phải chạy tốt trên môi trường tự host
- Docker Compose là path cơ bản
- Production có thể dùng PostgreSQL + Redis + MinIO
- Không thiết kế mặc định theo multi-tenant SaaS

---

## 2. One company per deployment

- Mỗi deployment phục vụ một company duy nhất
- Organization là singleton trong instance
- Không dùng tenant thinking của multi-company SaaS

---

## 3. Trust by control

Người dùng tin sản phẩm khi họ thấy:

- dữ liệu nằm ở đâu
- ai được truy cập
- ai có quyền thay đổi
- thay đổi nào đã xảy ra

Trust đến từ control và visibility, không phải từ lời quảng cáo.

---

## 4. Authentication boundary rõ

- Google OAuth2
- JWT trong httpOnly cookie
- Refresh token an toàn
- Employee access phải domain-gated
- HR / admin / employee permission tách rõ

---

## 5. Security by design

- OAuth tokens phải được mã hóa
- Audit log bắt buộc
- Domain gate cho employee login
- AI không có quyền write
- Error response không leak bí mật

---

## 6. Data ownership rõ

- Company sở hữu dữ liệu của chính mình
- Self-host cho phép giữ data trong hạ tầng đã kiểm soát
- Không đẩy dữ liệu nhạy cảm ra ngoài nếu không cần

---

## 7. Backup / restore phải là một phần của thiết kế

- deployment phải nghĩ tới backup từ đầu
- restore phải khả dụng và có thể hiểu được
- data loss không được xem là chi phí chấp nhận được

---

## 8. Environment settings phải rõ

- env config phải minh bạch
- secrets không hardcode
- defaults an toàn hơn defaults tiện
- docs phải nói rõ biến nào ảnh hưởng tới security

---

## 9. Deployment phải predictable

- chạy giống nhau giữa local và production càng nhiều càng tốt
- container / service boundaries rõ
- observability đủ để debug
- startup / shutdown an toàn

---

## 10. Least privilege

- HR chỉ thấy phần của HR
- Employee chỉ thấy data của mình
- Assistant chỉ đọc đúng boundary được cấp
- service account nào cũng chỉ có quyền cần thiết

---

## 11. No hidden automation

- không có automation tự ý write ngoài audit
- background jobs phải trace được
- AI / assistant không được trở thành backdoor

---

## 12. Compliance-ready thinking

Dù chưa làm full enterprise compliance, hệ thống phải đi theo hướng sẵn sàng cho:

- audit
- access logs
- retention policy
- data export / deletion policy khi cần

---

## Những điều cần tránh

- deploy phải sửa quá nhiều thủ công
- secrets nằm trong code
- permission mơ hồ
- self-host chỉ là lời hứa
- AI có thể can thiệp vượt quyền

---

## Một câu nhớ nhanh

**Deployment của Vroom HR phải giúp company tự tin giữ data, kiểm soát access, và trust hệ thống khi chạy thật.**

