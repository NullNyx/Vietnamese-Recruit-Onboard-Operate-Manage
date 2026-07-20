# 01 — Provider Health Check Dùng /chat/completions

## Mục tiêu
Xác minh health check hoạt động với provider không hỗ trợ `/models` endpoint.

## Mức độ ưu tiên
Medium

## Module liên quan
- `backend/src/modules/identity/` (OrganizationAIConfigService health check)
- `backend/src/modules/assistant/infrastructure/llm_client.py`

## Các bước thực hiện

1. **Provider có /models**: OpenAI standard
   - Expected: health check pass (qua /chat/completions)

2. **Provider không có /models**: Cline, DeepSeek
   - Expected: health check vẫn PASS (dùng /chat/completions, không cần /models)

3. **Provider sai Base URL**:
   - URL = "https://wrong-url.com"
   - Expected: health check FAIL với error connection

4. **Provider sai API Key**:
   - API Key = "invalid-key"
   - Expected: health check FAIL với error 401/403

5. **Provider sai Model**:
   - Model = "non-existent-model"
   - Expected: health check FAIL với error model not found

6. **Health check request tối thiểu**:
   - Prompt cố định: "Reply with OK."
   - `max_tokens` = 4
   - Timeout = 30s
   - Expected: không chứa dữ liệu Organization

7. **Deployment key path**:
   - Switch credential source → Deployment key
   - Expected: cũng dùng /chat/completions để test

## Kết quả mong đợi
- Tất cả provider OpenAI-compatible đều test được
- Health check dùng đúng production contract
- Không false negative vì `/models` không tồn tại

## Test files
- `backend/tests/modules/identity/test_organization_ai_config_service.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
