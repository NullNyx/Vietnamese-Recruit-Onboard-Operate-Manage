# 10 — Organization AI Configuration

Provider setup, health check, capability toggle, key rotation.

## Test case

| # | File | Mô tả | Ưu tiên |
|---|------|-------|---------|
| 01 | `01-provider-health-check.md` | Health check dùng /chat/completions | Medium |
| 02 | `02-capability-toggle.md` | Bật/tắt độc lập Automation và Assistant | Medium |
| 03 | `03-key-rotation.md` | Rotate API key không gián đoạn | Medium |
| 04 | `04-runtime-resolution.md` | Runtime đọc đúng provider từ Organization config | Medium |

## Code liên quan

- `backend/src/modules/identity/` (OrganizationAIConfigService)
- `backend/src/modules/assistant/application/assistant_service.py`
- `backend/src/modules/assistant/infrastructure/llm_client.py`
- `backend/tests/modules/assistant/test_organization_provider_resolution.py`
- `backend/tests/modules/assistant/test_llm_client_config.py`
- `backend/tests/modules/identity/test_organization_ai_config_service.py`
- `backend/tests/modules/identity/test_organization_ai_config_routes.py`
