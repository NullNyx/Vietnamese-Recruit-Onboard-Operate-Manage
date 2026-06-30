# Hướng dẫn sử dụng Open Code Review (OCR)

Open Code Review (OCR) là một công cụ Code Review CLI hoạt động dựa trên cơ chế lai (Hybrid Architecture) kết hợp giữa:

1. **Deterministic Logic**: Định vị chính xác các dòng code thay đổi (diff) trong Git và quản lý tệp tin.
2. **LLM Agents**: Sử dụng Trí tuệ Nhân tạo để phân tích, phát hiện lỗi logic, bảo mật (như SQL Injection, XSS, Thread-safety, Null Pointer Exception) và gợi ý cải tiến code.

---

## 1. Cấu hình kết nối LLM (LLM Configuration)

Trước khi chạy review, OCR cần kết nối tới một mô hình ngôn ngữ lớn (như OpenAI, Claude, hoặc mô hình Custom).

### Sử dụng lệnh `ocr config set`

Bạn sử dụng cấu hình này để lưu vĩnh viễn vào máy:

```bash
# Cấu hình API Endpoint (Nếu dùng custom, nhớ thêm hậu tố /chat/completions)
ocr config set llm.url http://127.0.0.1:20128/v1/chat/completions

# Cấu hình API Key (Token)
ocr config set llm.auth_token your_api_key_here

# Cấu hình tên Model sử dụng
ocr config set llm.model your_model_name

# Tắt chế độ Anthropic (sử dụng chuẩn OpenAI)
ocr config set llm.use_anthropic false

# Thiết lập ngôn ngữ phản hồi (mặc định English, bạn có thể chuyển thành Vietnamese nếu muốn)
ocr config set language English
```

### Sử dụng biến môi trường (Environment Variables)

Hữu ích khi bạn tích hợp OCR vào hệ thống CI/CD (GitHub Actions, GitLab CI...):

- `OCR_LLM_URL`
- `OCR_LLM_TOKEN`
- `OCR_LLM_MODEL`
- `OCR_USE_ANTHROPIC`

### Vị trí lưu File cấu hình

Cấu hình của bạn sẽ được lưu tại:

- **Global**: `config.json`

---

## 2. Kiểm tra kết nối LLM

Để đảm bảo thông số cấu hình đã chính xác, bạn chạy lệnh:

```bash
ocr llm test
```

Nếu thành công, CLI sẽ hiển thị lời chào từ Alibaba Open Code Review cùng thông tin Endpoint và Model đang kết nối.

---

## 3. Các lệnh Review Code (Review Commands)

OCR hỗ trợ review theo nhiều phạm vi khác nhau trong Git repo:

### A. Review các thay đổi hiện tại (Staged + Unstaged + Untracked)

Lệnh cơ bản nhất, dùng khi bạn đang code local và muốn review trước khi commit:

```bash
ocr review
# hoặc viết tắt
ocr r
```

### B. Review sự khác biệt giữa hai nhánh / commits

Rất hữu ích trước khi tạo Pull Request:

```bash
ocr review --from master --to feature-branch
```

### C. Review một Commit cụ thể

```bash
ocr review --commit <commit_hash>
# hoặc viết tắt
ocr review -c abc1234
```

### D. Thêm ngữ cảnh nghiệp vụ (Business Context)

Để AI không chỉ kiểm tra cú pháp mà còn hiểu đúng logic nghiệp vụ của bạn:

```bash
ocr review -b "Nhánh này nâng cấp cổng thanh toán lên v2, yêu cầu bảo mật cao cho token"
```

### E. Xem trước danh sách file sẽ được review (Không tốn token LLM)

```bash
ocr review --preview
```

---

## 4. Quản lý Luật Review riêng (Custom Rules)

OCR đi kèm với bộ luật mặc định cực tốt. Tuy nhiên, bạn hoàn toàn có thể tự viết các quy định kiểm tra code phù hợp với dự án (ví dụ: quy chuẩn đặt tên, thư viện cấm dùng, cấu trúc bắt buộc).

### Định dạng File `rule.json`

Tạo một file JSON có cấu trúc như sau:

```json
{
  "rules": [
    {
      "path": "src/api/**/*.java",
      "rule": "Tất cả các API mới phải kiểm tra quyền truy cập (Permission Check) và bắt buộc validate đầu vào."
    },
    {
      "path": "**/*mapper*.xml",
      "rule": "Kiểm tra rủi ro SQL Injection, không được sử dụng nối chuỗi trực tiếp mà phải dùng tham số."
    }
  ]
}
```

### Cách áp dụng Rule

1. **Chỉ định trực tiếp qua CLI**:

   ```bash
   ocr review --rule /path/to/my-rule.json
   ```

2. **Cấu hình dự án (Project level)**: Lưu file quy tắc tại `.opencodereview/rule.json` ngay trong thư mục gốc của Git dự án. Khi bạn gõ `ocr review`, file này tự động được áp dụng và bạn có thể push nó lên Git để cả nhóm dùng chung.

### Kiểm tra Rule nào sẽ áp dụng cho File

Bạn có thể kiểm tra xem một file bất kỳ trong dự án sẽ bị áp dụng luật nào bằng lệnh:

```bash
ocr rules check src/api/UserController.java
```

---

## 5. Trình xem Lịch sử WebUI (Session Viewer)

Một tính năng rất mạnh mẽ của OCR là khả năng hiển thị các nhận xét review dưới dạng giao diện Web trực quan thay vì chỉ đọc text thô trên Terminal.

Để khởi động WebUI, chạy lệnh:

```bash
ocr viewer
```

- Mặc định WebUI sẽ mở tại địa chỉ: `http://localhost:5483`
- Bạn có thể thay đổi cổng nếu muốn: `ocr viewer --addr :3000`

Tại đây, bạn sẽ thấy toàn bộ lịch sử các phiên review trước đó, các file đã review kèm theo dòng code được bôi đỏ/xanh lá kèm nhận xét chi tiết của AI cực kỳ trực quan.
