# Báo cáo đồ án tốt nghiệp Vroom HR

> Phiên bản markdown để làm nền cho báo cáo chính thức.
> Nội dung bám theo hướng: HR Workflow Assistant, không phải HRM suite.

## Chương 1. Giới thiệu

### 1.1. Bối cảnh thực tế

Bộ phận HR tại các doanh nghiệp Việt Nam (đặc biệt là SME và startup) thường phải xử lý khối lượng tác vụ hành chính lớn và phân tán: email ứng viện trộn lẫn với email nội bộ, CV đính kèm nhiều định dạng, lịch phỏng vấn trao đổi qua lại nhiều vòng, checklist onboarding hay bị quên bước, dữ liệu HR nằm rải rác trong email, drive, bảng tính, chat và các hệ thống HRM hiện có.

Trong khi đó, thị trường HRM Việt Nam đã có nhiều sản phẩm tương đối hoàn thiện về chức năng quản lý (1Office, Base HR, OrangeHRM, Odoo HR). Tuy nhiên, các sản phẩm này thường được thiết kế theo hướng "thay thế toàn bộ quy trình HR", đòi hỏi doanh nghiệp phải chuyển đổi hệ thống hoặc vận hành song song — một rào cản đáng kể đối với các doanh nghiệp đã quen với workflow hiện tại.

Vấn đề không nằm ở chỗ "thiếu một HRM mới", mà ở chỗ HR cần các công cụ trợ lý nhỏ, nhanh, rõ trạng thái, có thể tích hợp bên cạnh hệ thống hiện có và giảm thao tác lặp.

### 1.2. Lý do chọn đề tài

Lựa chọn xây dựng Vroom HR với hướng tiếp cận "HR Workflow Assistant" xuất phát từ ba nhận định:

1. **Pain thực tế có thể chứng minh** — Các tác vụ như phân loại email tuyển dụng, đọc và tóm tắt CV, sắp xếp lịch phỏng vấn, tạo checklist onboarding là những công việc lặp đi lặp lại hàng ngày, tốn thời gian và dễ sai sót. Giải pháp cải thiện các tác vụ này tạo ra giá trị rõ ràng và có thể đo lường.

2. **Phù hợp với quy mô đồ án tốt nghiệp** — Hướng "tool hỗ trợ HR" có phạm vi hẹp hơn một HRM suite, tập trung vào chiều sâu của một số tác vụ cụ thể. Điều này giúp đồ án có thể hoàn thành trong khung thời gian giới hạn, đồng thời đảm bảo tính khả thi của việc demo end-to-end.

3. **Có điểm khác biệt so với sản phẩm hiện có** — Các HRM hiện tại thường yếu về hỗ trợ AI, thiếu khả năng tự động hóa tác vụ cụ thể và khó tùy biến cho quy trình đặc thù Việt Nam. Vroom HR tập trung vào AI-native, task-centric, audit-first — một hướng đi chưa được khai thác triệt để.

### 1.3. Mục tiêu đồ án

Mục tiêu tổng quát của đồ án là xây dựng một hệ thống công cụ hỗ trợ tác vụ HR (HR Workflow Assistant / Tool Manager), bao gồm:

- **Tự động hóa xử lý đầu vào**: phân loại email, trích xuất thông tin từ CV, nhận diện yêu cầu công việc
- **Giảm thời gian xử lý thủ công**: tóm tắt nội dung, tạo nháp phản hồi, đề xuất lịch, sinh checklist
- **Cung cấp trạng thái và khả năng theo dõi**: bảng điều khiển công việc, audit trail, traceability
- **Đảm bảo nguyên tắc AI hỗ trợ có trách nhiệm**: AI chỉ đọc, phân loại, tóm tắt, đề xuất, soạn nháp — không tự ý ghi đè dữ liệu, không thay thế quyết định của HR
- **Không thay thế HRM hiện tại** mà hoạt động như một lớp tăng năng suất bên cạnh

### 1.4. Phạm vi đồ án

**Trọng tâm — HR Inbox Intelligence:**

- Tiếp nhận và phân loại email đầu vào (ứng viên, nội bộ, đối tác, thông báo)
- Phân tích CV từ file đính kèm → tóm tắt cấu trúc
- Tạo nháp lịch phỏng vấn
- Tạo checklist onboarding tự động
- Soạn nháp email phản hồi
- Dashboard trạng thái công việc HR

**Không nằm trong phạm vi:**

- Hệ thống HRM đầy đủ (payroll, attendance, employee-facing self-service)
- App store / plugin platform
- Tích hợp sâu với các HRM bên thứ ba (chỉ đọc đầu vào)

### 1.5. Đối tượng sử dụng

- **HR:** người dùng chính, xử lý công việc hàng ngày qua inbox trung tâm
- **Quản lý / Owner:** theo dõi trạng thái tổng quan, xem pipeline ứng viên, onboarding
- **Candidate (gián tiếp):** nhận email phản hồi, lịch phỏng vấn từ hệ thống

### 1.6. Phương pháp tiếp cận

Đồ án áp dụng quy trình BA-first:

1. **Phân tích nghiệp vụ (Business Analysis)** — Xác định pain points, stakeholders, use cases, business rules, edge cases
2. **Thiết kế hệ thống** — Kiến trúc, module, data model, AI boundary, audit
3. **Triển khai** — Công nghệ, cấu trúc mã nguồn, demo flow
4. **Đánh giá** — Kết quả đạt được, hạn chế, hướng phát triển

Tài liệu phân tích là source of truth, được duy trì xuyên suốt đồ án và cập nhật theo từng quyết định thiết kế.

### 1.7. Ý nghĩa thực tiễn

- Giảm thời gian xử lý email HR và CV xuống đáng kể so với làm thủ công
- Giảm sai sót trong phân loại và theo dõi trạng thái
- Cung cấp cái nhìn tổng quan về khối lượng công việc HR cho quản lý
- Tạo tiền đề cho các doanh nghiệp VN có thể áp dụng công cụ AI hỗ trợ HR mà không cần thay đổi toàn bộ hạ tầng hiện có

### 1.8. Định nghĩa HR trong phạm vi đồ án

Trong đồ án này, "HR" được hiểu theo nghĩa vận hành công việc của bộ phận nhân sự, không phải là toàn bộ HRM suite. Phạm vi HR mà Vroom HR tập trung hỗ trợ bao gồm các tác vụ đầu vào, xử lý, theo dõi và phản hồi liên quan đến tuyển dụng và onboarding.

#### 1.8.1. Chuỗi công việc HR

- **Attract / Receive**: tiếp nhận email, CV, yêu cầu tuyển dụng, thông tin đầu vào từ nhiều nguồn
- **Recruit / Screen**: phân loại, đọc nhanh, tóm tắt, sàng lọc hồ sơ
- **Schedule / Coordinate**: sắp xếp lịch phỏng vấn, nhắc việc, follow-up
- **Onboard**: tạo checklist onboarding, hướng dẫn bước đầu, theo dõi trạng thái
- **Operate / Track**: theo dõi tiến độ, giữ trạng thái rõ ràng, audit thay đổi
- **Respond**: soạn nháp email phản hồi, trả lời ứng viên / nội bộ

#### 1.8.2. Phạm vi HR mà Vroom HR hỗ trợ

- Phân loại email tuyển dụng và nội bộ
- Trích xuất và tóm tắt CV
- Sinh nháp phản hồi / lịch phỏng vấn
- Tạo checklist onboarding
- Theo dõi trạng thái công việc và audit
- Hỗ trợ thao tác lặp của HR bằng AI đọc / tóm tắt / draft

#### 1.8.3. Ngoài phạm vi

- Payroll
- Attendance
- Employee-facing self-service
- Performance management full
- Compensation engine
- HR policy administration đầy đủ

> Kết luận: Vroom HR là HR workflow assistant cho tác vụ HR hằng ngày, không phải hệ thống quản lý nhân sự toàn diện.

### 1.9. Câu chuyện người dùng

Một buổi sáng đầu tuần, người làm HR mở hộp thư trong tâm thế quen thuộc: hàng chục email mới đang chờ, trong đó có thư ứng tuyển, phản hồi từ ứng viên, trao đổi nội bộ, nhắc việc từ quản lý và những thông tin rời rạc cần được xử lý ngay. Thay vì phải lần lượt mở từng email, tải từng CV, tự ghi nhớ ai đang ở bước nào, rồi liên tục chuyển qua lại giữa nhiều tab và nhiều công cụ khác nhau, họ chỉ cần đi vào Vroom HR.

Ngay từ khoảnh khắc đầu tiên, hệ thống không buộc họ phải suy nghĩ theo cách của phần mềm, mà đón họ bằng đúng thứ họ đang cần: một inbox trung tâm rõ ràng, các mục được phân loại sẵn theo ngữ cảnh, các CV được tóm tắt nhanh theo cấu trúc dễ đọc, và những tác vụ tiếp theo được gợi ý đúng lúc. Người dùng không phải bắt đầu từ con số không; hệ thống đã làm phần “dọn đường” trước, để họ đi thẳng vào phần quan trọng nhất: ra quyết định.

Điều tạo nên cảm giác “đây đúng là thứ mình cần” không nằm ở việc hệ thống làm thay hoàn toàn công việc HR, mà ở chỗ nó giảm bớt tối đa những ma sát nhỏ nhưng lặp đi lặp lại mỗi ngày. Không còn cảm giác bị kéo vào một mê cung của email, file đính kèm, lịch hẹn và checklist rời rạc. Không còn phải nhớ thủ công xem việc nào đã xử lý, việc nào còn pending, việc nào cần phản hồi ngay. Mọi thứ được gom về một luồng làm việc liên tục, mạch lạc và ít đứt gãy hơn.

Vroom HR vì thế tạo ra một trải nghiệm rất gần với cách con người thật sự muốn làm việc: ít bước hơn, ít phải nhớ hơn, ít phải chuyển ngữ cảnh hơn, nhưng vẫn giữ toàn quyền quyết định ở người dùng. AI chỉ đọc, tóm tắt, gợi ý và chuẩn bị nháp; người HR vẫn là người chốt. Chính sự kết hợp này làm cho hệ thống có cảm giác “smooth”: không gây áp lực học cách dùng, không ép thay đổi thói quen làm việc quá mạnh, mà âm thầm làm cho từng thao tác trở nên nhẹ hơn và đáng tin hơn.

Nói cách khác, câu chuyện người dùng của Vroom HR không phải là câu chuyện về một phần mềm quản lý nhân sự toàn diện. Đó là câu chuyện về một trợ lý workflow biết đứng đúng chỗ, làm đúng việc, và giúp người làm HR cảm thấy rằng công cụ này sinh ra là để phục vụ đúng những gì họ đang thiếu mỗi ngày.

### 1.10. Ý nghĩa thực tiễn

- Giảm thời gian xử lý email HR và CV xuống đáng kể so với làm thủ công
- Giảm sai sót trong phân loại và theo dõi trạng thái
- Cung cấp cái nhìn tổng quan về khối lượng công việc HR cho quản lý
- Tạo tiền đề cho các doanh nghiệp VN có thể áp dụng công cụ AI hỗ trợ HR mà không cần thay đổi toàn bộ hạ tầng hiện có

## Chương 2. Khảo sát và phân tích

### 2.1. Mục tiêu khảo sát

Mục tiêu của phần khảo sát và phân tích là làm rõ bài toán mà Vroom HR cần giải quyết trước khi đi vào thiết kế hệ thống. Cụ thể:

- Xác định các pain points thực tế của bộ phận HR trong bối cảnh doanh nghiệp Việt Nam
- Làm rõ nhóm người dùng chính và nhu cầu của từng nhóm
- Khảo sát các giải pháp hiện có để xác định mức độ phù hợp với bài toán
- Tìm ra khoảng trống mà Vroom HR có thể khai thác mà không bị trùng lặp với HRM truyền thống
- Chốt lại phạm vi giải quyết để tránh mở rộng thành một HRM suite đầy đủ

### 2.2. Bối cảnh vận hành hiện tại của HR

Trong thực tế, quy trình làm việc của HR thường không nằm ở một công cụ duy nhất mà trải rộng trên nhiều kênh khác nhau. Một email tuyển dụng có thể đi kèm CV, file đính kèm, trao đổi nội bộ trên chat, lịch hẹn trên calendar, và các dữ liệu bổ sung trong bảng tính hoặc drive.

Mô hình làm việc phân mảnh này dẫn đến các vấn đề phổ biến:

- **Thông tin đầu vào rời rạc**: CV, yêu cầu tuyển dụng, phản hồi ứng viên, lịch phỏng vấn đều nằm ở các nơi khác nhau
- **Xử lý thủ công nhiều bước**: HR phải đọc, lọc, tóm tắt, phản hồi và cập nhật trạng thái bằng tay
- **Khó theo dõi trạng thái**: không phải lúc nào cũng rõ một ứng viên đang ở bước nào hoặc một checklist onboarding đã hoàn thành đến đâu
- **Dễ bỏ sót việc lặp lại**: các email quan trọng có thể bị trộn lẫn với email không liên quan
- **Thiếu audit và traceability**: khó biết ai đã xem, ai đã thay đổi, thay đổi lúc nào

Nhìn chung, bài toán thực tế của HR không chỉ là "thiếu tính năng quản lý", mà là thiếu một lớp trợ lý công việc có thể gom dữ liệu rời rạc, giảm thao tác lặp và đưa ra trạng thái rõ ràng hơn.

### 2.3. Phân tích người dùng

#### 2.3.1. HR

**Vai trò:** người dùng chính và duy nhất của hệ thống.

**Mục tiêu:**

- Xử lý nhanh email và CV đầu vào
- Tạo và theo dõi lịch phỏng vấn
- Ghi nhận trạng thái ứng viên / nhân sự
- Sinh checklist onboarding và email phản hồi nhanh

**Pain points:**

- Quá nhiều thông tin phải đọc và phân loại thủ công
- Dễ bỏ sót email hoặc file đính kèm quan trọng
- Phải lặp lại các thao tác soạn nháp, chuyển trạng thái, follow-up
- Khó có một màn hình trung tâm để biết việc nào đang pending

**Dữ liệu họ chạm vào:**

- Email
- CV / file đính kèm
- lịch phỏng vấn
- checklist onboarding
- trạng thái ứng viên / tác vụ

**Quyền:**

- Xem, phân loại, cập nhật trạng thái, tạo nháp phản hồi, xác nhận hoặc chỉnh sửa đề xuất của AI

> Tool được thiết kế riêng cho HR. Các nhóm người dùng khác (quản lý, candidate) không nằm trong phạm vi của đồ án.

### 2.4. Khảo sát giải pháp hiện có

#### 2.4.1. Mục tiêu khảo sát

Trước khi thiết kế tính năng, cần xác định rõ thị trường đã có những gì, giải pháp nào gần với bài toán nhất, và khoảng trống nào Vroom HR có thể khai thác. Mục tiêu là tránh xây lại những gì đã có và định vị rõ vị trí của đồ án.

#### 2.4.2. Phân nhóm giải pháp

Các giải pháp hiện có được chia thành bốn nhóm dựa trên cách tiếp cận bài toán HR:

- **HRM/HRIS suite**: 1Office, Base HR, OrangeHRM, BambooHR, Odoo HR
- **Workflow / project tools**: Plane, Notion, Trello, ClickUp
- **AI recruiting tools**: Ideal, HireVue, Manatal, CV parsing APIs (Affinda, Sovren)
- **HR template / automation tools**: forms, email templates, onboarding checklist tools

#### 2.4.3. Tiêu chí phân tích

Mỗi giải pháp được đánh giá theo cùng một khung:

- Mục tiêu chính
- Mạnh ở đâu
- Yếu ở đâu
- Hỗ trợ HR workflow tác vụ nhỏ mức nào
- AI support có thực chất không
- Self-host / cloud
- Audit / traceability
- Phù hợp bối cảnh Việt Nam
- Phù hợp với phạm vi đồ án

#### 2.4.4. Nhận xét từng nhóm

**Nhóm 1 — HRM/HRIS suite**

Đây là nhóm sản phẩm mạnh nhất về chức năng quản lý toàn diện. Họ bao phủ hầu hết quy trình HR từ tuyển dụng, chấm công, tính lương, phúc lợi đến báo cáo.

Điểm mạnh: quy trình chuẩn hóa, dữ liệu tập trung, báo cáo đa dạng.

Điểm yếu khi xét trên bài toán của Vroom HR:

- Đòi hỏi chuyển đổi hệ thống, không phải lớp bổ trợ
- Tác vụ nhỏ (phân loại email, tóm tắt CV thủ công) không được tối ưu
- AI hỗ trợ còn yếu hoặc mang tính hình thức
- Đa số là cloud, ít lựa chọn self-host (trừ OrangeHRM, Odoo)
- Không phù hợp với phạm vi đồ án vì quá toàn diện, dễ overbuild

**Nhóm 2 — Workflow / project tools**

Các công cụ này linh hoạt, có thể tracking bất kỳ quy trình nào bằng bảng Kanban hoặc timeline.

Điểm mạnh: linh hoạt, dễ tùy chỉnh, chi phí thấp.

Điểm yếu:

- Không hiểu nghiệp vụ HR, chỉ là layer tracking chung
- Thiếu hiểu biết về CV, email tuyển dụng, lịch phỏng vấn
- AI hỗ trợ nghiệp vụ HR gần như không có
- Audit không được thiết kế cho HR context

**Nhóm 3 — AI recruiting tools**

Một số công cụ tập trung vào AI cho từng khâu như đọc CV, match kỹ năng, sắp lịch, chatbot phản hồi.

Điểm mạnh: AI đúng chỗ, giảm thao tác thủ công ở khâu được hỗ trợ.

Điểm yếu:

- Thường chỉ giải quyết một khâu, không có pipeline hoàn chỉnh
- Tích hợp với workflow HR hiện tại còn khó
- Không self-host
- Phù hợp một phần nhưng cần gom lại nhiều sản phẩm để cover hết pipeline

**Nhóm 4 — HR template / automation tools**

Các công cụ cung cấp mẫu có sẵn cho email, form, checklist onboarding.

Điểm mạnh: dễ dùng, giảm lặp lại ở một bước cụ thể.

Điểm yếu:

- Thiếu khả năng kết nối pipeline
- Không phải system of record
- Không audit
- Rất dễ bị thay thế

#### 2.4.5. Ma trận so sánh nhanh

| Tiêu chí                    | HRM suite  | Workflow tools | AI recruiting | VROOM HR         |
| --------------------------- | ---------- | -------------- | ------------- | ---------------- |
| Quản lý quy trình toàn diện | cao        | trung bình     | thấp          | trung bình (hẹp) |
| AI hỗ trợ tác vụ nhỏ        | yếu        | không          | tốt (1 khâu)  | tốt (pipeline)   |
| Phân loại / tóm tắt đầu vào | yếu        | không          | tốt           | tốt              |
| Self-host                   | hiếm       | có             | hiếm          | có (first-class) |
| Audit theo thiết kế         | trung bình | yếu            | yếu           | có               |
| Phù hợp với doanh nghiệp VN | trung bình | trung bình     | thấp          | cao              |
| Phù hợp scope đồ án         | thấp       | thấp           | trung bình    | cao              |
| Bổ trợ bên cạnh hệ thống cũ | khó        | trung bình     | dễ            | dễ               |
| Audit theo thiết kế         | trung bình | yếu            | yếu           | có               |
| Phù hợp với doanh nghiệp VN | trung bình | trung bình     | thấp          | cao              |
| Phù hợp scope đồ án         | thấp       | thấp           | trung bình    | cao              |
| Bổ trợ bên cạnh hệ thống cũ | khó        | trung bình     | dễ            | dễ               |

#### 2.4.6. Kết luận

Khảo sát cho thấy:

- Thị trường có nhiều HRM mạnh về quản lý, nhưng mỗi sản phẩm đều yếu ở mảng tác vụ cụ thể có AI hỗ trợ
- Workflow tools linh hoạt nhưng thiếu hiểu biết nghiệp vụ HR
- AI recruiting tools tốt nhưng chỉ ở một khâu, chưa bao trùm pipeline đầu vào
- Vroom HR đứng ở khoảng trống: "HR workflow assistant — AI-native, task-centric, audit-first, bổ trợ bên cạnh HRM hiện có"

Khoảng trống này phù hợp với phạm vi đồ án và có thể tạo ra giá trị thực tế mà không cạnh tranh trực tiếp với các HRM suite.

### 2.5. Pain points & root cause

#### 2.5.1. Tổng quan

Các pain points được tổng hợp từ bối cảnh vận hành thực tế của bộ phận HR tại SME và startup Việt Nam, không phải suy diễn từ lý thuyết. Mỗi pain đều có thể truy ra root cause và kéo theo tác động cụ thể.

#### 2.5.2. Pain points chính

**(P1) Email đầu vào lẫn lộn, khó phân loại**

Mỗi ngày HR nhận một lượng email đa dạng: tuyển dụng kèm CV, phản hồi từ ứng viên, trao đổi nội bộ, liên hệ từ đối tác, thông báo hệ thống, spam. Các email này lẫn lộn trong cùng một inbox, buộc HR phải đọc tay từng cái để phân loại. Không có trợ lý gắn nhãn hoặc ưu tiên.

- **Hệ quả**: mất 20-30 phút mỗi buổi sáng chỉ để lọc mail; dễ bỏ sót CV hoặc phản hồi ứng viên quan trọng
- **Tần suất**: hằng ngày

**(P2) CV đính kèm nhiều định dạng, đọc thủ công**

CV được gửi dưới dạng PDF, DOCX, hình ảnh, đôi khi là text thuần trong thân email. Mỗi định dạng yêu cầu cách xử lý khác nhau. HR phải mở từng file, đọc, ghi nhớ thông tin chính, rồi quyết định next action.

- **Hệ quả**: tốn vài phút cho mỗi CV; khó so sánh nhanh giữa nhiều ứng viên
- **Tần suất**: hằng ngày, theo mùa tuyển dụng

**(P3) Lịch phỏng vấn phải trao đổi qua lại nhiều vòng**

Để xếp lịch, HR thường gửi email hỏi giờ rảnh của ứng viên, sau đó đối chiếu với lịch của người phỏng vấn. Quy trình này dễ kéo dài 2-4 vòng email, đặc biệt với ứng viên ngoài giờ hành chính.

- **Hệ quả**: mất thời gian, dễ lệch thông tin giữa các bên
- **Tần suất**: mỗi lần cần hẹn

**(P4) Onboarding checklist không có sẵn hoặc hay thiếu bước**

Khi có nhân sự mới onboard, HR thường làm theo kinh nghiệm cá nhân. Các bước như cấp tài khoản, hướng dẫn nội quy, giới thiệu team, cài đặt thiết bị... dễ bị quên nếu không có công cụ theo dõi.

- **Hệ quả**: thiếu nhất quán, onboarding không hoàn chỉnh, nhân viên mới mất thời gian để tự xoay sở
- **Tần suất**: mỗi lần onboard

**(P5) Không có dashboard trạng thái tổng quan**

HR không có một nơi duy nhất để xem: đang có bao nhiêu ứng viên, người nào ở bước nào, việc gì đang pending, việc gì quá hạn. Trạng thái phải hỏi hoặc nhớ.

- **Hệ quả**: mất visibility, quản lý khó can thiệp kịp
- **Tần suất**: tác động lâu dài

**(P6) Thiếu audit trail và traceability**

Khi xảy ra vấn đề (ví dụ: quên reply một ứng viên quan trọng), rất khó truy ngược lại lịch sử tương tác: ai đã xem? đã phản hồi gì? khi nào? thay đổi trạng thái do ai?

- **Hệ quả**: khó giải trình, khó cải tiến quy trình
- **Tần suất**: tiềm ẩn, xảy ra khi có tranh chấp hoặc sai sót

#### 2.5.3. Root cause tổng quát

Các pain points trên không phải do "thiếu một hệ thống HRM toàn diện", mà xuất phát từ ba nguyên nhân gốc:

1. **Dữ liệu phân mảnh** — email, CV, lịch, checklist, trạng thái nằm ở các nơi riêng biệt
2. **Thiếu lớp xử lý đầu vào** — không có AI hỗ trợ phân loại, tóm tắt, trích xuất trước khi HR vào việc
3. **Workflow HR chưa được chuẩn hóa** — mỗi tác vụ là một bước thủ công, không được nối thành pipeline có trạng thái rõ

#### 2.5.4. Tác động tổng thể lên hoạt động HR

- **Tốn thời gian**: HR dành tỷ lệ lớn thời gian cho xử lý thủ công thay vì tương tác với ứng viên và nhân sự
- **Sai sót**: dễ quên, dễ nhầm, dễ mất thông tin
- **Follow-up chậm**: ứng viên chờ lâu, onboarding kéo dài
- **Thiếu đo lường**: khó biết pipeline hoạt động thế nào, khâu nào yếu
- **Khó mở rộng**: khi khối lượng công việc tăng, HR phải làm thêm giờ thay vì scale bằng công cụ

#### 2.5.5. Hàm ý cho thiết kế Vroom HR

Từ mỗi pain point có thể suy ra yêu cầu chức năng tương ứng:

| Pain point                 | Hàm ý thiết kế                                            |
| -------------------------- | --------------------------------------------------------- |
| (P1) Email lẫn lộn         | Inbox triage module: phân loại, gắn nhãn, ưu tiên         |
| (P2) CV nhiều format       | CV parsing engine: trích xuất thông tin, tóm tắt          |
| (P3) Lịch nhiều vòng       | Interview scheduling assistant: gợi ý slot, draft lời mời |
| (P4) Onboarding thiếu bước | Onboarding checklist generator: template + theo dõi       |
| (P5) Không dashboard       | Status board: pipeline trực quan, trạng thái từng bước    |
| (P6) Thiếu audit           | Audit trail: ghi mọi thay đổi, truy vết ai-làm gì-khi nào |

Toàn bộ các chức năng này xoay quanh inbox trung tâm, tạo thành pipeline liên tục từ đầu vào đến hoàn thành.

#### 2.5.6. Kết luận

Pain points của HR không phải "thiếu một HRM mới". Pain thật là:

- Công việc bị vỡ vụn trên nhiều kênh
- Thiếu AI hỗ trợ xử lý đầu vào
- Thiếu công cụ gom trạng thái và tác vụ về một nơi

Vroom HR, với định hướng workflow assistant, giải quyết chính xác các pain này — không cần thay thế hệ thống nào, chỉ cần một lớp trợ lý ở giữa.

### 2.6. Gap analysis

#### 2.6.1. Mục tiêu

Gap analysis nhằm xác định khoảng trống giữa những gì thị trường HR hiện có và những gì bài toán thực tế của HR cần — từ đó định vị chính xác vị trí của Vroom HR.

#### 2.6.2. Thị trường đã có gì

Qua khảo sát (mục 2.4), có thể tổng hợp:

- **HRM suite**: quản lý nhân sự toàn diện, phù hợp doanh nghiệp lớn
- **Workflow tools**: tracking linh hoạt, không hiểu nghiệp vụ HR
- **AI recruiting tools**: tốt ở một khâu đơn lẻ (CV parsing, scheduling)
- **HR template tools**: mẫu sẵn nhưng không phải system of record

#### 2.6.3. Còn thiếu gì

Phân tích cho thấy khoảng trống rõ rệt:

1. **Thiếu một công cụ AI-native cho HR ops hằng ngày**
   - Phân loại inbox, tóm tắt CV, sinh nháp, tracking pipeline
   - Công cụ hiện tại yếu ở layer "xử lý đầu vào"

2. **Thiếu lớp bổ trợ bên cạnh hệ thống hiện có**
   - Sản phẩm hiện tại yêu cầu chuyển đổi hoặc nhập dữ liệu
   - HRM hiện tại không có plugin/assistant layer

3. **Thiếu khả năng kết nối pipeline**
   - Các bước (CV → phân loại → lịch → onboarding) không được nối
   - HR phải tự nối bằng tay giữa email, drive, chat, checklist

4. **Thiếu audit được thiết kế sẵn**
   - Audit hiện tại là phụ trợ, không phải thiết kế chủ đạo
   - Không thể truy vết nhanh ai làm gì với email/CV

5. **Thiếu hỗ trợ đặc thù Việt Nam**
   - Luật lao động VN (BHXH, thuế TNCN) không được hỗ trợ native
   - Template email/CV phù hợp văn hóa VN còn hạn chế

#### 2.6.4. Vroom HR đứng ở khoảng trống nào

Vroom HR không cạnh tranh với HRM suite. Nó đứng ở layer giữa:

```
[Đầu vào] → VROOM HR (xử lý, phân loại, hỗ trợ) → [HR action]
                    ↓
             Audit + Status
```

Cụ thể:

- **Không thay thế** 1Office, Base, OrangeHRM
- **Nhưng bổ sung** lớp AI-native để HR xử lý đầu vào nhanh hơn
- **Tích hợp bằng cách** đọc email, gắn nhãn, đề xuất, draft
- **Không yêu cầu** chuyển đổi dữ liệu hay training lại quy trình

#### 2.6.5. Những gì Vroom HR nên làm

| Khoảng trống     | Vroom HR làm gì                             | Mức độ ưu tiên |
| ---------------- | ------------------------------------------- | -------------- |
| AI-native HR ops | Inbox triage + CV parsing + summary         | P0             |
| Pipeline kết nối | Từ email → task → trạng thái                | P0             |
| Lớp bổ trợ       | Đọc email, không cần nhập liệu              | P0             |
| Audit by design  | Ghi mọi hành động, truy vết được            | P1             |
| Hỗ trợ VN        | Template tiếng Việt, luật VN cho onboarding | P1             |
| Dashboard        | Pipeline + pending + overdue                | P1             |

#### 2.6.6. Những gì Vroom HR không nên làm

- Xây HRM suite đầy đủ
- Thay thế payroll / attendance / check-in
- Cạnh tranh trực tiếp với 1Office hay Base
- Yêu cầu doanh nghiệp chuyển đổi toàn bộ quy trình

#### 2.6.7. Kết luận

Khoảng trống thị trường rõ ràng: không có sản phẩm nào kết hợp AI-native, task-centric, audit-first và self-host trong một package nhỏ phù hợp với SME/startup Việt Nam. Vroom HR lấp đầy khoảng trống này mà không đụng đến vùng đã có sản phẩm mạnh.

### 2.7. Định vị sản phẩm

#### 2.7.1. Định vị tổng quan

Vroom HR được định vị là một **HR Workflow Assistant**: công cụ hỗ trợ HR xử lý công việc hằng ngày nhanh hơn, rõ trạng thái hơn và ít thao tác thủ công hơn. Sản phẩm không nhắm tới việc thay thế toàn bộ HRM/HRIS hiện có, mà hoạt động như một lớp trợ lý nằm giữa đầu vào và hành động của HR.

#### 2.7.2. Câu định vị

> Vroom HR là trợ lý workflow cho HR, giúp phân loại, tóm tắt, nháp phản hồi và theo dõi các tác vụ tuyển dụng/onboarding trên một luồng làm việc tập trung, audit-first và AI-native.

#### 2.7.3. Khác biệt so với HRM truyền thống

- **HRM truyền thống**: quản lý toàn diện, nặng cấu hình, bao trùm nhiều phân hệ
- **Vroom HR**: hẹp hơn, sâu hơn ở tác vụ đầu vào và follow-up, tập trung vào tốc độ xử lý và khả năng truy vết

#### 2.7.4. Trục sản phẩm

Trục chính của Vroom HR là **HR Inbox Intelligence** — tức là biến inbox và đầu vào rời rạc thành một pipeline có thể đọc, phân loại, đề xuất và theo dõi.

Các năng lực cốt lõi:

- Đọc và phân loại email / CV
- Tóm tắt nội dung quan trọng
- Tạo nháp phản hồi hoặc lời mời
- Gắn trạng thái và theo dõi tiến độ
- Ghi audit đầy đủ cho từng hành động

#### 2.7.5. Nguyên tắc định vị

- Không cạnh tranh trực tiếp với HRM suite
- Không ôm toàn bộ vòng đời nhân sự
- Tập trung vào tác vụ có tần suất cao và giá trị lặp lại lớn
- Ưu tiên self-host, audit và khả năng bổ trợ bên cạnh hệ thống sẵn có
- Dùng AI đúng vai: đọc, hiểu, tóm tắt, draft, đề xuất

#### 2.7.6. Kết luận

Định vị này giúp Vroom HR có phạm vi đủ hẹp để làm tốt trong đồ án, nhưng đủ sâu để chứng minh giá trị thực tế. Đây là một công cụ hỗ trợ HR theo hướng vận hành, không phải một bộ HRM đầy đủ.

### 2.8. Kết luận chương

Sau khi khảo sát và phân tích, có thể rút ra ba kết luận chính:

1. **Pain thật nằm ở vận hành hằng ngày của HR**, đặc biệt là inbox, CV, lịch và onboarding.
2. **Thị trường đã có nhiều HRM suite**, nhưng còn thiếu một lớp trợ lý AI-native cho các tác vụ nhỏ và liên tục.
3. **Vroom HR nên được định vị là HR Workflow Assistant**, tập trung vào xử lý đầu vào, theo dõi trạng thái và audit thay vì thay thế toàn bộ hệ thống HR.

Từ kết luận này, chương tiếp theo sẽ chuyển sang thiết kế hệ thống và mô hình chức năng dựa trên phạm vi đã chốt.

## Chương 3. Thiết kế hệ thống

### 3.1. Kiến trúc tổng quan

Vroom HR được thiết kế theo hướng AI-native, task-centric, audit-first và self-host. Thay vì xây một HRM suite đầy đủ, hệ thống chỉ tập trung vào lớp xử lý công việc HR hằng ngày: nhận đầu vào, hiểu ngữ cảnh, giảm thao tác lặp, hỗ trợ ra quyết định và giữ traceability rõ ràng.

#### 3.1.1. Sơ đồ kiến trúc tổng thể

Kiến trúc tổng thể tuân theo mô hình nhiều lớp, mỗi lớp có trách nhiệm và hướng phụ thuộc rõ ràng:

```
  ┌───────────────────────────────────────────────────┐
  │                   FRONTEND                        │
  │  Next.js · shadcn/ui · Tailwind · luồng màn hình  │
  └──────────────────┬────────────────────────────────┘
                     │ REST API (HTTP only)
                     ▼
  ┌───────────────────────────────────────────────────┐
  │              API LAYER (Routers)                   │
  │  · Xác thực (cookie JWT)                           │
  │  · Kiểm tra quyền                                  │
  │  · Error handling                                  │
  └──────────────────┬────────────────────────────────┘
                     │
                     ▼
  ┌───────────────────────────────────────────────────┐
  │            APPLICATION LAYER (Services)             │
  │  · Use case orchestration                          │
  │  · Business rules                                  │
  │  · AI integration (classification, parsing)        │
  │  · Draft generation                                │
  └──────────────────┬────────────────────────────────┘
                     │
                     ▼
  ┌───────────────────────────────────────────────────┐
  │              DOMAIN LAYER (Entities)               │
  │  · Domain models                                   │
  │  · Invariants & validation                         │
  │  · State machines (pipeline, onboarding)           │
  └──────────────────┬────────────────────────────────┘
                     │
                     ▼
  ┌───────────────────────────────────────────────────┐
  │           INFRASTRUCTURE LAYER                     │
  │  PostgreSQL ─ Redis ─ MinIO ─ AI Provider          │
  │  Email (IMAP/SMTP) ─ Audit Log                     │
  └───────────────────────────────────────────────────┘
```

**Hướng phụ thuộc**: các layer chỉ phụ thuộc xuống dưới (Frontend → API → Application → Domain → Infrastructure). Domain layer không phụ thuộc vào bất kỳ layer nào bên ngoài.

#### 3.1.2. Phân tích chi tiết từng tầng

**Frontend**: giao diện người dùng xây bằng Next.js. Gồm các khu vực chính:

- Inbox trung tâm (danh sách email đã phân loại)
- Candidate queue (danh sách ứng viên, pipeline)
- Preview panel (xem chi tiết email, CV, lịch)
- Status board (pipeline tổng quan)
- Action panel (xác nhận / chỉnh sửa đề xuất)

**API layer**: FastAPI routers, đăng ký prefix `/api/<module>`. Container pattern đảm bảo DI. Error codes được chuẩn hóa toàn module.

**Application layer**: service classes xử lý từng use case. Orchestration flow gọi domain + infrastructure. Nơi tích hợp AI (gọi LLM provider, parse response).

**Domain layer**: domain entities + exceptions + value objects. Không biết gì về DB hay HTTP. State machine cho trạng thái Candidate, OnboardingTask.

**Infrastructure layer**: PostgreSQL (async), Redis cache, MinIO file store, AI provider (LLM API), email provider (IMAP/SMTP), audit log persistence.

#### 3.1.3. Nguyên tắc thiết kế

- task-centric: ưu tiên tác vụ hơn màn hình
- audit-first: mọi hành động quan trọng đều có dấu vết
- human-in-the-loop: AI chỉ đề xuất, HR xác nhận
- self-host: triển khai độc lập cho từng doanh nghiệp

Luồng dữ liệu cơ bản đi theo chiều:

`Đầu vào (email/CV/yêu cầu) → Vroom HR xử lý → trạng thái/tác vụ/nháp phản hồi → HR xác nhận hoặc chỉnh sửa`

Thiết kế này giúp hệ thống không bị phụ thuộc vào một màn hình duy nhất hay một quy trình cứng nhắc, mà vẫn giữ được tính linh hoạt cho các tình huống HR khác nhau.

### 3.2. Các module chức năng

#### 3.2.1. Bảng module tổng quan

| Module                         | Trách nhiệm chính         | Đầu vào              | Đầu ra                         |
| ------------------------------ | ------------------------- | -------------------- | ------------------------------ |
| Inbox Triage Module            | Phân loại email đầu vào   | Email, metadata      | Nhãn, ưu tiên, candidate draft |
| CV Parsing Engine              | Trích xuất CV             | File đính kèm        | Dữ liệu CV đã parse, summary   |
| Interview Scheduling Assistant | Hỗ trợ xếp lịch           | Candidate, lịch rảnh | Draft lời mời, đề xuất slot    |
| Onboarding Checklist Generator | Sinh checklist onboarding | Candidate accepted   | Checklist, task list           |
| Status Board & Pipeline        | Hiển thị trạng thái       | Workflow items       | Dashboard trạng thái           |
| Audit Trail Engine             | Ghi trace                 | Action event         | Audit log                      |

#### 3.2.2. Inbox Triage Module

Module này xử lý lớp đầu vào từ inbox HR. Mục tiêu là giảm thời gian lọc mail, gắn nhãn, và ưu tiên tác vụ.

Chức năng chính:

- tiếp nhận email đầu vào từ nhiều nguồn
- phân loại email theo ngữ cảnh: ứng viên, nội bộ, đối tác, thông báo
- gợi ý mức độ ưu tiên
- chuẩn bị dữ liệu đầu vào cho các module phía sau

#### 3.2.3. CV Parsing Engine

Module này đọc file đính kèm và trích xuất thông tin quan trọng từ CV.

Chức năng chính:

- nhận file PDF, DOCX hoặc text
- trích xuất các trường dữ liệu quan trọng
- tóm tắt nội dung CV theo cấu trúc dễ đọc
- chuẩn bị thông tin cho bước sàng lọc hoặc phản hồi

#### 3.2.4. Interview Scheduling Assistant

Module này hỗ trợ khâu xếp lịch phỏng vấn.

Chức năng chính:

- gợi ý slot phù hợp
- soạn nháp lời mời phỏng vấn
- hỗ trợ follow-up khi lịch thay đổi
- giảm số vòng trao đổi qua lại giữa HR và ứng viên

#### 3.2.5. Onboarding Checklist Generator

Module này hỗ trợ tạo checklist onboarding theo template và theo dõi tiến độ.

Chức năng chính:

- sinh checklist từ mẫu có sẵn
- đánh dấu trạng thái từng bước
- nhắc việc các đầu việc còn pending
- giúp onboarding đi theo một quy trình nhất quán

#### 3.2.6. Status Board & Pipeline

Module này cung cấp cái nhìn tổng quan về trạng thái công việc.

Chức năng chính:

- hiển thị pipeline ứng viên và tác vụ HR
- cho biết việc nào đang pending, overdue hoặc completed
- giảm phụ thuộc vào ghi nhớ thủ công
- giúp quản lý quan sát trạng thái nhanh hơn

#### 3.2.7. Audit Trail Engine

Module này ghi lại mọi hành động quan trọng trong hệ thống.

Chức năng chính:

- lưu ai đã làm gì, lúc nào, trên dữ liệu nào
- theo dõi thay đổi trạng thái trước và sau
- hỗ trợ truy vết khi có sai sót hoặc cần giải trình
- đảm bảo audit-by-design thay vì audit bổ sung sau

### 3.3. Luồng nghiệp vụ chính

#### 3.3.1. Luồng xử lý email tuyển dụng

1. Email từ ứng viên hoặc nguồn tuyển dụng đi vào inbox trung tâm.
2. Hệ thống phân loại email và nhận diện đây là đầu vào liên quan tuyển dụng.
3. Nếu có CV đính kèm, hệ thống trích xuất và tóm tắt thông tin quan trọng.
4. Hệ thống gợi ý next action như lưu ứng viên, phản hồi, hoặc lên lịch phỏng vấn.
5. HR xem lại, chỉnh sửa nếu cần, rồi xác nhận hành động.
6. Toàn bộ hành động được ghi audit.

#### 3.3.2. Luồng onboarding nhân sự mới

1. Khi có nhân sự mới, hệ thống tạo một luồng onboarding tương ứng.
2. Checklist onboarding được sinh từ template phù hợp.
3. Mỗi bước được theo dõi theo trạng thái rõ ràng.
4. HR hoặc quản lý cập nhật khi từng bước hoàn tất.
5. Hệ thống nhắc các bước còn pending để tránh bỏ sót.
6. Lịch sử thay đổi được lưu lại để truy vết.

### 3.4. Data model

Mô hình dữ liệu của Vroom HR tập trung vào các thực thể gắn trực tiếp với workflow HR.

#### 3.4.1. Các thực thể chính

- **EmailMessage**: email đầu vào hoặc đầu ra
- **Attachment**: file đính kèm như CV hoặc tài liệu liên quan
- **Candidate**: ứng viên được theo dõi trong pipeline
- **ParsedResume**: dữ liệu CV đã được trích xuất và tóm tắt
- **Interview**: lịch phỏng vấn và thông tin liên quan
- **OnboardingTask**: từng đầu việc trong checklist onboarding
- **WorkflowItem**: tác vụ HR ở mức tổng quát
- **AuditLog**: sự kiện thay đổi trong hệ thống

#### 3.4.2. Quan hệ giữa các thực thể

- Một EmailMessage có thể có nhiều Attachment.
- Một Candidate có thể gắn với nhiều EmailMessage và nhiều Interview.
- Một Candidate có thể có một hoặc nhiều ParsedResume theo phiên bản xử lý.
- Một WorkflowItem có thể dẫn đến Interview hoặc OnboardingTask.
- Mỗi thay đổi quan trọng đều tạo AuditLog.

#### 3.4.3. Source of truth

- Email gốc là source of truth cho nội dung đầu vào.
- File đính kèm gốc là source of truth cho dữ liệu CV.
- Trạng thái workflow là source of truth cho tiến độ xử lý.
- AuditLog là source of truth cho lịch sử thay đổi.

#### 3.4.4. Mô tả mức khái niệm của dữ liệu

- **EmailMessage**: lưu metadata email, chủ đề, người gửi, thời điểm nhận, trạng thái xử lý.
- **Attachment**: lưu tên file, loại file, dung lượng, vị trí lưu trữ.
- **Candidate**: lưu danh tính ứng viên, trạng thái pipeline, liên kết job opening nếu có.
- **ParsedResume**: lưu dữ liệu đã trích xuất, summary, độ tin cậy của kết quả parse.
- **Interview**: lưu lịch hẹn, người phỏng vấn, slot thời gian, trạng thái xác nhận.
- **OnboardingTask**: lưu tên nhiệm vụ, trạng thái, người phụ trách, thời hạn.
- **WorkflowItem**: lưu một việc HR cần xử lý ở mức tổng quát.
- **AuditLog**: lưu actor, hành động, đối tượng bị tác động, thời điểm, trước/sau thay đổi.

### 3.5. AI boundary

AI trong Vroom HR được đặt ở vai trò hỗ trợ, không thay thế quyết định của HR.

#### 3.5.1. AI được phép làm

- phân loại email
- tóm tắt nội dung
- trích xuất thông tin từ CV
- gợi ý nháp phản hồi
- đề xuất next action theo ngữ cảnh

#### 3.5.2. AI không được phép làm

- tự ý gửi email thay HR
- tự ý ghi đè dữ liệu nguồn
- tự quyết định loại bỏ ứng viên
- tự động hoàn tất các bước nghiệp vụ có tính quyết định

#### 3.5.3. Human-in-the-loop

Mọi hành động có ảnh hưởng đến trạng thái nghiệp vụ đều cần HR xác nhận. AI chỉ tạo đề xuất; người dùng là người chốt.

#### 3.5.4. Confidence threshold / fallback

Khi độ chắc chắn của AI thấp, hệ thống phải:

- hiển thị kết quả như một gợi ý, không như kết luận chắc chắn
- cho phép HR sửa hoặc bỏ qua
- fallback về xử lý thủ công nếu dữ liệu quá thiếu hoặc mơ hồ

#### 3.5.5. Bảng AI boundary tóm tắt

| Năng lực          | AI được làm                  | AI không được làm | Cơ chế chốt    |
| ----------------- | ---------------------------- | ----------------- | -------------- |
| Email triage      | Phân loại, gắn nhãn, ưu tiên | Tự xoá / tự gửi   | HR xác nhận    |
| CV parsing        | Trích xuất, tóm tắt          | Ghi đè nguồn      | HR sửa nếu cần |
| Scheduling        | Đề xuất slot, draft lời mời  | Tự đặt lịch       | HR chốt        |
| Onboarding        | Gợi ý checklist              | Tự hoàn tất bước  | HR duyệt       |
| Response drafting | Soạn nháp email              | Tự gửi email      | HR xác nhận    |

### 3.6. Audit & traceability

Audit là một phần của thiết kế gốc, không phải tính năng thêm sau.

#### 3.6.1. Nguyên tắc audit-by-design

- mọi hành động quan trọng đều có log
- mọi thay đổi trạng thái đều truy vết được
- audit phải đủ chi tiết để giải trình khi cần

#### 3.6.2. Sự kiện được log

- ai đã mở hoặc xử lý email nào
- ai đã tạo, sửa hoặc xác nhận tác vụ nào
- trạng thái nào đã đổi từ gì sang gì
- AI đã đề xuất gì, HR đã chấp nhận hay chỉnh sửa ra sao

#### 3.6.3. Mục tiêu của audit

- giảm rủi ro quên hoặc mất dấu
- giúp quản lý hiểu quy trình đang vận hành thế nào
- tạo niềm tin khi hệ thống có AI hỗ trợ
- hỗ trợ truy vết khi có sai sót hoặc tranh chấp

#### 3.6.4. Bảng audit event tóm tắt

| Sự kiện                 | Dữ liệu log tối thiểu                        |
| ----------------------- | -------------------------------------------- |
| Email opened            | actor, email_id, timestamp                   |
| Email triaged           | actor, email_id, label, priority             |
| Candidate updated       | actor, candidate_id, before, after           |
| Resume parsed           | actor/system, attachment_id, summary_version |
| Interview drafted       | actor, candidate_id, slot, draft_id          |
| Onboarding task changed | actor, task_id, before, after                |
| Draft confirmed         | actor, draft_id, final_action                |

## Chương 4. Triển khai

- Công nghệ
- Cấu trúc mã nguồn
- Demo flow
- Các màn hình chính

## Chương 5. Đánh giá và kết luận

- Kết quả đạt được
- Hạn chế
- Hướng phát triển
