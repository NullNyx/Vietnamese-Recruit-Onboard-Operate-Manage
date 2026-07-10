# Thiết lập lần đầu nguyên tử

Thiết lập lần đầu xác lập Organization và tạo tài khoản HR đầu tiên trong cùng một thao tác bootstrap nguyên tử. Chọn cách này thay vì tách thành nhiều request từ frontend để setup bị lỗi hoặc gián đoạn không thể để lại deployment có Organization nhưng không có tài khoản HR khả dụng (hoặc ngược lại); UI có thể trình bày thành wizard hai bước, nhưng request cuối cùng ở backend vẫn là một transaction.

## Trạng thái

accepted

## Các phương án đã cân nhắc

- Tách request tạo Organization và tài khoản: loại bỏ vì việc hoàn tất một phần tạo ra trạng thái khôi phục không rõ ràng.
- Chỉ tạo tài khoản rồi cấu hình Organization sau: loại bỏ vì deployment sẽ có thể sử dụng mà chưa có danh tính Organization rõ ràng.

## Hệ quả

Endpoint setup phải nhận danh tính tối thiểu của Organization cùng thông tin xác thực của tài khoản HR, validate ở server và chỉ trả về authenticated session sau khi cả hai record đã commit thành công.
