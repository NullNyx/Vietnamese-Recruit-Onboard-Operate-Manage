# Runbook rollout Job Application classification

## Mục tiêu

Rollout classifier/policy theo thứ tự `stable → shadow → canary → full`, giữ Recruitment Inbox và Job Application hiện có khi rollback. Organization chỉ chọn policy nghiệp vụ `recall_first` (**Ưu tiên không bỏ sót**); threshold số là chi tiết hệ thống, không xuất hiện trong API/UI.

## Chuẩn bị

1. Chạy migration `066`.
2. Ghi lại classifier version, policy version và evaluation dataset version.
3. Chạy operational checks:

```bash
cd backend
uv run pytest tests/modules/gmail/test_classification_rollout.py -q
uv run pytest tests/modules/identity/test_classification_rollout_config.py -q
uv run alembic heads  # phải là 066
```

Các test trên chứng minh shadow trả stable result, partition giữ nguyên qua retry, release gate chặn full rollout và rollback giữ stable classifier/policy.

## Bật shadow

Trong Organization AI Configuration UI, nhập candidate classifier/policy version và chọn **Bật shadow**, hoặc gọi:

```http
PUT /api/admin/organization/ai-config/classification-rollout
Content-Type: application/json

{
  "mode": "shadow",
  "business_policy": "recall_first",
  "policy_version": "recall-first-v2",
  "classifier_version": "classifier-v2",
  "canary_percentage": 0
}
```

Shadow luôn trả kết quả stable cho workflow. Candidate chỉ tạo `classification_rollout_events`; lỗi provider candidate được ghi telemetry và không đổi Job Application, Recruitment Inbox hoặc Candidate.

## Kiểm tra telemetry

API operational tự động tổng hợp event mới nhất của mỗi email, correction/review state và duplicate durable:

```http
GET /api/admin/organization/ai-config/classification-rollout/telemetry?hours=24
```

Response có recall proxy (candidate/selected và stable), correction rate, review rate, `needs_classification` rate, p95 latency, provider error rate, duplicate count và `no_cv_recall_proxy` riêng.

Dùng bản ghi mới nhất của mỗi email để retry không làm lệch cohort:

```sql
WITH latest AS (
  SELECT DISTINCT ON (gmail_message_id) *
  FROM classification_rollout_events
  WHERE created_at >= now() - interval '24 hours'
  ORDER BY gmail_message_id, created_at DESC
), labelled AS (
  SELECT
    e.*,
    CASE
      WHEN e.stable_intent IS NOT NULL THEN e.stable_intent
      ELSE e.candidate_intent
    END AS selected_intent,
    i.corrected_intent,
    (i.id IS NOT NULL) AS reviewed
  FROM latest e
  LEFT JOIN recruitment_inbox_items i USING (gmail_message_id)
)
SELECT
  count(*) AS classified,
  avg((corrected_intent IS NOT NULL)::int)::float AS correction_rate,
  avg(reviewed::int)::float AS review_rate,
  percentile_cont(0.95) WITHIN GROUP (
    ORDER BY coalesce(candidate_latency_ms, stable_latency_ms)
  ) AS p95_latency_ms,
  avg(candidate_provider_error::int)::float AS provider_error_rate,
  (
    count(*) FILTER (
      WHERE corrected_intent = 'job_application'
        AND selected_intent IN ('recruitment', 'job_application')
    )::float
    / nullif(count(*) FILTER (WHERE corrected_intent = 'job_application'), 0)
  ) AS job_application_recall_proxy
FROM labelled;
```

Báo cáo cohort no-CV bắt buộc chạy riêng bằng cùng query với `WHERE e.has_cv = false` trong CTE `labelled`.

Kiểm tra duplicate thật từ durable workflow:

```sql
SELECT gmail_message_id, count(*)
FROM job_applications
GROUP BY gmail_message_id
HAVING count(*) > 1;
```

Kết quả phải rỗng. Không đưa subject, body, attachment content hoặc credential vào telemetry/export.

## Bật canary

Chỉ bật sau khi shadow không có side effect và candidate provider ổn định. UI dùng cohort 10%; API chấp nhận `1..100`:

```json
{
  "mode": "canary",
  "business_policy": "recall_first",
  "policy_version": "recall-first-v2",
  "classifier_version": "classifier-v2",
  "canary_percentage": 10
}
```

Partition là SHA-256 của `gmail_message_id` modulo 100, nên cùng email luôn vào cùng cohort qua retry.

## Full rollout

Full rollout chỉ qua API và phải gửi đủ release metrics. Backend từ chối nếu:

- Job Application recall `< 0.98`;
- `needs_classification_rate > 0.15`;
- recall thấp hơn baseline;
- thiếu báo cáo `no_cv_recall`;
- phát hiện duplicate.

```json
{
  "mode": "full",
  "business_policy": "recall_first",
  "policy_version": "recall-first-v2",
  "classifier_version": "classifier-v2",
  "canary_percentage": 100,
  "release_metrics": {
    "job_application_recall": 0.985,
    "baseline_recall": 0.98,
    "needs_classification_rate": 0.14,
    "no_cv_recall": 0.99,
    "correction_rate": 0.03,
    "review_rate": 0.14,
    "p95_latency_ms": 1200,
    "provider_error_rate": 0.002,
    "duplicate_count": 0
  }
}
```

Lưu evaluation report và câu SQL telemetry cùng model/prompt/policy/dataset version để audit có thể tái lập.

## Rollback

Gọi UI **Rollback stable** hoặc:

```http
POST /api/admin/organization/ai-config/classification-rollout/rollback
```

Rollback chỉ xóa candidate rollout state và phục hồi stable classifier/policy đã giữ lại. Không xóa hoặc sửa EmailMessage, Job Application, Recruitment Inbox item, Candidate hay correction. Sau rollback, kiểm tra API trả `rollout_mode=stable`, candidate version là `null`, và các work item trước đó vẫn truy cập được.
