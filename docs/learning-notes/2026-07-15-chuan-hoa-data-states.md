# Task
Chuẩn hóa data states và notification feedback theo issue #223.

# What I changed
- `DataTable` tách rõ loading, lỗi, empty data và empty filter.
- Empty filter có nút `Xóa bộ lọc`; lỗi có thông báo và `Thử lại`.
- Danh sách Employee nối retry thật qua React Query.
- Dashboard không còn hiển thị số 0 giả khi tải số liệu lỗi; có retry.
- Notification control bỏ unread badge giả và mở empty state quan sát được.

# The real problem
UI dùng mảng rỗng hoặc số 0 làm giá trị mặc định ở nhiều tình huống, khiến người dùng không biết hệ thống đang tải, lỗi, hay thực sự chưa có dữ liệu. Badge thông báo `3` cũng không có nguồn unread data thật.

# Why this solution
Đặt các quy tắc phổ biến ở `DataTable`, nơi nhiều danh sách dùng chung, và chỉ nối callback retry ở page sở hữu query. Notification dùng popover để click luôn có phản hồi mà không giả lập dữ liệu.

# Production shape
Khi API đang tải, bảng hiển thị skeleton. Khi lỗi, UI giữ thông báo lỗi và nút retry. Khi thành công nhưng không có bản ghi, UI nói rõ phạm vi dữ liệu. Khi có bộ lọc không khớp, UI cho phép xóa bộ lọc. Notification chỉ hiển thị badge khi sau này có unread count từ API thật.

# Other possible approaches
- Dùng một `AsyncState` component bao quanh mọi page; phù hợp khi toàn bộ màn hình được xây mới cùng một design system.
- Dùng React Query global error boundary/toast; phù hợp cho lỗi không cần hành động tại đúng vị trí, nhưng không tốt cho danh sách cần retry và ngữ cảnh empty.

# Why I did not choose those alternatives
Repo hiện có nhiều page legacy với state riêng; một global boundary sẽ cần refactor lớn và dễ làm mất ngữ cảnh. Toast toàn cục không thay thế được empty state trong bảng. Vì vậy thay đổi shared table và các điểm dashboard/header quan trọng trước.

# Key concepts to learn
Loading không đồng nghĩa empty; empty data khác empty filter; error state cần recovery action; badge phải phản ánh dữ liệu đã xác nhận.

# Common mistakes
Không dùng `data ?? []` để quyết định empty trước khi kiểm tra loading/error. Không hiển thị số unread cố định. Không biến lỗi API thành số liệu 0.

# Small example
`loading=true` → skeleton; `error` → “Lỗi tải dữ liệu” + “Thử lại”; `loading=false && data=[] && search="abc"` → empty filter + “Xóa bộ lọc”; `loading=false && data=[] && search=""` → empty data.

# How to think about this next time
Xác định state machine trước khi viết JSX: loading, error, empty-data, empty-filter, data. Mỗi state phải có copy và hành động phù hợp, rồi mới chọn component dùng chung.
