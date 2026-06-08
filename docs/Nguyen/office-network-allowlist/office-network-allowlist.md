# Office Network Allowlist — Quy cách kỹ thuật

## Tổng quan

Thêm cấu hình mạng văn phòng cấp Organization cho Attendance Records theo ADR-0010.

HR/admin có thể cấu hình các dải IP/CIDR được phép sử dụng khi nhân viên check-in/check-out. Backend xác thực định dạng CIDR/IP và expose cấu hình an toàn.

## Phạm vi

**Trong phạm vi:**
- Organization settings lưu trữ danh sách IP/CIDR được phép cho attendance
- Thao tác CRUD của HR/admin cho allowlist
- Xác thực CIDR/IP (chỉ IPv4 cho phiên bản MVP)
- Cấu hình sẵn sàng cho service check-in/check-out của Attendance
- Kiểm soát truy cập chỉ dành cho admin
- Ghi audit log khi thay đổi cấu hình

**Ngoài phạm vi (theo ADR-0010):**
- GPS, theo dõi thiết bị di động, sinh trắc học
- Lập lịch ca, logic policy-engine
- IPv6 (xem xét sau)
- Employee tự xem allowlist

## Mô hình dữ liệu

### Mở rộng OrganizationSettings

Thêm trường vào entity `OrganizationSettings` hiện có:

```python
class OrganizationSettings(SQLModel, table=True):
    # ... các trường hiện có ...
    attendance_allowed_networks: list[str] = Field(
        default_factory=list,
        sa_column=Column(ARRAY(String), nullable=False),
    )
```

**Ràng buộc:** Tối đa 20 dải CIDR mỗi organization.

## Thiết kế API

### Endpoints (prefix: `/api/attendance/`)

| Method | Path | Mô tả | Truy cập |
|--------|------|-------|----------|
| GET | `/settings/network` | Lấy danh sách allowlist hiện tại | HR+ |
| PUT | `/settings/network` | Thay thế toàn bộ allowlist | HR only |
| POST | `/settings/network/add` | Thêm CIDR vào allowlist | HR only |
| DELETE | `/settings/network/{cidr}` | Xóa một CIDR khỏi allowlist | HR only |

### Request/Response Schemas

```python
# GET /api/attendance/settings/network
class NetworkAllowlistResponse(BaseModel):
    networks: list[str]  # Danh sách ký hiệu CIDR
    updated_at: datetime | None

# PUT /api/attendance/settings/network
class NetworkAllowlistUpdate(BaseModel):
    networks: list[str]  # Thay thế toàn bộ danh sách
```

### Quy tắc xác thực

- Định dạng CIDR: `X.X.X.X/N` với X ∈ [0-255], N ∈ [0-32]
- IP đơn lẻ: `X.X.X.X/32` (được xử lý như CIDR /32)
- Tối đa 20 entries
- Không trùng lặp
- Danh sách rỗng = cho phép tất cả (validation pass nhưng service ghi log cảnh báo)

### Error Responses

| Code | Điều kiện |
|------|-----------|
| 400 | Định dạng CIDR không hợp lệ |
| 400 | Quá nhiều entries (>20) |
| 400 | Entry trùng lặp |
| 403 | User không phải admin thực hiện write |
| 404 | Settings row chưa được khởi tạo |

## Service Layer

### AttendanceSettingsService

```python
class AttendanceSettingsService:
    async def get_allowed_networks() -> list[str]
    async def set_allowed_networks(networks: list[str]) -> list[str]
    async def add_networks(networks: list[str]) -> list[str]
    async def remove_network(cidr: str) -> list[str]
    async def is_ip_allowed(ip: str) -> bool  # Cho validation check-in
```

### Logic xác thực IP

```python
def _ip_in_cidr(ip: str, cidr: str) -> bool:
    """Kiểm tra IP có nằm trong dải CIDR không."""
    import ipaddress
    return ipaddress.ip_address(ip) in ipaddress.ip_network(cidr, strict=False)
```

## Frontend

### Trang Organization Settings

Vị trí: `/app/(dashboard)/settings/organization/page.tsx`

Components:
- `OfficeNetworkManager` — component chính
- `NetworkCidrInput` — input với phản hồi xác thực
- `NetworkList` — hiển thị allowlist hiện tại với nút xóa

## Điều kiện chấp nhận

- [ ] HR/admin có thể lưu một hoặc nhiều dải IP/CIDR được phép
- [ ] Employee không phải admin không thể cập nhật cấu hình mạng attendance của Organization
- [ ] Giá trị CIDR/IP không hợp lệ bị từ chối với thông báo lỗi xác thực rõ ràng
- [ ] Cấu hình sẵn sàng cho service check-in/check-out của Attendance
- [ ] Tests cover admin-only access và validation

## Các bước triển khai

1. **Domain**: Thêm `attendance_allowed_networks` vào entity `OrganizationSettings`
2. **Repository**: Mở rộng `OrganizationSettingsRepository` với các method network
3. **Service**: Tạo `AttendanceSettingsService` với xác thực
4. **API**: Thêm router với các endpoint được bảo vệ bởi HR role
5. **Audit**: Log tất cả thay đổi cấu hình network
6. **Frontend**: Thêm UI components trong Organization Settings
7. **Tests**: Unit tests cho validation, integration cho API auth
