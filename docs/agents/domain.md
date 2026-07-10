# Domain Docs

Cách engineering skills nên đọc tài liệu domain của repo khi lần theo codebase.

## Trước khi khám phá, đọc mấy file này

- **`CONTEXT.md`** ở root, hoặc
- **`CONTEXT-MAP.md`** ở root nếu có - nó trỏ tới một `CONTEXT.md` cho mỗi context. Đọc file nào liên quan tới topic đang làm.
- **`docs/adr/`** - đọc ADR chạm vào khu vực sắp làm. Với repo multi-context, kiểm tra thêm `src/<context>/docs/adr/` cho quyết định scope theo context.

Nếu file nào không tồn tại, **im lặng mà đi tiếp**. Đừng báo thiếu; đừng đề nghị tạo trước. Skill `/domain-modeling` (đi qua `/grill-with-docs` và `/improve-codebase-architecture`) sẽ tạo lazily khi thuật ngữ hoặc quyết định thật sự được chốt.

## Cấu trúc file

Repo single-context (đa số repo):

```text
/
├── CONTEXT.md
├── docs/adr/
│   ├── 0001-event-sourced-orders.md
│   └── 0002-postgres-for-write-model.md
└── src/
```

Repo multi-context (có `CONTEXT-MAP.md` ở root):

```text
/
├── CONTEXT-MAP.md
├── docs/adr/                          ← quyết định toàn hệ thống
└── src/
    ├── ordering/
    │   ├── CONTEXT.md
    │   └── docs/adr/                  ← quyết định theo context
    └── billing/
        ├── CONTEXT.md
        └── docs/adr/
```

## Dùng vocab của glossary

Khi output nhắc tới khái niệm domain, dùng đúng từ trong `CONTEXT.md` - trong issue title, đề xuất refactor, hypothesis, tên test, v.v. Đừng trôi sang synonym mà glossary đã loại.

Nếu khái niệm cần dùng chưa có trong glossary, đó là tín hiệu - hoặc bạn đang bịa ngôn ngữ repo không dùng (nên dừng lại), hoặc có gap thật (ghi lại cho `/domain-modeling`).

## Báo ADR xung đột

Nếu output mâu thuẫn với ADR hiện có, hãy nói thẳng thay vì âm thầm ghi đè:

> _Mâu thuẫn ADR-0007 (event-sourced orders) - nhưng đáng mở lại vì..._
