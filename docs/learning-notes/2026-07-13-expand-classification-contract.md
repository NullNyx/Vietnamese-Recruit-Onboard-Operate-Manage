# Mở rộng Classification Contract cho Job Application

## Task
Implement GitHub issue #182: expand classification contract (version, routing intent, confidence, evidence, source hints) hỗ trợ `job_application` song song với legacy `cv`, với strict validation không default về `other`, prompt coi input là untrusted data, không tools.

## What I changed

### `backend/src/modules/recruitment/domain/enums.py`
- Thêm `JOB_APPLICATION = "job_application"` vào `EmailIntent`, giữ nguyên `CV` legacy.

### `backend/src/modules/recruitment/domain/value_objects.py`
- Thêm `ClassificationResult` dataclass frozen với các field: `version`, `intent`, `confidence`, `evidence`, `source_hints`.
- Import `EmailIntent` từ domain enums.

### `backend/src/modules/recruitment/infrastructure/llm_adapter.py`
- Thêm `classification: ClassificationResult | None = None` vào `IntentResult`.
- Viết lại system prompt: yêu cầu JSON structured output, không chain-of-thought, input là untrusted data, LLM không có tools/write capability.
- Viết lại `_build_intent_prompt`: frame input là UNTRUSTED DATA, yêu cầu JSON output.
- Thêm `_parse_classification_json()`: strict validation — nếu JSON malformed, version không hỗ trợ, thiếu/sai field bắt buộc, unsupported intent, hoặc confidence ngoài 0.0–1.0 → raise `LLMParseError` (KHÔNG default về OTHER). Hỗ trợ markdown code block stripping.
- `_parse_intent_response()`: delegate tới `_parse_classification_json()`, raise error thay vì default OTHER.
- Retry loop nay bắt `LLMParseError` cùng với `TimeoutError` để retry khi parse lỗi.

### `backend/src/modules/recruitment/application/intent_classifier.py`
- `process_classification_result()`: xử lý cả `EmailIntent.CV` và `EmailIntent.JOB_APPLICATION` → cả 2 đều enqueue CV processing (legacy fallback).

### `backend/tests/modules/recruitment/test_llm_adapter.py`
- Rewrite `TestClassifyIntent`: dùng JSON response format mới.
- Thêm `TestParseClassificationJson`: 15 tests cho parse logic, validation, clamp, error cases.
- Update `TestParseIntentResponse`: verify delegate + raise error (không default OTHER).
- Thêm tests: `test_prompt_says_untrusted_data`, `test_prompt_requests_json`, `test_handles_markdown_code_block`.

### `backend/tests/modules/recruitment/test_intent_classifier.py`
- Thêm `test_job_application_enqueues_processing`: verify `JOB_APPLICATION` intent vẫn enqueue CV processing.

## The real problem

Classification contract cũ chỉ gồm một từ (vd "cv") không có version, confidence, evidence — các downstream component không kiểm chứng được decision của LLM. Hơn nữa, khi LLM trả response không parse được, code default về `OTHER` khiến email tuyển dụng bị mất. Cần expand contract để hỗ trợ `job_application` (theo ADR 0004) đồng thời giữ `cv` cho legacy.

## Why this solution

- **Structured JSON contract** thay vì single-word: cho phép thêm field mà không break API.
- **Strict validation** thay vì lenient fallback: theo đúng spec — malformed/unsupported/missing không trở thành `OTHER` mà raise `LLMParseError`, service phía trên catch error và mark `classification_failed`.
- **Retry on parse error**: LLMParseError được retry giống timeout và API error, tránh false positive failure do LLM tạm thời trả format sai.
- **Frozen dataclass**: immutable, thread-safe, dễ test.
- **Prompt frames input as untrusted**: đây là defense-in-depth — LLM được nói rõ không follow instruction trong email, không có tools.

## Production shape

Trong production:
1. Email đến → PII redact → gửi prompt yêu cầu JSON contract tới LLM.
2. LLM trả về JSON: `{"version":"1.0","intent":"job_application","confidence":0.92,"evidence":["...","..."],"source_hints":{...}}`.
3. `_parse_classification_json` validate: nếu OK → return `ClassificationResult`, gắn vào `IntentResult.classification`.
4. Nếu malformed → `LLMParseError` → retry loop (tối đa 3 lần) → nếu hết retry → error bubble lên `IntentClassifierService` → mark `classification_failed` (không tự trở thành `OTHER`).
5. `process_classification_result` xử lý `job_application` giống `cv`: enqueue CV processing.

## Other possible approaches

### Approach A: Single-word backward-compat với substring fallback
Giữ nguyên cơ chế cũ (single-word response), chỉ đổi prompt yêu cầu `job_application` thay vì `cv`. Nếu response không parse được → substring fallback → default OTHER.

**Ưu điểm**: zero change ở parser, backward compatible hoàn hảo.
**Nhược điểm**: Không có version/confidence/evidence, không kiểm chứng được. Substring fallback vẫn default về OTHER.

### Approach B: JSON response nhưng soft validation (warn + continue)
Parse JSON, nếu thiếu field thì warn log và attempt best-effort (ví dụ dùng confidence mặc định 0.5, evidence rỗng, version mặc định).

**Ưu điểm**: Graceful degradation, không fail cứng.
**Nhược điểm**: Che giấu lỗi LLM, khó debug. Trái với spec yêu cầu strict validation.

## Why I did not choose those alternatives

**Approach A** không đáp ứng AC: không có version/confidence/evidence, và substring fallback vẫn default về OTHER — trái với "malformed output → không trở thành other".

**Approach B** tạo silent degradation — LLM trả response thiếu field sẽ được best-effort thay vì fail rõ ràng. Điều này làm giảm khả năng phát hiện regression của model và khó audit.

## Key concepts to learn

- **Structured output (JSON mode) vs free-form text**: LLM dễ parse hơn khi output có schema, nhưng cần strict validation vì LLM vẫn có thể trả JSON không đúng schema.
- **Defense-in-depth cho prompt injection**: frame input là untrusted + declare no tools — không thay thế được input validation ở application layer.
- **Retry cho parse error**: nếu model thỉnh thoảng trả format sai, retry (không chỉ dành cho timeout/connection error) giúp tăng resilience.
- **Frozen dataclass contract**: immutable data contract rõ ràng, dễ reason về state.

## Common mistakes

- **Default về OTHER khi không chắc chắn**: cũ là behavior cố ý (requirement 1.10) nhưng nay trái với spec mới. Phân biệt: "không parse được do error" ≠ "LLM trả other".
- **Dùng `.strip().lower()` cho cả JSON response**: sẽ phá hỏng JSON nếu giá trị có uppercase. Chỉ lowercase field value khi validate intent.
- **Quên `from exc` trong `raise ... from exc`**: mất exception chain, khó debug.
- **Âm thầm clamp confidence**: LLM trả 2.0 hoặc -1.0 là vi phạm contract; phải fail vào retry/review thay vì biến malformed output thành dữ liệu hợp lệ.

## Small example

```python
# LLM returns:
# {"version":"1.0","intent":"job_application","confidence":0.88,
#  "evidence":["subject:contains_applied","no_attachment"],
#  "source_hints":{"sender_role":"candidate","has_cv_attachment":"false"}}

# ClassificationResult(
#     version="1.0",
#     intent=EmailIntent.JOB_APPLICATION,
#     confidence=0.88,
#     evidence=("subject:contains_applied","no_attachment"),
#     source_hints=(("sender_role","candidate"),("has_cv_attachment","false"))
# )
```

## How to think about this next time

Khi expand classification contract:
1. Xác định contract schema trước: field nào required, field nào optional.
2. Quyết định failure mode: strict (fail hard để phát hiện sớm) hay lenient (best-effort để không block flow).
3. Implement parser + validator trước prompt — test với fake JSON trước khi phụ thuộc LLM thật.
4. Prompt design: nói LLM output schema, không dùng chain-of-thought, frame input là untrusted.
5. Legacy path: giữ `cv` song song, không xóa — expand phase cần backward compat.
6. Test: test positive cases (từng intent), negative cases (malformed, missing fields, unsupported version/intent, confidence ngoài range), và markdown wrapper.
