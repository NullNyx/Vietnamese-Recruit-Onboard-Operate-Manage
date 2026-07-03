# Bộ khung

`just-harness` dùng lại được cho nhiều project và agent.

App là thứ user chạm. Harness là thứ agent chạm.

## Mô hình tư duy

```text
intent -> intake -> profile -> context -> implement -> agent gate -> CI gate -> record -> next task
```

Mỗi task có 2 output:

1. Product delta - code, docs, tests, config.
2. Harness delta - rule, template, proof, decision, friction record.

## Phạm vi v0

- phân loại task
- profile dự án
- chọn context
- độ tươi note
- agent gate
- CI gate
- xác minh bằng evidence
- lưu decision
- ghi friction

## Ngoài scope v0

- scheduler đầy đủ
- CLI có DB
- multi-agent orchestration
- pipeline sinh test

## Profile dự án

Chọn profile theo loại repo:

- backend
- frontend
- full-stack
- cli
- docs-only
- custom

Profile quyết định docs nào đọc trước, proof commands nào bắt buộc, và phase nào được bật.

## Trình chạy gate

`scripts/run-gate.sh` là lớp agent-gate mỏng.
Nó chạy scope + profile checks theo thứ tự và xuất JSON để đọc lại sau.

CI gate là truth cuối.
Agent không được tin lời mình nếu CI chưa pass.

## Notes

Notes giữ project truth đổi nhanh hơn decision.
Đọc `docs/notes/INDEX.md` trước, rồi đọc active notes khớp scope. Archive chỉ dùng khi truy lịch sử.

## Luật tăng trưởng

Nếu agent lặp lỗi, đoán quá nhiều, hoặc thiếu verify, sửa harness trước.
Nếu chưa sửa được, ghi friction để lên backlog.
