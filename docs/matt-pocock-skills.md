# Matt Pocock Skills — Tích hợp

Hướng dẫn sử dụng các skill từ [Matt Pocock skills](https://github.com/mattpocock/skills).
Mỗi skill là một prompt có cấu trúc, trigger riêng, output riêng.

Nguồn: [github.com/mattpocock/skills](https://github.com/mattpocock/skills)

## Cách dùng

| Nếu muốn… | Dùng skill | Rồi làm gì tiếp |
|-----------|-----------|-----------------|
| Phản biện plan + cập nhật docs | `grill-with-docs` | → to-prd nếu cần spec |
| Chốt PRD từ conversation | `to-prd` | → to-issues nếu cần chia slice |
| Chia task thành issue | `to-issues` | → implement từng slice |
| Làm task từ spec | `implement` | kết thúc với code-review |
| Soát code cuối | `code-review` | chạy review, verify gate pass |
| Phân loại issue raw | `triage` | → implement hoặc ready-for-human |
| Debug bug cứng | `diagnose` | verify fix bằng test |
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
      verify: lint + typecheck + test
  → handoff nếu cần bàn giao
```

Không ép chạy hết các bước. Vào ở stage khớp với những gì user đã có.

## Context hygiene

- Mỗi skill mới = context mới. Không giữ context skill cũ.
- `handoff` là cách duy nhất để truyền context xuyên phiên.
- `docs/decisions/` giữ tradeoff đã chốt, skill sau không phải hỏi lại.

## Cài đặt lần đầu

Skill `setup-matt-pocock-skills` sinh các file cấu hình:

- `docs/agents/issue-tracker.md` — nơi issue sống
- `docs/agents/triage-labels.md` — 5 nhãn canonical
- `docs/agents/domain.md` — layout context

## Thiết kế

- Matt skills giữ prompt chuyên sâu cho từng phase.
- Bản đồ skill ở file này.
