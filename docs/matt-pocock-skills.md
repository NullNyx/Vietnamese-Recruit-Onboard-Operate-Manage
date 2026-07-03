# Matt Pocock Skills — Tích hợp

Đây là lớp kỹ năng (skill) bên trên workflow harness.
Mỗi skill là một prompt có cấu trúc, trigger riêng, output riêng.
Harness không thay thế skill; harness là lớp vận hành (gate + note + evidence)
chạy bao ngoài skill.

Nguồn: [github.com/mattpocock/skills](https://github.com/mattpocock/skills)

## Cách dùng

| Nếu muốn… | Dùng skill | Rồi làm gì tiếp |
|-----------|-----------|-----------------|
| Phản biện plan + cập nhật docs | `grill-with-docs` | → to-prd nếu cần spec |
| Chốt PRD từ conversation | `to-prd` | → to-issues nếu cần chia slice |
| Chia task thành issue | `to-issues` | → implement từng slice |
| Làm task từ spec | `implement` | kết thúc với code-review |
| Soát code cuối | `code-review` | gate harness + evidence |
| Phân loại issue raw | `triage` | → implement hoặc ready-for-human |
| Debug bug cứng | `diagnose` | gate harness sau fix |
| Làm test-first | `tdd` | implement theo đỏ-xanh |
| Xem tổng quan code | `zoom-out` | → srcwalk hoặc codegraph |
| Bàn giao context | `handoff` | trước khi kết thúc phiên |
| Tìm skill phù hợp | `ask-matt` | router, hỏi trước khi làm |

## Luồng đầy đủ (feature mới)

```
intent
  → ask-matt (nếu chưa rõ skill nào)
  → grill-with-docs (phản biện + cập nhật docs)
  → to-prd (chốt spec)
  → to-issues (chia slice)
  → [vòng lặp cho từng slice]
      implement (chạy tdd nội bộ, kết thúc code-review)
      gate harness (run-gate.sh + check-scope.sh)
      record-evidence
      notes nếu truth stale
  → handoff nếu cần bàn giao
```

Không ép chạy hết các bước. Vào ở stage khớp với những gì user đã có.

## Context hygiene

- Mỗi skill mới = context mới. Không giữ context skill cũ.
- `handoff` là cách duy nhất để truyền context xuyên phiên.
- `docs/notes/` giữ truth tạm cho skill sau đọc lại.
- `docs/decisions/` giữ tradeoff đã chốt, skill sau không phải hỏi lại.

## Cài đặt lần đầu

Khi dùng harness trong repo mới, chạy `setup-matt-pocock-skills` trước.

Skill này sinh:

- `docs/agents/issue-tracker.md` — nơi issue sống
- `docs/agents/triage-labels.md` — 5 nhãn canonical
- `docs/agents/domain.md` — layout context

Harness chỉ wrapper: không sửa file đó, không ghi đè.

## Thiết kế

- Harness giữ gate + evidence + note + profile.
- Matt skills giữ prompt chuyên sâu cho từng phase.
- Không nhồi skill vào harness script; skill là agent construct, không phải shell script.
- Bản đồ skill ở file này; `workflow-skills.md` là surface ngắn.
