# Error / Exception Model — Vroom HR

Mục tiêu: chốt domain exceptions, API error codes, retry/fallback pattern cho MVP.

## 1. Domain exceptions

| Exception | When | Handling |
| --- | --- | --- |
| CaseNotFound | OnboardingCase not found by given id | Return 404, HR sees error banner |
| CandidateNotFound | Candidate not found when referenced | Return 404, block write |
| CandidateNotAccepted | Candidate status != accepted | Block case creation, return 400 |
| CaseAlreadyCompleted | HR tries to modify a completed case | Block domain-changing writes; read/audit/export still allowed |
| CaseAlreadyCancelled | HR tries to modify a cancelled case | Block domain-changing writes; read/audit/export still allowed |
| InvalidStatusTransition | Status change violates domain rules | Return 400 with allowed transitions |
| TemplateNotFoundById | Template requested by id does not exist | Return 404 |
| NoCompanyTemplateConfigured | Company has no template configured for a flow | Use system default template |
| DuplicateCandidateCase | OnboardingCase already exists for candidate | Return 409 with existing case id |
| FileTooLarge | Upload exceeds limit | Return 413 |
| UnsupportedFileType | File format not accepted | Return 415 with accepted types |
| AiProviderTimeout | AI draft/extraction call times out | Return 503, HR sees "AI temporarily unavailable" |
| AiProviderLowConfidence | AI cannot produce result with sufficient confidence | Return fallback result with confidence_label = low; not an error |
| AuditWriteFailure | Audit log write fails for important write | Block transaction, rollback write, return 500 |

## 2. API error codes

| HTTP | Error | Meaning | Retryable |
| --- | --- | --- | --- |
| 400 | bad_request | Invalid input or status transition | No |
| 400 | candidate_not_accepted | Candidate cannot start onboarding | No |
| 400 | case_already_completed | Case closed, no more domain-changing writes allowed | No |
| 400 | case_already_cancelled | Case cancelled, no more domain-changing writes allowed | No |
| 400 | invalid_status_transition | Domain state change not allowed | No |
| 404 | not_found | Entity not found | No |
| 409 | conflict | Duplicate case or concurrent edit | No |
| 413 | file_too_large | Upload exceeds size limit | No, reduce size |
| 415 | unsupported_file_type | File format not accepted | No, use accepted format |
| 422 | validation_error | Input validation failed | No, fix input |
| 429 | rate_limited | Too many requests (for AI calls) | Yes, after backoff |
| 500 | internal_error | Unexpected server error or audit write failure | No |
| 503 | service_unavailable | Database or external dependency unavailable | Yes |
| 503 | ai_unavailable | AI provider timeout / down | Yes |

## 3. Success / fallback response for AI low confidence

Low confidence is not an error. Return 200 with explicit fallback payload.

```json
{
  "result_type": "fallback",
  "confidence_label": "low",
  "message": "Không đủ dữ liệu để đề xuất chắc chắn",
  "details": {
    "missing_fields": ["start_date", "salary"]
  },
  "request_id": "req-xxx"
}
```

- No HTTP error for low confidence.
- HR may continue manually.
- No entity change until HR confirms a write.

## 4. Error response shape

```json
{
  "error": {
    "code": "case_not_found",
    "message": "OnboardingCase not found",
    "details": {"case_id": "abc-123"},
    "request_id": "req-xxx"
  }
}
```

- code: machine-readable error key
- message: human-readable description
- details: optional context for this occurrence
- request_id: traceable to server log / correlation_id

### 4.1 Safety rule for details

`details` must not include raw PII, contract body, CV text, or document OCR content.

## 5. Retry rules

| Error | Retry strategy | Max attempts |
| --- | --- | --- |
| ai_unavailable | Exponential backoff (1s, 2s, 4s) | 3 |
| ai_low_confidence | No auto-retry; fallback to manual | 0 |
| file_too_large | No retry, return error immediately | 0 |
| validation_error | No retry, fix input | 0 |
| conflict | No auto-retry; refresh latest state and let HR decide | 0 |
| service_unavailable | Retry if transient and safe | 3 |

## 6. UI fallback rules

| Scenario | Fallback |
| --- | --- |
| AI draft fails | Show "AI không khả dụng lúc này" + HR can still type manually |
| AI extraction fails | Show "Không thể đọc file" + HR upload/view file manually |
| AI summary fails | Show normal dashboard data without summary |
| Read API fails (CRUD) | Error banner + retry button |
| Write API fails | Error banner, do not simulate success, keep previous UI state |
| File upload fails | Keep DocumentItem unchanged, show error |
| Concurrent edit conflict | Refresh latest state, then HR decides |

## 7. Correlation id

- Every request that goes through AI path carries `correlation_id`
- Audit log records `correlation_id` for multi-step operations
- Error response includes `request_id` (mapped to correlation_id when AI path involved)

## 8. What is out of scope for this model

- Low-level DB driver errors beyond HTTP mapping
- Network errors below application layer
- Auth token expiry (handled by auth middleware)

## 9. Next step

After review, update checklist. ADRs if there are open trade-offs.
