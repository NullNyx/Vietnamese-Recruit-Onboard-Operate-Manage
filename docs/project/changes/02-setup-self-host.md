# 02 — Setup Self-Host

## Mục tiêu

Thiết kế luồng setup lần đầu cho admin khi triển khai self-host, để khởi tạo
Organization, allow domain, whitelist email, và cấu hình Google OAuth trước
khi mở login bình thường.

## Foundation liên quan

- `docs/project/foundation/01-product-statement.md`
- `docs/project/foundation/02-target-user-personas.md`
- `docs/project/foundation/03-user-journey.md`
- `docs/project/foundation/08-deployment-trust-security-principles.md`
- `docs/project/foundation/10-open-source-strategy.md`
- `docs/project/changes/00-file-lifecycle.md`

## Trạng thái hiện tại

- Auth login đang dùng Google OAuth.
- Access control hiện phụ thuộc vào whitelist file trong backend config.
- Domain gate đã có trong backend, nhưng chưa có first-run setup flow cho admin.
- Chưa có UI để admin khởi tạo Organization settings từ app.

## Trạng thái mong muốn

- App detect trạng thái first boot, nếu hệ thống chưa init thì chuyển vào setup wizard.
- Admin có thể khai báo:
  - Organization name
  - timezone / locale mặc định
  - allowed email domain(s)
  - optional whitelist email(s)
  - initial admin email
  - Google OAuth client config
- Sau khi hoàn tất, hệ thống lưu cấu hình vào DB và khóa setup lại.
- Runtime auth chỉ đọc DB-backed config, file whitelist chỉ là fallback bootstrap.

## User journey đề xuất

1. **First boot**
   - Hệ thống detect DB chưa init hoặc setup chưa completed.
   - Redirect tới `/setup`.

2. **Welcome**
   - Giải thích rõ: one deployment = one company.
   - Setup chỉ làm một lần.

3. **Organization basics**
   - Nhập Organization name, timezone, locale.
   - Lưu draft theo từng bước.

4. **Access control**
   - Nhập allowed email domain(s).
   - Nhập whitelist email(s) cho ngoại lệ.
   - Chọn initial admin email.

5. **Identity provider**
   - Nhập Google OAuth client ID/secret và redirect URI.
   - Test kết nối ngay trong wizard.

6. **Review**
   - Hiển thị summary toàn bộ cấu hình.
   - Admin xác nhận hoàn tất.

7. **Lock setup**
   - Set `setup_completed = true`.
   - Ẩn `/setup` sau khi đã xong.
   - Chuyển sang `/login` hoặc dashboard.

## Các bước triển khai

1. Thêm trạng thái setup vào schema Organization settings.
2. Thiết kế setup wizard route và layout riêng.
3. Tạo màn hình nhập Organization basics + access control + OAuth config.
4. Thêm API lưu draft và complete setup.
5. Cập nhật auth flow để ưu tiên DB config, fallback file chỉ khi bootstrap.
6. Thêm kiểm tra redirect nếu hệ thống chưa setup.
7. Viết validation và error states cho domain/email/OAuth.

## Rủi ro / lưu ý

- Không biến setup thành config form dài, phải chia step rõ ràng.
- Cần bảo đảm chỉ có một luồng setup duy nhất, tránh re-run ngoài ý muốn.
- Nếu OAuth test fail, cho retry step hiện tại, không rollback toàn bộ.
- `whitelist.txt` chỉ nên là đường cứu hộ bootstrap, không phải source of truth lâu dài.
- Sau khi chuyển sang DB-backed config, phải cập nhật mọi cross-reference liên quan.
