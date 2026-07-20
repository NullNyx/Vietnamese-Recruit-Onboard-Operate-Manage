# 06 — Onboarding

> **Nhóm:** Onboarding | **Tổng:** 3 chức năng | **Deployed:** 3 | **Pending Review:** 3
> **Backend module:** `backend/src/modules/onboarding/`
> **Frontend:** `(dashboard)/onboarding/`

---

## Danh sách chức năng

| ID | Chức năng | Mô tả ngắn | Backend Route | Frontend Page | Status | Review |
|----|-----------|------------|---------------|---------------|--------|--------|
| ON-01 | Kích hoạt từ Candidate Accepted | Event `candidate_accepted` → ARQ consumer; retry ≤3 | Recruitment publisher, `onboarding/worker.py` | — | ✅ Deployed | ⬜ |
| ON-02 | Tạo Process Nguyên Tử | Idempotent: Employee inactive + OnboardingProcess + checklist (4 task cố định) | Onboarding service/repository | — | ✅ Deployed | ⬜ |
| ON-03 | Checklist & Activation | HR cập nhật task; task cuối → process complete + `Employee.is_active = true` | `/api/onboarding/*` | `/onboarding` | ✅ Deployed | ⬜ |

---

## Tiêu chí Review

- [ ] Router đã wired trong `backend/src/main.py`
- [ ] ARQ worker: validate payload, retry ≤3
- [ ] Idempotent: `start_from_event` theo candidate
- [ ] Transaction nguyên tử: Employee inactive + process + checklist
- [ ] Activation: task cuối → employee active trong cùng transaction
- [ ] Chỉ Employee active mới nhận Employee Account

---

## Kết quả Review từng chức năng

### ON-01 — Kích hoạt từ Candidate Accepted
- **Ngày review:** —
- **Người review:** —
- **Kết quả:** ⬜
- **Ghi chú:** —

### ON-02 — Tạo Process Nguyên Tử
- **Ngày review:** —
- **Người review:** —
- **Kết quả:** ⬜
- **Ghi chú:** —

### ON-03 — Checklist & Activation
- **Ngày review:** —
- **Người review:** —
- **Kết quả:** ⬜
- **Ghi chú:** —
