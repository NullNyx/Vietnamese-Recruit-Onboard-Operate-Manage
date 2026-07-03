# Ánh xạ workflow -> skill

Áp dụng khi agent làm việc trong repo có harness.

## Luồng mặc định

| Phase | Agent action | Skill / command | Evidence |
|-------|-------------|------------------|----------|
| intake | Xác định loại task | `docs/FEATURE_INTAKE.md` | lane + type record |
| plan | Làm rõ scope | `/plan` nếu agent hỗ trợ | plan note |
| goal | Giữ objective xuyên phiên | `/goal` nếu agent hỗ trợ | goal text |
| implement | Code / config / docs | agent implement | changed files |
| gate | Scope check | `scripts/run-gate.sh` hoặc `scripts/check-scope.sh` | JSON + log output |
| notes | Ghi truth dễ stale | `scripts/record-note.sh` | active note |
| record | Ghi output chạy thật | `scripts/record-evidence.sh` | evidence log |
| review | Soát code cuối | code review tool / `/code-review` nếu có | review notes |

## Gợi ý skill theo profile

| Profile | Skills |
|---------|--------|
| backend | tdd, diagnose, code-review, implement |
| frontend | ui-ux-pro-max, frontend-testing-debugging, implement |
| full-stack | tdd, diagnose, ui-ux-pro-max, frontend-testing-debugging, implement, code-review |
| cli | tdd, diagnose, implement, code-review |

## Mô hình gate

### Agent gate

Agent gate nhẹ, chạy trong lúc implement.
Nó check scope và ghi evidence.

```bash
scripts/run-gate.sh --profile <profile> --allowlist <file>
```

### CI gate

CI gate là truth cuối.
Chạy lệnh project định nghĩa:

- lint
- typecheck
- test
- build

Nếu repo không khai báo một lệnh nào, harness không bịa ra.

## Nguyên tắc

1. Skill là optional cho task nhỏ.
2. Gate không optional khi sửa code thật.
3. Evidence là output, không phải claim.
4. CI gate thắng agent gate.

## Nguyên tắc note

Nếu task làm đổi project truth có thể stale, thêm hoặc update note rồi refresh `docs/notes/INDEX.md`.

## Tích hợp Matt Pocock

Danh sách skill đầy đủ + cách dùng + luồng feature:

→ `docs/matt-pocock-skills.md`

Các skill đó là agent construct (prompt), không phải shell script.
Harness chỉ wrapper: gate + evidence + note + profile.
Skill sống bên trong agent, không có file ở harness.
