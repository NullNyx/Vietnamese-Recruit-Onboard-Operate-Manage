# 10 — Payslip (Phiếu lương)

> **Nhóm:** Payslip | **Tổng:** 2 chức năng | **Deployed:** 2 | **Pending Review:** 2
> **Backend module:** `backend/src/modules/payslip/`
> **Frontend:** `(dashboard)/payroll/`, ESS Payslips

---

## Danh sách chức năng

| ID | Chức năng | Mô tả ngắn | Backend Route | Frontend Page | Status | Review |
|----|-----------|------------|---------------|---------------|--------|--------|
| PS-01 | HR Payslip CRUD | List/filter, tạo draft, sửa draft, publish, xóa draft | `/api/admin/payslips*` | Payroll UI | ✅ Deployed | ⬜ |
| PS-02 | Employee Payslip | Employee chỉ xem Payslip đã publish của chính mình | `/api/payslips/me*` | ESS Payslips | ✅ Deployed | ⬜ |

---

## Tiêu chí Review

- [ ] Router đã wired trong `backend/src/main.py`
- [ ] Draft không lộ qua ESS
- [ ] Employee chỉ xem Payslip của chính mình
- [ ] Publish/unpublish flow
- [ ] Payslip là bảng kê, không phải payroll calculation engine

---

## Kết quả Review từng chức năng

### PS-01 — HR Payslip CRUD
- **Ngày review:** —
- **Người review:** —
- **Kết quả:** ⬜
- **Ghi chú:** —

### PS-02 — Employee Payslip
- **Ngày review:** —
- **Người review:** —
- **Kết quả:** ⬜
- **Ghi chú:** —
