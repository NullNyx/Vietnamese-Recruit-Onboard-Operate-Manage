# Domain Docs

Cách skill engineering tiêu thụ domain docs khi khám phá codebase.

## Thứ tự nguồn

1. `CONTEXT.md` — từ điển thuật ngữ chuẩn.
2. `docs/design-docs/` — working docs được `grill-with-docs`, `to-prd`, `to-issues`, và các skill khác xem xét. Scope HR-only ở đây được ưu tiên hơn từ ngữ cũ về employee ở chỗ khác.
3. `docs/decisions/` — ADR cho các quyết định đã chốt và tradeoff thực sự.

Nếu thiếu file nào, cứ tiếp tục im lặng. Không tự chế tài liệu hay yêu cầu user tạo trước.

## Cấu trúc file

Repo single-context:

```
/
├── CONTEXT.md
├── docs/
│   ├── design-docs/
│   └── decisions/
└── backend/ , frontend/
```

Không có `CONTEXT-MAP.md` và không có file `CONTEXT.md` riêng theo context. Chỉ đọc `CONTEXT.md` gốc.

## Dùng từ vựng trong glossary

Khi output nhắc tới khái niệm domain, dùng term như định nghĩa trong `CONTEXT.md`. Tránh synonym bị cấm trong glossary.

Nếu khái niệm cần thiết chưa có trong glossary, coi là gap cho `/grill-with-docs`, không phải tìm synonym.

## Báo ADR xung đột

Nếu output mâu thuẫn với ADR, nêu rõ thay vì âm thầm ghi đè:

> _Mâu thuẫn với ADR-0005 (remove policy engine) — nhưng đáng xem xét lại vì…_

## Quy tắc working-doc

`docs/design-docs/` chỉ là không gian nháp. Chuyển quy tắc đã chốt vào `CONTEXT.md` hoặc `docs/decisions/` khi lựa chọn sản phẩm đã khóa. Không copy spec đầy đủ vào `docs/agents/`.
