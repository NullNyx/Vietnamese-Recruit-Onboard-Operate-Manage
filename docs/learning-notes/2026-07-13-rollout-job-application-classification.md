# Task

Triển khai issue #189: rollout an toàn classifier và business policy cho Job Application qua shadow, stable-partition canary, release gate, rollback và telemetry.

# What I changed

- Thêm deep boundary `ClassificationRollout` để quyết định classifier nào được phép ảnh hưởng workflow.
- Thêm policy Organization `recall_first` (Ưu tiên không bỏ sót); threshold nằm trong hệ thống, không lộ qua API/UI.
- Mở rộng Organization AI Configuration với stable/candidate classifier-policy version, rollout mode và canary percentage; mọi thay đổi/rollback dùng audit action riêng.
- Thêm API và UI cho shadow, canary, rollback; full rollout chỉ qua API có release report.
- Thêm release gates: recall ≥ 98%, `needs_classification` ≤ 15%, không recall regression, có báo cáo no-CV riêng và không có duplicate.
- Gắn rollout vào Gmail classification seam. Shadow chạy cả stable và candidate nhưng chỉ trả stable result cho Job Application/Recruitment Inbox workflow.
- Dùng SHA-256 của `gmail_message_id` modulo 100 để canary giữ cohort qua retry.
- Thêm bảng telemetry không chứa body/subject/attachment content, migration 066, runbook và operational checks.

# The real problem

Bài toán không chỉ là “chạy model mới”. Một model có recall tốt hơn vẫn có thể gây side effect production, thay cohort khi retry, làm tăng work item, tạo duplicate hoặc không thể quay lại policy cũ. Safety boundary phải nằm trước nơi kết quả classifier được persist thành Job Application hoặc Recruitment Inbox item. Nếu shadow chỉ được quy ước bằng log/convention, một refactor nhỏ có thể vô tình dùng candidate result cho workflow.

# Why this solution

`ClassificationRollout` trả đúng một production result và tự giữ candidate result trong telemetry. Vì caller chỉ nhận stable result ở shadow, việc “không side effect” là đặc tính cấu trúc thay vì lời hứa. Stable version vẫn được giữ trong Organization AI Configuration khi canary/full đang chạy, nên rollback chỉ đổi rollout state; nó không đụng vào work item đã tồn tại.

Business policy là enum domain, còn threshold được ánh xạ bên trong module. Điều này giữ UI theo ngôn ngữ HR và ngăn Organization tự nhập một con số có thể phá recall. Release gate là hàm thuần, tạo một quyết định machine-readable có thể test và dùng lại ở API.

# Production shape

1. HR cấu hình candidate classifier/policy version ở Organization AI Configuration.
2. Shadow chạy candidate trên production traffic và ghi telemetry, nhưng stable result tiếp tục điều khiển workflow.
3. Operator kiểm tra recall proxy, correction/review rate, latency, provider error, duplicates và cohort no-CV.
4. Canary chọn cohort deterministic theo Gmail message ID.
5. Full rollout yêu cầu release metrics và bị backend chặn nếu thiếu gate.
6. Khi guardrail hỏng, rollback xóa candidate state và dùng lại stable classifier/policy; Job Application và Recruitment Inbox không bị xóa.

# Other possible approaches

1. **Feature flag ngẫu nhiên ở worker:** mỗi lần xử lý gọi random để chọn model.
2. **Deploy hai worker pool riêng:** một pool stable, một pool candidate; load balancer phân traffic.
3. **Chỉ chạy offline evaluation:** model mới được so sánh trên frozen dataset rồi deploy thẳng 100%.

# Why I did not choose those alternatives

- Random trong worker làm cùng email đổi cohort qua retry, khiến so sánh và duplicate analysis không đáng tin. Cách này chỉ phù hợp khi mỗi request hoàn toàn stateless và không retry.
- Hai worker pool tạo isolation mạnh và phù hợp hệ thống traffic lớn/Kubernetes, nhưng deployment self-hosted một Organization sẽ phải vận hành thêm queue routing và hạ tầng. Deep boundary trong application nhỏ hơn và test trực tiếp được.
- Offline evaluation cần thiết nhưng không bắt được provider latency/error, traffic drift và workflow side effect production. Nó phù hợp làm gate trước shadow, không thể thay shadow/canary.

# Key concepts to learn

- **Shadow execution:** chạy candidate để quan sát nhưng không cho output điều khiển production state.
- **Stable partition:** hash immutable key để cohort không thay đổi qua retry.
- **Release gate:** điều kiện machine-readable chặn transition, không chỉ là checklist thủ công.
- **Rollback by retained state:** giữ stable version thay vì cố dựng lại từ audit sau sự cố.
- **Recall proxy:** nhãn correction/review production chỉ là proxy; vẫn cần frozen evaluation set.
- **Structural safety:** API trả production result duy nhất an toàn hơn việc yêu cầu caller “đừng dùng candidate”.

# Common mistakes

- Hash sender email thay vì Gmail message ID: một sender có thể gửi nhiều Job Application khác nhau.
- Cho shadow callback tạo Job Application rồi “xóa sau”: side effect đã xảy ra và audit/idempotency bị bẩn.
- Expose raw threshold để HR chỉnh trực tiếp.
- Tính metric trên mọi retry thay vì lấy event mới nhất của mỗi email.
- Full rollout chỉ nhìn aggregate, không có cohort no-CV riêng.
- Rollback bằng cách xóa Recruitment Inbox item hoặc Job Application đã tạo.
- Ghi subject/body/attachment content vào telemetry operational.

# Small example

```python
rollout = ClassificationRollout(
    RolloutConfig(
        mode=RolloutMode.SHADOW,
        business_policy=BusinessPolicy.RECALL_FIRST,
        policy_version="recall-first-v2",
        stable_classifier_version="classifier-v1",
        candidate_classifier_version="classifier-v2",
    ),
    record=telemetry.record,
)

# Candidate có thể dự đoán job_application, nhưng shadow vẫn trả stable_result.
production_result = await rollout.classify(
    gmail_message_id="18f...",
    stable=stable_classifier,
    candidate=candidate_classifier,
    has_cv=False,
)
```

# How to think about this next time

Bắt đầu từ câu hỏi: “Output nào được phép tạo durable state?” Đặt rollout boundary ngay trước seam đó, rồi thiết kế mode transition và rollback state trước khi viết telemetry/UI. Chọn partition key immutable theo work item, tách policy nghiệp vụ khỏi threshold kỹ thuật, và biến mọi release gate quan trọng thành code có test. Cuối cùng mới bổ sung dashboard/runbook để operator quan sát cùng một contract mà code đang thực thi.
