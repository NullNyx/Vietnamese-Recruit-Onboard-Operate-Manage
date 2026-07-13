# Capture safe classification evaluation feedback

## Task

Implement Issue #187: biến correction của HR thành evaluation feedback an toàn, không thành online learning. Mặc định chỉ giữ prediction, correction, versions và metadata tối thiểu; HR có thể chủ động chọn một mẫu, redaction rồi lưu vào evaluation set.

## What I changed

- **New entity** `CorrectionRecord` — lưu prediction, quyết định HR, model/prompt/policy version, metadata tối thiểu và timestamps. Raw body, thread content, attachment content và chain-of-thought không có field nào trong entity này.
- **New entity** `EvaluationSet` — versioned evaluation set (semver, description).
- **New entity** `EvaluationSample` — redacted sample đã commit vào evaluation set, chỉ chứa redacted data.
- **New enum** `CorrectionEvaluationStatus` — none → selected → redacted → committed.
- **New migration** `064` — tạo 3 bảng `correction_records`, `evaluation_sets`, `evaluation_samples`.
- **New repositories** — `CorrectionRecordRepository`, `EvaluationSetRepository`, `EvaluationSampleRepository`.
- **New service** `CorrectionEvaluationService` — record_correction, select_for_evaluation, commit_to_evaluation_set, create_evaluation_set.
- **Extended inbox_router** — correct-intent endpoint tự động ghi CorrectionRecord; thêm endpoints cho list corrections và select-for-evaluation.
- **New router** `evaluation_router` — CRUD cho evaluation sets và commit samples.
- **Redaction utility** `_redact_email_field` — redact email và phone trong subject/snippet.
- **Tests** 19 privacy contract tests + service tests + journey tests.

## The real problem

Corrections và evaluation feedback cần được tách biệt khỏi online learning để đảm bảo privacy và safety. Nếu mọi correction đều tự động feed vào model training, thì:
1. Dữ liệu nhạy cảm (email body, thread content, PII) sẽ bị lưu bền vĩnh viễn.
2. HR không kiểm soát được sample nào đi vào evaluation set.
3. Không có versioning cho evaluation data, không reproducible.

## Why this solution

- **Structural enforcement** — entity `CorrectionRecord` không có field cho raw body/COT, nên không thể lưu chúng dù có bug.
- **Opt-in flow** — HR phải chủ động chọn từng sample (select_for_evaluation), không có bulk opt-in.
- **Redaction trước commit** — chỉ data đã redacted được ghi vào evaluation set.
- **No online learning** — field `triggers_online_learning` mặc định False, documentation field confirm design principle.
- **Versioned evaluation sets** — dùng semver để so sánh classifier qua các phiên bản.

## Production shape

- `correction_records` table — mỗi lần HR correct intent, ghi 1 record với safe metadata.
- `evaluation_sets` table — được tạo khi release classifier mới.
- `evaluation_samples` table — chứa redacted samples đã commit vào evaluation set.
- API endpoints nằm dưới `/api/recruitment/inbox/{id}/...` và `/api/recruitment/evaluation/...`.
- Các endpoint evaluation yêu cầu HR role.

## Other possible approaches

1. **Tiếp tục dùng JSONB correction_history trên inbox item** — không tạo entities riêng.
   - Ưu: zero migration, minimal code change.
   - Nhược: không có version fields riêng, không evaluation lifecycle, không evaluation set.

2. **Auto collect tất cả corrections vào evaluation set** — không cần opt-in.
   - Ưu: HR không cần làm gì, evaluation set tự đầy.
   - Nhược: không có privacy gate, PII leak, HR không kiểm soát data nào đi vào training.

3. **Dùng file system / MinIO cho evaluation data** — không dùng DB.
   - Ưu: evaluation set portable, có thể export trực tiếp.
   - Nhược: mất referential integrity, khó query, khó migrate.

## Why I did not choose those alternatives

1. JSONB correction_history — thiếu versioning và lifecycle, không scale được cho evaluation.
2. Auto collect — vi phạm privacy contract, HR không kiểm soát.
3. File system — phức tạp hơn DB-first approach, evaluation data vốn nhỏ.

## Key concepts to learn

- **Privacy contract test** — structural test chứng minh entity không có field cho sensitive data.
- **Safe evaluation feedback** — correction chỉ dùng để evaluate, không bao giờ để train.
- **PII redaction pipeline** — email/phone được redact trước khi vào evaluation set.
- **Semantic versioning cho evaluation set** — mỗi release có evaluation set riêng.

## Common mistakes

- Lưu raw body/COT vì "đề phòng" — cần structural enforcement (entity không có field).
- Quên redact trước khi commit vào evaluation set.
- Cho phép bulk select thay vì từng sample.
- Không version evaluation set, mất reproducibility.

## Small example

```python
# HR corrects intent → auto records safe correction
await eval_service.record_correction(
    source_type="inbox_item",
    source_id=item_id,
    prediction_intent="job_application",
    corrected_intent="other",
    corrected_by_user_id=user_id,
    evidence=[{"signal": "subject:ung tuyen"}],
)

# HR opts in → marks as selected (with redacted content)
await eval_service.select_for_evaluation(
    correction_record_id=record_id,
    redacted_subject="Ung tuyen [REDACTED]",
    redacted_snippet="Toi muon ung tuyen [REDACTED]",
)

# HR commits to versioned evaluation set
await eval_service.commit_to_evaluation_set(
    correction_record_id=record_id,
    evaluation_set_id=set_id,
)
```

## How to think about this next time

Khi thiết kế correction/evaluation flow, luôn bắt đầu từ privacy contract:
1. Xác định data nào được phép lưu (prediction, correction, versions) — không bao giờ raw content.
2. Thiết kế entity structural — không có field = không thể lưu.
3. Opt-in flow cho evaluation — HR kiểm soát từng sample.
4. Redaction trước khi durable storage.
5. Versioned evaluation sets cho reproducible metrics.
