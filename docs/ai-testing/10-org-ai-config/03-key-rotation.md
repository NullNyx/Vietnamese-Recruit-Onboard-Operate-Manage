# 03 — Key Rotation Không Gây Gián Đoạn

## Mục tiêu
Xác minh khi HR đổi API key, hệ thống dùng key mới mà không cần restart.

## Mức độ ưu tiên
Medium

## Module liên quan
- `backend/src/modules/identity/` (OrganizationAIConfigService)
- `backend/src/modules/assistant/infrastructure/llm_client.py`
- `backend/src/modules/assistant/application/assistant_service.py`

## Các bước thực hiện

1. **Rotate API key**:
   - HR cập nhật API key mới trong Organization AI Settings
   - Expected: key mới được encrypt và lưu trong DB

2. **Assistant dùng key mới ngay**:
   - Sau khi rotate, gửi chat message
   - Expected: request tới LLM provider dùng key mới, không cần restart

3. **Health check với key mới**:
   - Test connection sau khi rotate
   - Expected: health check PASS với key mới

4. **Key cũ hết hạn**:
   - Key cũ bị revoke ở provider
   - Test connection → FAIL
   - HR rotate key mới → Test connection → PASS
   - Expected: hệ thống tiếp tục hoạt động sau rotate

5. **Key không persist khi test fail**:
   - Nhập key sai → Test connection FAIL
   - Expected: key sai không được lưu vào DB

6. **Credential source switch**:
   - Master key → Deployment key
   - Expected: đọc key từ deployment config thay vì DB

## Kết quả mong đợi
- Rotate key không cần restart
- Key được encrypt trong DB
- Test trước khi persist

## Test files
- `backend/tests/modules/assistant/test_organization_provider_resolution.py`
- `backend/tests/modules/identity/test_organization_ai_config_service.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
