# 04 — Runtime Resolution: Đọc Đúng Provider Từ Organization Config

## Mục tiêu
Xác minh runtime đọc provider từ Organization config, fallback về env khi chưa config.

## Mức độ ưu tiên
Medium

## Module liên quan
- `backend/src/modules/identity/` (OrganizationAIConfigService.get_runtime_config)
- `backend/src/modules/assistant/container.py`
- `backend/src/modules/assistant/infrastructure/llm_client.py`

## Các bước thực hiện

1. **Organization đã config**:
   - DB có `organization_ai_configurations` với capability="assistant"
   - Expected: Assistant dùng provider/model/key từ DB, KHÔNG dùng env

2. **Organization chưa config**:
   - DB không có record
   - Expected: fallback về `ASSISTANT_LLM_BASE_URL`, `ASSISTANT_LLM_MODEL`, `ASSISTANT_LLM_API_KEY`

3. **Capability disabled**:
   - DB có record nhưng capability bị disable
   - Expected: trả lỗi, không fallback im lặng

4. **Employee Assistant dùng cùng provider**:
   - Employee Assistant cũng resolve qua Organization config
   - Expected: dùng cùng provider/model, khác scope

5. **Provider response wrapped** (Cline):
   - Provider trả `{"data": {"choices": [...]}}`
   - Expected: parser unwrap đúng, lấy được choices

6. **Precedence contract**:
   - Cả env và DB đều có config
   - Expected: DB luôn thắng (Organization config là source of truth)

## Kết quả mong đợi
- DB > env về precedence
- Disabled → lỗi, không silent fallback
- Provider adapter xử lý response wrapper

## Test files
- `backend/tests/modules/assistant/test_organization_provider_resolution.py`
- `backend/tests/modules/assistant/test_llm_client_config.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
