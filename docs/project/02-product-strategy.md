# Hướng đi phát triển Vroom HR

## Mục tiêu của tài liệu này

Tài liệu này ghi lại hướng đi cần thiết để Vroom HR không chỉ là một bộ tính năng HR, mà trở thành một sản phẩm có **câu chuyện**, có **tư duy hệ thống**, có **góc nhìn người dùng**, và có khả năng phát triển bền vững theo kiểu open-source nhưng vẫn đủ “đứng vững” như một sản phẩm thật.

## Điểm gốc cần thay đổi

Hiện tại, Vroom HR đã có nền móng kỹ thuật và một số module rõ ràng. Nhưng nếu chỉ nhìn như một tập hợp chức năng, sản phẩm sẽ dễ rơi vào trạng thái:

- mỗi module là một mảnh rời
- user thấy đây là một hệ thống HRM “làm được việc”, nhưng không thấy lý do nó sinh ra
- team dễ thêm feature theo phản ứng thay vì theo một trục sản phẩm

Cần chuyển từ tư duy **feature-first** sang **story-first**.

## Câu chuyện sản phẩm

### Vroom HR sinh ra để giải quyết gì

Vroom HR sinh ra từ một thực tế rất phổ biến:

- công ty Việt Nam cần quản trị con người thật
- quy trình HR thường bị đứt đoạn giữa tuyển dụng, onboarding, vận hành
- dữ liệu nhân sự nằm rải rác ở email, sheet, chat, và nhiều công cụ khác
- phần mềm HR hiện có thường либо quá cứng, либо quá rời, либо không phù hợp bối cảnh Việt Nam

Vì vậy, câu chuyện của Vroom HR không nên bắt đầu bằng “chúng ta có bao nhiêu màn hình”, mà phải bắt đầu bằng:

**Vroom HR giúp company đi qua hành trình từ tuyển một người đến vận hành một employee trong cùng một mạch liên tục, có kiểm soát, có audit, có AI hỗ trợ, và có thể tự host.**

### Backbone story

Core story nên là:

**incoming email → AI classify → CV parse → Candidate → HR review → interview scheduling → accept → congratulations email → onboarding → Employee**

Đây không chỉ là luồng nghiệp vụ. Đây là **câu chuyện hình thành quan hệ giữa company và con người**.

Khi kể sản phẩm, phải kể theo câu chuyện này, không kể theo danh sách table hay endpoint.

## Tư duy sản phẩm cần có

### 1. Từ “quản trị HR” sang “quản trị journey của con người”

HR system truyền thống thường xoay quanh:

- quản lý danh sách
- approve
- payroll
- attendance
- report

Những thứ đó là thật, nhưng chưa đủ để tạo bản sắc.

Vroom HR cần tập trung vào journey:

- người mới đi vào hệ thống như thế nào
- HR nhìn thấy họ ra sao
- quyết định được đưa ra ở đâu
- lúc nào người đó trở thành Employee chính thức
- lúc nào họ bắt đầu dùng self-service

Nói cách khác, sản phẩm không chỉ quản lý nhân sự. Sản phẩm quản lý **hành trình vào tổ chức**.

### 2. Từ module-first sang context-first

Một feature chỉ có giá trị khi nó nằm trong ngữ cảnh.

Ví dụ:

- Candidate không chỉ là một record
- Candidate là một người đang được đánh giá trong một luồng tuyển dụng
- Onboarding không chỉ là checklist
- Onboarding là giai đoạn chuyển trạng thái từ “đã nhận” sang “đã sẵn sàng làm việc”
- Employee Assistant không chỉ là chatbot
- Nó là lớp hỗ trợ đọc context thật của employee

Nếu không giữ context-first, hệ thống sẽ thành một bộ CRUD có AI dán thêm bên ngoài.

### 3. Từ tool bán năng suất sang system tạo niềm tin

Với HR, yếu tố tin cậy quan trọng không kém tốc độ.

Người dùng cần cảm giác rằng:

- dữ liệu của họ không bị mất
- action nào cũng có audit
- AI không tự ý ghi bừa
- quyền truy cập rõ ràng
- hệ thống phản ánh đúng trạng thái thật

Điều này rất quan trọng nếu Vroom HR đi theo hướng open-source. Open-source không chỉ là “mã nguồn mở”, mà còn là “minh bạch đủ để người dùng tin” và “control đủ để company dám dùng”.

## Góc nhìn người dùng

### User chính là ai

Có 3 nhóm chính:

1. **HR / admin**
   - muốn tuyển nhanh, onboard rõ, review minh bạch, ít thao tác thừa
2. **Employee**
   - muốn tự xem, tự hiểu, tự hoàn tất các bước cần thiết
3. **Organization / owner**
   - muốn dữ liệu an toàn, tuân thủ, có thể tự host, và tránh vendor lock-in

### Mỗi nhóm cần gì

#### HR

- một nơi duy nhất để xem candidate lifecycle
- review queue rõ ràng
- scheduling không rối
- onboarding có kiểm soát
- audit đầy đủ
- AI hỗ trợ nhưng không thay quyền quyết định

#### Employee

- hiểu rõ mình đang ở trạng thái nào
- biết mình cần làm gì tiếp theo
- self-service đơn giản
- không bị kéo vào hệ thống phức tạp của HR

#### Organization / owner

- biết dữ liệu nằm ở đâu
- biết hệ thống có thể tự host
- biết AI và automation không vượt quyền
- biết sản phẩm có thể lớn dần mà không mất kiểm soát

## Tư duy thiết kế hệ thống

### 1. Hệ thống phải phản ánh domain, không ép domain theo UI

Mỗi entity, event, state transition phải có lý do business rõ.

Ví dụ:

- Candidate → Employee không phải đổi tên record
- Đó là một domain transition
- accepted không chỉ là status change
- Nó là mốc kích hoạt onboarding

Nếu hệ thống model sai, UI càng đẹp càng che giấu sự sai đó.

### 2. Mỗi module phải có ranh giới rõ

Vroom HR cần giữ ranh giới giữa:

- Identity / auth
- Recruitment
- Onboarding
- Employee
- ESS
- Attendance
- Payroll
- Assistant

Module không được chồng chéo vô tội vạ. Khi một user action đi qua nhiều module, cần nhìn thấy rõ ai sở hữu dữ liệu nào, ai ghi gì, ai chỉ đọc gì.

### 3. AI là lớp orchestration, không phải source of truth

AI chỉ nên:

- đọc context thật
- tóm tắt
- draft
- đề xuất

AI không nên trở thành nơi lưu trạng thái nghiệp vụ chính.

Source of truth vẫn phải là domain model + database + audit log.

### 4. Event và state transition phải có ý nghĩa sản phẩm

Mỗi event không chỉ để “cho có kiến trúc”.
Nó phải hỗ trợ câu chuyện người dùng:

- candidate accepted → onboarding bắt đầu
- onboarding complete → employee active
- attendance correction → audit
- request approved → data thay đổi có kiểm soát

### 5. Hệ thống phải mở rộng được mà không mất trục chính

Nếu tương lai thêm:

- performance review
- training
- internal mobility
- document workflows
- HR analytics

thì các phần đó phải bám vào backbone, không phá backbone.

## Tư duy trải nghiệm sản phẩm

### 1. Trải nghiệm phải bắt đầu từ “biết chuyện gì đang xảy ra”

Người dùng không muốn mở hệ thống rồi thấy rất nhiều form.
Họ muốn biết:

- hiện tại có candidate nào cần xử lý
- ai đang chờ interview
- ai đã accept
- onboarding nào đang dang dở
- employee nào cần thao tác tiếp

Tức là UI phải kể chuyện trạng thái, không chỉ hiển thị dữ liệu.

### 2. Mỗi màn hình phải trả lời một câu hỏi rõ

- Đây là ai?
- Người này đang ở trạng thái nào?
- Bước tiếp theo là gì?
- Ai chịu trách nhiệm?
- Hành động này có an toàn không?

Nếu một màn hình không trả lời được các câu hỏi này, nó đang quá rời khỏi user intent.

### 3. Giảm nhận thức phải dùng

Người dùng HR thường bị overload. Vì vậy:

- ưu tiên queue, timeline, status, next action
- giảm click thừa
- giảm form dài nếu có thể
- AI chỉ giúp chứ không làm phức tạp thêm

### 4. Self-service phải read-first, write có kiểm soát

Employee experience không nên copy HR admin experience.

ESS nên:

- đọc rõ trạng thái cá nhân
- đưa ra việc cần làm tiếp theo
- chỉ mở write flow khi đúng boundary

## Hướng đi cần thiết

### Giai đoạn 1: Chốt product narrative

Cần chốt một câu duy nhất để mọi người trong team có thể nói lại:

**Vroom HR là open-source HR platform cho company Việt Nam, giúp biến luồng recruit-to-onboard thành một hành trình rõ ràng, có AI hỗ trợ, có audit, có self-host, và có trải nghiệm đủ tin cậy để dùng thật.**

### Giai đoạn 2: Thiết kế theo story, không theo tính năng

Khi làm bất kỳ thứ gì, hỏi:

- nó nằm ở đoạn nào trong story?
- nó giúp ai?
- nó làm cho user hiểu gì rõ hơn?
- nó làm cho flow nào bớt đứt?

### Giai đoạn 3: Xây “one clear path” cho user

Nên có một đường đi rất rõ cho từng nhóm:

- HR path: inbox → candidate review → interview → accept → onboarding
- Employee path: access → self-service → tasks → active state
- Owner path: deploy → secure → control → trust

### Giai đoạn 4: Biến docs thành một phần của sản phẩm

Docs không nên là nơi ghi chú rời rạc.
Nó phải giúp human hiểu:

- vì sao sản phẩm sinh ra
- product direction là gì
- user journey là gì
- hệ thống được thiết kế ra sao

### Giai đoạn 5: Tạo sự thống nhất giữa kỹ thuật và sản phẩm

Backend model, frontend flow, AI boundary, and docs phải kể cùng một câu chuyện.
Nếu không thống nhất, sản phẩm sẽ nhìn như nhiều dự án ghép lại.

## Nguyên tắc ra quyết định từ nay

Mỗi quyết định mới nên được soi qua 5 câu hỏi:

1. Có phục vụ backbone không?
2. Có giúp user hiểu và làm việc tốt hơn không?
3. Có làm hệ thống rõ ràng hơn không?
4. Có làm mất control hay audit không?
5. Có mở đường cho story sản phẩm dài hạn không?

Nếu câu trả lời là không ở đa số câu, feature đó nên hoãn hoặc bỏ.

## Kết luận

Điểm cần thay đổi không phải là “thêm nhiều module hơn”.
Điểm cần thay đổi là **cách nghĩ về sản phẩm**.

Vroom HR cần trở thành một hệ thống có:

- backbone rõ
- user story rõ
- trust rõ
- AI boundary rõ
- đường phát triển rõ

Khi đó, sản phẩm không chỉ đáp ứng nhu cầu người dùng. Nó sẽ tạo được cảm giác rằng nó **được sinh ra đúng lúc, đúng vấn đề, đúng cách**.
