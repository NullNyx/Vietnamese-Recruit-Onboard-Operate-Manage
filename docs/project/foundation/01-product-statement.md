# Product Statement

## Vroom HR là gì

Vroom HR là một **open-source HR platform** cho company Việt Nam, được thiết kế để biến luồng **recruit-to-onboard** thành một hành trình rõ ràng, có kiểm soát, có audit, có AI hỗ trợ, và có thể self-host.

## Vroom HR sinh ra để làm gì

Vroom HR sinh ra để giải quyết một vấn đề rất cụ thể:

- công ty có dữ liệu HR rải rác ở email, sheet, chat và nhiều công cụ khác
- quy trình tuyển dụng, onboarding, employee ops thường bị đứt đoạn
- hệ thống HR hiện có hoặc quá cứng, hoặc quá rời, hoặc không phù hợp bối cảnh Việt Nam
- HR cần một hệ thống vừa giúp làm việc nhanh, vừa giữ được niềm tin, kiểm soát và audit

## Một câu nói ngắn để nhớ

**Vroom HR giúp company đi từ một email tuyển dụng đến một Employee active trong cùng một mạch liên tục.**

## Backbone chính

Backbone của sản phẩm là:

**incoming email → AI classify → CV parse → Candidate → HR review → interview scheduling → accept → congratulations email → onboarding → Employee**

Đây là câu chuyện sản phẩm trung tâm. Mọi module khác chỉ có giá trị nếu nó phục vụ backbone này hoặc mở rộng tự nhiên từ nó.

## Sản phẩm không phải là gì

Vroom HR không phải:

- một bộ CRUD HRM rời rạc
- một chatbot AI chung chung
- một hệ thống multi-purpose phình to theo feature
- một sản phẩm chỉ để demo công nghệ

## Người dùng chính

### HR / admin

Cần review nhanh, scheduling rõ, onboarding có kiểm soát, audit đầy đủ, ít thao tác thừa.

### Employee

Cần hiểu mình đang ở trạng thái nào, cần làm gì tiếp theo, và có self-service đơn giản.

### Organization / owner

Cần dữ liệu an toàn, control tốt, compliance rõ, và khả năng self-host để tránh vendor lock-in.

## Giá trị cốt lõi

- **Clarity**: user luôn biết chuyện gì đang xảy ra
- **Control**: mỗi action có boundary rõ
- **Trust**: dữ liệu, audit, access, AI đều có giới hạn
- **Continuity**: flow không bị đứt giữa recruit, onboard, employee
- **Local fit**: phù hợp ngữ cảnh công ty Việt Nam

## Nguyên tắc sản phẩm

1. Backbone trước, feature sau.
2. Story-first, không feature-first.
3. Context-first, không CRUD-first.
4. AI chỉ hỗ trợ, không thay source of truth.
5. Open-source là kênh trust và adoption, không phải đích cuối.

## Tiêu chí chấp nhận một feature mới

Một feature mới chỉ nên vào roadmap nếu nó:

- phục vụ backbone
- làm user hiểu và làm việc tốt hơn
- tăng trust hoặc control
- giữ audit và boundary rõ
- mở rộng câu chuyện sản phẩm dài hạn
