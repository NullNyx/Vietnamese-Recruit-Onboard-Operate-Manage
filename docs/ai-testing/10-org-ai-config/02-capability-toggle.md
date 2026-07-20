# 02 — Capability Toggle: Bật/Tắt AI Automation & Assistant

## Mục tiêu
Xác minh có thể bật/tắt độc lập AI Automation và AI Assistant.

## Mức độ ưu tiên
Medium

## Module liên quan
- `backend/src/modules/identity/` (OrganizationAIConfigService)
- Alembic migration 058 (ai_consent_and_toggles)
- `backend/src/modules/assistant/application/assistant_service.py`

## Các bước thực hiện

1. **Enable AI Automation**:
   - HR bật AI Automation capability
   - Expected: email classification chạy, CV parsing chạy

2. **Disable AI Automation**:
   - HR tắt AI Automation
   - Expected: classification/pipeline dừng, email mới không được classify

3. **Enable AI Assistant**:
   - HR bật AI Assistant capability
   - Expected: Assistant chat hoạt động

4. **Disable AI Assistant**:
   - HR tắt AI Assistant
   - Expected: Assistant trả về lỗi config, chat không khả dụng

5. **Độc lập**:
   - Tắt Automation, bật Assistant
   - Expected: Assistant vẫn hoạt động, Automation dừng
   - Bật Automation, tắt Assistant
   - Expected: Automation chạy, Assistant không hoạt động

6. **Disable không xóa pending items**:
   - Đang có email pending_classification → disable Automation
   - Expected: pending items giữ nguyên trạng thái

## Kết quả mong đợi
- 2 capabilities độc lập
- Disable → không xóa dữ liệu
- Có error message rõ ràng khi capability bị disable

## Test files
- `backend/tests/modules/identity/test_organization_ai_config_service.py`
- `backend/tests/modules/identity/test_organization_ai_config_routes.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
