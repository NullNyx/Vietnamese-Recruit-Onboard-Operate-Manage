# Note

Notes là lớp giữa `CONTEXT.md` và `state/`.

## Khi nào viết note

- Domain term chưa có trong `CONTEXT.md`
- Scope cũ so với file thật
- Dev-setup, CI, toolchain đổi
- Friction lặp lại hai lần
- Kết luận task trước mà task sau cần biết

## Format

```markdown
# <title>

**status:** active | superseded
**supersedes:** <file> (nếu thay note cũ)
**scope:** <module/area>
**last_reviewed:** YYYY-MM-DD

<nội dung>
```

## Vòng đời

- active note: `docs/notes/active/<topic>.md` + INDEX chỉ active
- hết hạn: move vào `archive/`, cập nhật INDEX
- không xóa note

## Đọc

1. `docs/notes/INDEX.md` → danh sách active
2. Đọc file trong `active/` có scope khớp task
3. Archive chỉ đọc khi cần tra lịch sử
4. INDEX rỗng = không có note

## Ghi

Dùng `scripts/record-note.sh` hoặc viết tay theo format trên.

## Nguyên tắc

Note không thay thế `CONTEXT.md`, decision record, hay `AGENTS.md`.
Note chỉ là temporary context cho scope/friction quyết định.
Khi note ổn định, đưa vào `CONTEXT.md` hoặc decision record.
