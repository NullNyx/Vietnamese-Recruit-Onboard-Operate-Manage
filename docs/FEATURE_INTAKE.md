# Tiếp nhận task

Phân loại task trước khi làm.

## Luồng

- `tiny` - sửa nhỏ, proof rõ, một lần verify
- `normal` - slice vừa, có thể cần nhiều file hoặc nhiều test
- `high-risk` - auth, data ownership, API shape, audit, validate, release

## Loại

- `new-spec`
- `spec-slice`
- `change-request`
- `maintenance`
- `harness-improvement`

## Nguyên tắc

Task vào lane nào thì chỉ làm trong lane đó. Nếu lane sai, dừng và chốt lại trước khi code.

## Profile dự án

Profile là lớp trên lane.
Lane quyết định mức rủi ro.
Profile quyết định loại work và workflow nào bật cho repo đang cài harness.
