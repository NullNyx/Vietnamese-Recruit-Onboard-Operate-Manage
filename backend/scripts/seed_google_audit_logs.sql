-- ============================================================================
-- Seed Google Connection Audit Logs (Vietnamese format)
-- ============================================================================
-- Tạo dữ liệu mẫu audit log tiếng Việt cho tất cả action type Google
-- connection, bao gồm cả ``org_google_calendar_select`` (action type mới).
--
-- Usage:
--   docker exec -i vroom-postgres psql -U postgres -d vroom_hr < this_file.sql
--
-- Idempotent: bỏ qua nếu đã có bản ghi Vietnamese-format (key "kết_quả").
-- ============================================================================

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM audit_logs
        WHERE details ? 'kết_quả' AND action_type LIKE 'org_google%'
    ) THEN
        RAISE NOTICE '⏭️  Bỏ qua: đã có bản ghi Vietnamese-format Google audit logs.';
        RETURN;
    END IF;

    INSERT INTO audit_logs (id, admin_user_id, admin_email, action_type, details, created_at) VALUES
    -- Kết nối Google (lần đầu)
    ('a0000000-0000-0000-0000-000000000001',
     'ffbe3f1f-5c48-406b-9657-32e345247614', 'hr@vroom.com',
     'org_google_connect',
     '{"kết_quả": "đã kết nối"}',
     '2026-07-18 06:00:00+00'),

    -- Kết nối lại Google
    ('a0000000-0000-0000-0000-000000000002',
     'ffbe3f1f-5c48-406b-9657-32e345247614', 'hr@vroom.com',
     'org_google_reconnect',
     '{"kết_quả": "đã kết nối"}',
     '2026-07-18 06:10:00+00'),

    -- Chuyển tài khoản Google
    ('a0000000-0000-0000-0000-000000000003',
     'ffbe3f1f-5c48-406b-9657-32e345247614', 'hr@vroom.com',
     'org_google_switch_account',
     '{"kết_quả": "đã kết nối"}',
     '2026-07-18 06:20:00+00'),

    -- Ngắt kết nối Google
    ('a0000000-0000-0000-0000-000000000004',
     'ffbe3f1f-5c48-406b-9657-32e345247614', 'hr@vroom.com',
     'org_google_disconnect',
     '{"kết_quả": "đã ngắt kết nối"}',
     '2026-07-18 06:30:00+00'),

    -- Chọn lịch Google (family calendar)
    ('a0000000-0000-0000-0000-000000000005',
     'ffbe3f1f-5c48-406b-9657-32e345247614', 'hr@vroom.com',
     'org_google_calendar_select',
     '{"kết_quả": "đã chọn lịch", "lịch": "family04977367558189544443@group.calendar.google.com"}',
     '2026-07-18 06:40:00+00'),

    -- Chọn lịch Google (personal calendar)
    ('a0000000-0000-0000-0000-000000000006',
     'ffbe3f1f-5c48-406b-9657-32e345247614', 'hr@vroom.com',
     'org_google_calendar_select',
     '{"kết_quả": "đã chọn lịch", "lịch": "nthengoc.dev@gmail.com"}',
     '2026-07-18 06:50:00+00');

    RAISE NOTICE '✅ Đã seed 6 audit log Google connection (Vietnamese format).';
END $$;
