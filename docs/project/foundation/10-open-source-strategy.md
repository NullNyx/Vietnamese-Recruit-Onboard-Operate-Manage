# Open-Source Strategy

## Mục tiêu

Tài liệu này chốt chiến lược open-source của Vroom HR: tại sao mở mã nguồn, mở ở đâu, và điều gì sẽ không mở hoặc cần lớp thương mại phía sau.

---

## 1. Open-source là trust + adoption, không phải đích cuối

Open-source cho phép:

- company tự kiểm tra mã nguồn → trust
- company tự deploy → control
- cộng đồng đóng góp → growth
- khách hàng không bị vendor lock-in → safety

Nhưng:

- open-source KHÔNG đồng nghĩa với free cho mọi thứ
- open-source KHÔNG đồng nghĩa không có đường kiếm tiền
- open-source KHÔNG đồng nghĩa không có trách nhiệm bảo trì

---

## 2. License: AGPL v3

Giấy phép:
- AGPL v3 cho mã nguồn gốc
- Ai cũng có thể fork, đọc, sửa
- Nếu sửa và chạy dịch vụ, phải mở lại mã nguồn sửa

Lý do:
- giữ cho community xây trên cùng một backbone
- tránh closed-source fork cạnh tranh không lành mạnh
- phù hợp với sản phẩm self-host

---

## 3. Core open-source vs commercial layer

### Core mở (trong open-source repo)

- Backbone (recruitment / onboarding / employee)
- Identity / auth
- Audit
- Attendance
- Payroll
- ESS
- AI Assistant basic (read + draft)
- Gmail integration

### Commercial layer (không mở, trả phí)

Những thứ này sẽ nằm ở layer riêng (không code tại thời điểm này, nhưng cần biết để thiết kế):

- Hosted cloud (managed)
- SSO / SAML / LDAP enterprise
- Advanced compliance reporting
- Priority support
- SLA
- Enterprise dashboard / analytics nâng cao
- Advanced migration tools

Tách biệt rõ: core vẫn chạy tốt nếu không mua commercial layer.

---

## 4. Deployment model mở

- Docker Compose deploy cho local và small production
- Kubernetes Helm chart cho production lớn hơn
- Docs deploy public
- Environment config public

---

## 5. Community contribution

- Mọi người có thể:
  - report bug
  - propose feature
  - submit PR
  - dịch docs
  - viết integration

- Maintainer review PR với tiêu chí:
  - có hợp backbone không
  - có phá module boundary không
  - có giữ audit / trust không
  - có thêm dependency không cần thiết không

---

## 6. Docs và source

- Mã nguồn public
- Docs cho agents (tiếng Anh, technical) public
- Docs cho human (tiếng Việt) public
- Commercial docs (hosted pricing, enterprise feature) private

---

## 7. Brand và control

- Core repo giữ brand identity
- Fork không được dùng brand gốc gây nhầm lẫn
- Contribution phải tuân theo code of conduct

---

## 8. Revenue path

Không bán license core. Bán:

- Hosted cloud (không phải ai cũng muốn self-host)
- Enterprise add-ons
- Migration / onboarding services
- Support contract

Revenue không được ảnh hưởng đến core open-source quality.

---

## 9. Khi nào cần thương mại hóa

Dấu hiệu sẵn sàng:

- Có user thật dùng self-host
- Có user hỏi về hosted version
- Có user yêu cầu enterprise features (SSO, compliance, SLA)
- Core đã ổn định, không thay đổi hàng tuần

---

## 10. Open-source triết lý

Vroom HR mở mã nguồn vì:

- company Việt Nam cần HR system đáng tin cậy, có thể kiểm tra
- HR data rất nhạy cảm, cần minh bạch
- Mô hình SaaS nước ngoài không phù hợp mọi company
- Cộng đồng giúp sản phẩm tốt hơn

---

## Một câu nhớ nhanh

**Vroom HR là open-source vì trust và adoption, core vẫn miễn phí, nhưng có đường revenue rõ qua hosted / enterprise / support khi sản phẩm đủ chín.**

