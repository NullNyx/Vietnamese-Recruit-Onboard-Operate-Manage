# Access Whitelist Bug Report

## Phát hiện

**BUG CONFIRMED**: Access Whitelist (WhitelistManager) và Domain Gate (DomainGateService) không được kết nối vào luồng login.

## Kết quả Playwright test

- `admin can add @gmail.com to whitelist via UI` ✅ **PASS**
- `whitelist check at login` ✅ **PASS** (confirm the bug exists)

Test thứ 2 gọi `POST /api/auth/login` với email `newuser@gmail.com`, kết quả:
- **Status:** 401
- **Error code:** `AUTH_INVALID_CREDENTIALS`
- **Message:** `"Email hoặc mật khẩu không đúng"`
- **Không có bất kỳ whitelist-related error code nào**

## Root Cause

Trong `backend/src/modules/identity/application/auth_service.py:116-130`:

```python
async def login(self, email: str, password: str) -> LocalAuthResult:
    user = await self._user_repository.get_by_email(email)
    if (user is None or not user.password_hash
        or not verify_password(password, user.password_hash)):
        raise InvalidCredentialsError()
    if not user.is_active:
        raise AccessDeniedError("Account is inactive")
    user.last_login = datetime.now(UTC)
    self._user_repository.session.add(user)
    await self._user_repository.session.flush()
    return await self._issue_session(user)
```

**Chỉ kiểm tra:**
1. User tồn tại + password đúng
2. User active

**Không kiểm tra:**
- `whitelist_manager.is_allowed_async(email)` — Access Whitelist
- `domain_gate_service.is_email_allowed(email)` — Email Domains

## Kiến trúc hiện tại

| Component | Backend class | Storage | Used at login? |
|---|---|---|---|
| **Access Whitelist** | `WhitelistManager` | DB + file | ❌ No |
| **Email Domains** | `DomainGateService` | OrgSettings | ❌ No |

Cả hai service đều có unit test riêng nhưng chưa ai gọi chúng trong `auth_service.login()`.

## Hướng fix

Thêm whitelist check vào `auth_service.login()`:

```python
async def login(
    self, email: str, password: str,
    whitelist_manager: WhitelistManager,
) -> LocalAuthResult:
    # Kiểm tra whitelist trước
    if not await whitelist_manager.is_allowed_async(email):
        raise AccessDeniedError("Email không có trong danh sách truy cập")

    # Phần còn lại giữ nguyên
    user = await self._user_repository.get_by_email(email)
    ...
```
