# 03 — PII Redaction: Không Leak Dữ Liệu Nhạy Cảm

## Mục tiêu
Xác minh PII không bị leak vào log, audit table, hoặc LLM provider.

## Mức độ ưu tiên
High

## Module liên quan
- `backend/src/modules/recruitment/infrastructure/pii_redactor.py`
- `backend/src/modules/assistant/domain/tools.py` (provenance.redacted)
- `backend/src/modules/gmail/infrastructure/ai_classifier.py`
- `backend/src/modules/assistant/infrastructure/quality_models.py`

## Các bước thực hiện

1. **Email body chứa SĐT, CMND**:
   - Gửi email "Em tên A, SĐT 0912345678, CMND 123456789"
   - Expected: PII bị redact trước khi gửi lên LLM classifier

2. **CV chứa thông tin nhạy cảm**:
   - CV có địa chỉ nhà, tên người thân
   - Expected: parser vẫn parse nhưng audit không lưu raw text

3. **Assistant log không chứa PII**:
   - Log tool execution
   - Expected: log chỉ có tool_name, duration, success; không có candidate email/phone

4. **Audit table không chứa raw conversation**:
   - Kiểm tra `assistant_tool_call_events`, `assistant_feedback_events`
   - Expected: không có trường nào chứa raw conversation hoặc email body

5. **Provenance redacted**:
   - provenance có `"redacted": true`
   - Expected: không chứa dữ liệu thật của candidate ngoài UUID

6. **Telemetry không chứa raw prompt/email**:
   - `classification_telemetry` events
   - Expected: chỉ có metadata (tokens, cost, version), không có email body

## Kết quả mong đợi
- PII redacted trước khi rời khỏi backend
- Audit/telemetry chỉ chứa metadata
- Log không chứa dữ liệu cá nhân

## Test files
- `backend/tests/modules/recruitment/test_intent_classifier.py`
- `backend/tests/modules/assistant/test_hr_tool_safety.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
