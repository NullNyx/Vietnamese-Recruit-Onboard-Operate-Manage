-- ============================================================================
-- Vroom HR — Comprehensive Demo Data Seed v2
-- ============================================================================
-- Cung cấp dữ liệu mẫu tiếng Việt cho các module chính:
--   Recruitment (Job Openings, Applications, Candidates, Interviews)
--   Onboarding (Processes, Tasks)
--   Employee Requests (Leave, Overtime, Correction)
--   Config (Whitelist, AI)
--
-- Usage:
--   docker exec -i vroom-postgres psql -U postgres -d vroom_hr < this_file.sql
--
-- Idempotent: mỗi section kiểm tra trước khi insert.
-- Mỗi section là một DO block riêng, không dùng transaction chung.
-- ============================================================================

-- Reference IDs (từ dữ liệu hiện có):
-- User HR:    ffbe3f1f-5c48-406b-9657-32e345247614 (hr@vroom.com)
-- Employee:   36ed96a4-c096-4f18-8058-5f775d0fdbc3 (Hoang Xuan Nguyen)
-- Dept Eng:   87cf5f58-7741-4fa9-9c8b-1fcc63b143ef
-- Dept People: ef22304d-4752-4a19-aa88-710452e15392
-- Pos BE:     25adc5d8-888e-4b27-ac94-0948ef63ee83
-- Pos HR:     d93b2c03-bf3b-4989-9af5-aa49345f2fbb
-- Email 1:    39e37068-84ed-41cf-9d9e-4dcc00de6dbb
-- Email 2:    759dd7d2-bae4-4f9b-b347-01f5e824e153
-- Email 3:    c85f798a-bf10-40bd-8f9d-f77d3bb16f99
-- Email 4:    7712aa98-e84c-42cf-8864-78690b935ccd
-- Email 5:    d426a1ff-44cb-4e51-b848-b4c046e9f2df

-- ============================================================================
-- 1. Whitelist Entries
-- ============================================================================
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM whitelist_entries LIMIT 1) THEN
    INSERT INTO whitelist_entries (id, value, entry_type, added_by_user_id, created_at) VALUES
      ('b0000001-0000-0000-0000-000000000001', '@vroom.com', 'domain_pattern', 'ffbe3f1f-5c48-406b-9657-32e345247614', '2026-07-01 00:00:00+00'),
      ('b0000001-0000-0000-0000-000000000002', 'hr@vroom.com', 'exact_email', 'ffbe3f1f-5c48-406b-9657-32e345247614', '2026-07-01 00:00:00+00');
    RAISE NOTICE '✅ Whitelist: 2 entries';
  ELSE
    RAISE NOTICE '⏭️  Whitelist: already seeded';
  END IF;
END $$;

-- ============================================================================
-- 2. Organization AI Configuration
-- ============================================================================
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM organization_ai_configurations LIMIT 1) THEN
    INSERT INTO organization_ai_configurations (
      id, organization_singleton_key, provider, base_url, model,
      api_key_enc, credential_source,
      ai_automation_enabled, ai_assistant_enabled,
      ai_automation_consent, ai_assistant_consent,
      ai_policy_preset, ai_policy_preset_version,
      data_policy_accepted, data_policy_accepted_at,
      data_policy_accepted_by_user_id, data_policy_version,
      classification_policy, classification_policy_version,
      stable_classifier_version, rollout_mode, canary_percentage,
      created_at, updated_at
    ) VALUES (
      'b0000002-0000-0000-0000-000000000001', 'default',
      'openai', 'https://api.openai.com/v1', 'gpt-4o-mini',
      '', 'org_api_key',
      true, true,
      true, true,
      'balanced', 'balanced-v1',
      true, '2026-07-01 00:00:00+00',
      'ffbe3f1f-5c48-406b-9657-32e345247614', 'v1',
      'balanced', 'balanced-v1',
      'classifier-v1', 'stable', 0,
      '2026-07-01 00:00:00+00', '2026-07-01 00:00:00+00'
    );
    RAISE NOTICE '✅ AI Configuration: 1 record';
  ELSE
    RAISE NOTICE '⏭️  AI Configuration: already seeded';
  END IF;
END $$;

-- ============================================================================
-- 3. Job Openings
-- ============================================================================
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM job_openings LIMIT 1) THEN
    INSERT INTO job_openings (id, title, description, position_id, target_headcount, status, opened_at, created_at, updated_at) VALUES
      ('c0000001-0000-0000-0000-000000000001', 'Senior Backend Engineer',
       'Xây dựng và duy trì hệ thống backend cho nền tảng HR. Yêu cầu 3+ năm kinh nghiệm Python/FastAPI, PostgreSQL.',
       '25adc5d8-888e-4b27-ac94-0948ef63ee83', 2, 'open',
       '2026-07-01 00:00:00+00', '2026-07-01 00:00:00+00', '2026-07-01 00:00:00+00'),
      ('c0000001-0000-0000-0000-000000000002', 'HR Specialist',
       'Phụ trách tuyển dụng và onboarding cho tổ chức. Yêu cầu 2+ năm kinh nghiệm HR, tiếng Anh tốt.',
       'd93b2c03-bf3b-4989-9af5-aa49345f2fbb', 1, 'open',
       '2026-07-05 00:00:00+00', '2026-07-05 00:00:00+00', '2026-07-05 00:00:00+00'),
      ('c0000001-0000-0000-0000-000000000003', 'Junior Frontend Developer',
       'Phát triển giao diện Next.js cho nền tảng HR. Yêu cầu 6 tháng+ kinh nghiệm React/Next.js.',
       '25adc5d8-888e-4b27-ac94-0948ef63ee83', 1, 'draft',
       NULL, '2026-07-10 00:00:00+00', '2026-07-10 00:00:00+00');
    RAISE NOTICE '✅ Job Openings: 3 records';
  ELSE
    RAISE NOTICE '⏭️  Job Openings: already seeded';
  END IF;
END $$;

-- ============================================================================
-- 4. Job Applications
-- ============================================================================
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM job_applications LIMIT 1) THEN
    INSERT INTO job_applications (
      id, source_email_message_id, gmail_message_id, gmail_thread_id,
      source, applicant_name, applicant_email, sender_name, sender_email,
      job_opening_id, status, intent, has_cv,
      evidence, source_hints, message_references, audit_history,
      created_at, updated_at
    ) VALUES
      ('c0000002-0000-0000-0000-000000000001',
       '39e37068-84ed-41cf-9d9e-4dcc00de6dbb', 'gm-msg-001', 'gm-thread-001',
       'email', N'Nguyễn Văn An', 'nguyenvana@gmail.com', N'Nguyễn Văn An', 'nguyenvana@gmail.com',
       'c0000001-0000-0000-0000-000000000001', 'processed', 'job_application', true,
       '{"cv_parsed": true, "skills": ["Python", "FastAPI", "PostgreSQL"]}',
       '{"cv_filename": "CV_NguyenVanAn.pdf"}',
       '{"in_reply_to": null}',
       '[{"action": "classified", "at": "2026-07-15T08:00:00Z", "result": "job_application"}]',
       '2026-07-15 08:00:00+00', '2026-07-15 08:00:00+00'),

      ('c0000002-0000-0000-0000-000000000002',
       '759dd7d2-bae4-4f9b-b347-01f5e824e153', 'gm-msg-002', 'gm-thread-002',
       'email', N'Trần Thị Bình', 'tranthib@yahoo.com', N'Trần Thị Bình', 'tranthib@yahoo.com',
       NULL, 'needs_review', 'job_application', false,
       '{"cv_parsed": false}',
       '{"cv_filename": null}',
       '{"in_reply_to": null}',
       '[{"action": "classified", "at": "2026-07-16T09:00:00Z", "result": "job_application"}]',
       '2026-07-16 09:00:00+00', '2026-07-16 09:00:00+00'),

      ('c0000002-0000-0000-0000-000000000003',
       'c85f798a-bf10-40bd-8f9d-f77d3bb16f99', 'gm-msg-003', 'gm-thread-003',
       'referral', N'Lê Văn Chính', 'levanc@gmail.com', N'Hoàng Xuân Nguyên', 'hoangxuannguyen2005@gmail.com',
       'c0000001-0000-0000-0000-000000000002', 'processed', 'job_application', true,
       '{"cv_parsed": true, "skills": ["HR", "Recruitment", "English"]}',
       '{"cv_filename": "CV_LeVanChinh.pdf", "referrer": "Hoang Xuan Nguyen"}',
       '{"in_reply_to": null}',
       '[{"action": "classified", "at": "2026-07-16T10:00:00Z", "result": "job_application"}]',
       '2026-07-16 10:00:00+00', '2026-07-16 10:00:00+00'),

      ('c0000002-0000-0000-0000-000000000004',
       '7712aa98-e84c-42cf-8864-78690b935ccd', 'gm-msg-004', 'gm-thread-004',
       'email', NULL, NULL, N'Công ty ABC', 'partner@abc-company.vn',
       NULL, 'processed', 'partner', false,
       '{"cv_parsed": false}',
       '{"cv_filename": null}',
       '{"in_reply_to": null}',
       '[{"action": "classified", "at": "2026-07-17T08:30:00Z", "result": "partner"}]',
       '2026-07-17 08:30:00+00', '2026-07-17 08:30:00+00'),

      ('c0000002-0000-0000-0000-000000000005',
       'd426a1ff-44cb-4e51-b848-b4c046e9f2df', 'gm-msg-005', 'gm-thread-005',
       'email', N'Hồ Văn Em', 'hovane@outlook.com', N'Hồ Văn Em', 'hovane@outlook.com',
       'c0000001-0000-0000-0000-000000000001', 'processed', 'job_application', true,
       '{"cv_parsed": true, "skills": ["Python", "Django", "Docker", "AWS"]}',
       '{"cv_filename": "CV_HoVanEm.pdf"}',
       '{"in_reply_to": null}',
       '[{"action": "classified", "at": "2026-07-17T11:00:00Z", "result": "job_application"}]',
       '2026-07-17 11:00:00+00', '2026-07-17 11:00:00+00'),

      ('c0000002-0000-0000-0000-000000000006',
       '39e37068-84ed-41cf-9d9e-4dcc00de6dbb', 'gm-msg-006', 'gm-thread-006',
       'email', NULL, NULL, N'Phòng IT', 'it@vroom.com',
       NULL, 'processed', 'internal', false,
       '{"cv_parsed": false}',
       '{"cv_filename": null}',
       '{"in_reply_to": null}',
       '[{"action": "classified", "at": "2026-07-17T14:00:00Z", "result": "internal"}]',
       '2026-07-17 14:00:00+00', '2026-07-17 14:00:00+00');

    RAISE NOTICE '✅ Job Applications: 6 records';
  ELSE
    RAISE NOTICE '⏭️  Job Applications: already seeded';
  END IF;
END $$;

-- ============================================================================
-- 5. Candidates
-- ============================================================================
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM candidates LIMIT 1) THEN
    INSERT INTO candidates (
      id, name, email, phone,
      skills, experience, education, summary,
      status, confidence_score,
      job_opening_id,
      source_email_message_id,
      created_at, updated_at
    ) VALUES
      ('c0000003-0000-0000-0000-000000000001',
       N'Nguyễn Văn An', 'nguyenvana@gmail.com', '0901000001',
       '["Python", "FastAPI", "PostgreSQL"]',
       '["FPT Software - Backend Developer (3 năm)", "VNG - Junior Dev (1 năm)"]',
       '["ĐH Bách Khoa TP.HCM - Kỹ sư CNTT (2019)"]',
       N'Kỹ sư backend 4 năm kinh nghiệm, chuyên Python và PostgreSQL.',
       'new', 0.85,
       'c0000001-0000-0000-0000-000000000001',
       '39e37068-84ed-41cf-9d9e-4dcc00de6dbb',
       '2026-07-16 08:00:00+00', '2026-07-16 08:00:00+00'),

      ('c0000003-0000-0000-0000-000000000002',
       N'Trần Thị Bình', 'tranthib@yahoo.com', '0901000002',
       '["React", "TypeScript"]',
       '["Tiki - Frontend Developer (1.5 năm)"]',
       '["ĐH KHTN TP.HCM - Cử nhân CNTT (2022)"]',
       N'Frontend developer trẻ, đam mê React và TypeScript.',
       'reviewing', 0.72,
       NULL,
       '759dd7d2-bae4-4f9b-b347-01f5e824e153',
       '2026-07-17 09:00:00+00', '2026-07-17 09:00:00+00'),

      ('c0000003-0000-0000-0000-000000000003',
       N'Lê Văn Chính', 'levanc@gmail.com', '0901000003',
       '["HR", "Recruitment", "English"]',
       '["Navigos Group - Recruitment Consultant (3 năm)", "Manpower - HR Coordinator (2 năm)"]',
       '["ĐH Kinh Tế TP.HCM - Cử nhân QTKD (2018)"]',
       N'Chuyên viên tuyển dụng 5 năm kinh nghiệm, tiếng Anh lưu loát.',
       'interview_scheduled', 0.91,
       'c0000001-0000-0000-0000-000000000002',
       'c85f798a-bf10-40bd-8f9d-f77d3bb16f99',
       '2026-07-17 10:00:00+00', '2026-07-18 06:00:00+00'),

      ('c0000003-0000-0000-0000-000000000004',
       N'Hồ Văn Em', 'hovane@outlook.com', '0901000004',
       '["Python", "Django", "Docker", "AWS"]',
       '["Sendo - Backend Developer (4 năm)"]',
       '["ĐH Cần Thơ - Kỹ sư CNTT (2018)"]',
       N'Kỹ sư backend giàu kinh nghiệm, từng làm việc với hệ thống lớn.',
       'accepted', 0.88,
       'c0000001-0000-0000-0000-000000000001',
       'd426a1ff-44cb-4e51-b848-b4c046e9f2df',
       '2026-07-18 02:00:00+00', '2026-07-18 06:30:00+00'),

      ('c0000003-0000-0000-0000-000000000005',
       N'Phạm Thị Dung', 'phamthid@gmail.com', '0901000005',
       '["HR", "Excel"]',
       '["AIA Vietnam - Admin Assistant (2 năm)"]',
       '["ĐH Mở TP.HCM - Cử nhân QTKD (2022)"]',
       N'Ứng viên trái ngành muốn chuyển sang HR. Kỹ năng Excel tốt.',
       'rejected', 0.45,
       'c0000001-0000-0000-0000-000000000002',
       NULL,
       '2026-07-17 05:00:00+00', '2026-07-18 01:00:00+00');

    RAISE NOTICE '✅ Candidates: 5 records (new/reviewing/interview_scheduled/accepted/rejected)';
  ELSE
    RAISE NOTICE '⏭️  Candidates: already seeded';
  END IF;
END $$;

-- ============================================================================
-- 6. Interviews + Participants
-- ============================================================================
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM interviews LIMIT 1) THEN
    INSERT INTO interviews (
      id, candidate_id, status, round_name,
      start_at, end_at, timezone,
      meeting_mode, meeting_link, calendar_id,
      needs_relink,
      created_at, updated_at
    ) VALUES
      ('c0000004-0000-0000-0000-000000000001',
       'c0000003-0000-0000-0000-000000000003', 'scheduled',
       N'Vòng 1 — Phỏng vấn kỹ thuật',
       '2026-07-20 09:00:00+00', '2026-07-20 10:00:00+00', 'Asia/Ho_Chi_Minh',
       'google_meet', 'https://meet.google.com/abc-defg-hij',
       'family04977367558189544443@group.calendar.google.com',
       false,
       '2026-07-18 06:00:00+00', '2026-07-18 06:00:00+00'),

      ('c0000004-0000-0000-0000-000000000002',
       'c0000003-0000-0000-0000-000000000003', 'scheduled',
       N'Vòng 2 — Phỏng vấn văn hóa',
       '2026-07-22 14:00:00+00', '2026-07-22 15:00:00+00', 'Asia/Ho_Chi_Minh',
       'in_person', NULL, NULL,
       false,
       '2026-07-18 06:10:00+00', '2026-07-18 06:10:00+00'),

      ('c0000004-0000-0000-0000-000000000003',
       'c0000003-0000-0000-0000-000000000002', 'scheduled',
       N'Screening ban đầu',
       '2026-07-21 10:00:00+00', '2026-07-21 10:30:00+00', 'Asia/Ho_Chi_Minh',
       'google_meet', 'https://meet.google.com/xyz-uvwx-yz',
       'family04977367558189544443@group.calendar.google.com',
       false,
       '2026-07-18 05:00:00+00', '2026-07-18 05:00:00+00');

    INSERT INTO interview_participants (id, interview_id, type, email, name, employee_id, created_at, response_status) VALUES
      ('c0000005-0000-0000-0000-000000000001', 'c0000004-0000-0000-0000-000000000001', 'interviewer', 'hr@vroom.com', N'HR Admin', '36ed96a4-c096-4f18-8058-5f775d0fdbc3', '2026-07-18 06:00:00+00', 'accepted'),
      ('c0000005-0000-0000-0000-000000000002', 'c0000004-0000-0000-0000-000000000001', 'candidate', 'levanc@gmail.com', N'Lê Văn Chính', NULL, '2026-07-18 06:00:00+00', 'accepted'),
      ('c0000005-0000-0000-0000-000000000003', 'c0000004-0000-0000-0000-000000000002', 'interviewer', 'hr@vroom.com', N'HR Admin', '36ed96a4-c096-4f18-8058-5f775d0fdbc3', '2026-07-18 06:10:00+00', 'accepted'),
      ('c0000005-0000-0000-0000-000000000004', 'c0000004-0000-0000-0000-000000000002', 'candidate', 'levanc@gmail.com', N'Lê Văn Chính', NULL, '2026-07-18 06:10:00+00', 'pending'),
      ('c0000005-0000-0000-0000-000000000005', 'c0000004-0000-0000-0000-000000000003', 'interviewer', 'hr@vroom.com', N'HR Admin', '36ed96a4-c096-4f18-8058-5f775d0fdbc3', '2026-07-18 05:00:00+00', 'accepted'),
      ('c0000005-0000-0000-0000-000000000006', 'c0000004-0000-0000-0000-000000000003', 'candidate', 'tranthib@yahoo.com', N'Trần Thị Bình', NULL, '2026-07-18 05:00:00+00', 'accepted');

    RAISE NOTICE '✅ Interviews: 3 scheduled + 6 participants';
  ELSE
    RAISE NOTICE '⏭️  Interviews: already seeded';
  END IF;
END $$;

-- ============================================================================
-- 7. Employee Requests
-- ============================================================================
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM employee_requests LIMIT 1) THEN
    INSERT INTO employee_requests (
      id, employee_id, request_type, status,
      submitted_at, updated_at, created_at,
      leave_type, start_date, end_date,
      work_date, start_time, end_time, duration_minutes,
      reason, reviewed_at, reviewed_by_user_id, review_reason
    ) VALUES
      ('d0000001-0000-0000-0000-000000000001',
       '36ed96a4-c096-4f18-8058-5f775d0fdbc3', 'leave', 'pending',
       '2026-07-18 03:00:00+00', '2026-07-18 03:00:00+00', '2026-07-18 03:00:00+00',
       N'nghỉ phép năm', '2026-07-25', '2026-07-27',
       NULL, NULL, NULL, NULL,
       N'Nghỉ phép năm về quê thăm gia đình.',
       NULL, NULL, NULL),

      ('d0000001-0000-0000-0000-000000000002',
       '36ed96a4-c096-4f18-8058-5f775d0fdbc3', 'leave', 'approved',
       '2026-07-15 02:00:00+00', '2026-07-15 06:00:00+00', '2026-07-15 02:00:00+00',
       N'nghỉ ốm', '2026-07-15', '2026-07-15',
       NULL, NULL, NULL, NULL,
       N'Bị sốt, không thể đi làm.',
       '2026-07-15 06:00:00+00', 'ffbe3f1f-5c48-406b-9657-32e345247614', N'Đồng ý, nghỉ ngơi điều trị.'),

      ('d0000001-0000-0000-0000-000000000003',
       '36ed96a4-c096-4f18-8058-5f775d0fdbc3', 'overtime', 'approved',
       '2026-07-17 10:00:00+00', '2026-07-17 12:00:00+00', '2026-07-17 10:00:00+00',
       NULL, NULL, NULL,
       '2026-07-20', '17:30', '20:00', 150,
       N'Hoàn thành gấp tính năng chấm công trước deadline.',
       '2026-07-17 12:00:00+00', 'ffbe3f1f-5c48-406b-9657-32e345247614', N'OK, làm thêm có lương.'),

      ('d0000001-0000-0000-0000-000000000004',
       '36ed96a4-c096-4f18-8058-5f775d0fdbc3', 'correction', 'pending',
       '2026-07-18 04:00:00+00', '2026-07-18 04:00:00+00', '2026-07-18 04:00:00+00',
       NULL, NULL, NULL,
       '2026-07-14', '08:00', '17:30', NULL,
       N'Quên chấm công ngày 14/7 do đi họp ngoài công ty từ sáng. Có email xác nhận của quản lý.',
       NULL, NULL, NULL);

    RAISE NOTICE '✅ Employee Requests: 4 records';
  ELSE
    RAISE NOTICE '⏭️  Employee Requests: already seeded';
  END IF;
END $$;

-- ============================================================================
-- 8. Onboarding (cho candidate đã accepted)
-- ============================================================================
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM onboarding_processes LIMIT 1) THEN
    INSERT INTO onboarding_processes (
      id, candidate_id, employee_id, status, created_at, updated_at
    ) VALUES (
      'e0000001-0000-0000-0000-000000000001',
      'c0000003-0000-0000-0000-000000000004',
      '36ed96a4-c096-4f18-8058-5f775d0fdbc3',  -- gán tạm employee hiện có
      'in_progress',
      '2026-07-18 06:30:00+00', '2026-07-18 06:30:00+00'
    );

    INSERT INTO onboarding_tasks (
      id, process_id, task_key, name, status, order_index, created_at
    ) VALUES
      ('e0000002-0000-0000-0000-000000000001', 'e0000001-0000-0000-0000-000000000001', 'sign_contract', N'Ký hợp đồng lao động', 'done', 1, '2026-07-18 06:30:00+00'),
      ('e0000002-0000-0000-0000-000000000002', 'e0000001-0000-0000-0000-000000000001', 'submit_docs', N'Nộp hồ sơ cá nhân', 'done', 2, '2026-07-18 06:30:00+00'),
      ('e0000002-0000-0000-0000-000000000003', 'e0000001-0000-0000-0000-000000000001', 'assign_dept', N'Gán phòng ban & vị trí', 'pending', 3, '2026-07-18 06:30:00+00'),
      ('e0000002-0000-0000-0000-000000000004', 'e0000001-0000-0000-0000-000000000001', 'set_start_date', N'Đặt ngày bắt đầu làm việc', 'pending', 4, '2026-07-18 06:30:00+00');

    RAISE NOTICE '✅ Onboarding: 1 process + 4 tasks';
  ELSE
    RAISE NOTICE '⏭️  Onboarding: already seeded';
  END IF;
END $$;

-- ============================================================================
-- Summary
-- ============================================================================
DO $$
BEGIN
  RAISE NOTICE '';
  RAISE NOTICE '═══════════════════════════════════════════════════════';
  RAISE NOTICE '  Vroom HR — Demo Data Seed Complete';
  RAISE NOTICE '═══════════════════════════════════════════════════════';
  RAISE NOTICE '  Recruitment: 3 openings, 6 applications, 5 candidates, 3 interviews';
  RAISE NOTICE '  Onboarding:  1 process + 4 tasks';
  RAISE NOTICE '  Requests:    4 employee requests';
  RAISE NOTICE '  Config:      2 whitelist, 1 AI config';
  RAISE NOTICE '═══════════════════════════════════════════════════════';
END $$;
