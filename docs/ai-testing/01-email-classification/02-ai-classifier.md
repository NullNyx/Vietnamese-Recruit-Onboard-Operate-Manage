# 02 — AI Classifier Xử Lý Email Ambiguous

## Mục tiêu
Xác minh AI classifier (Gemma 4 LLM) phân loại đúng email mà rules classifier không tự tin.

## Mức độ ưu tiên
Critical

## Module liên quan
- `backend/src/modules/gmail/infrastructure/ai_classifier.py`
- System prompt: `_SYSTEM_PROMPT` trong ai_classifier.py

## Điều kiện tiên quyết
- Backend có kết nối tới LLM provider (OpenAI-compatible)
- Organization AI config đã được setup

## Các bước thực hiện

1. **Email ambiguous tuyển dụng**: body "Em là A, tốt nghiệp UIT, muốn ứng tuyển. Em để CV ở link drive."
   - Expected: category = `recruitment`, matched_signals chứa intent signal

2. **Email ambiguous offer**: "Em cảm ơn anh chị, em đồng ý mức lương 15tr, khi nào em bắt đầu ạ?"
   - Expected: category = `offer`

3. **Email ambiguous nghỉ việc**: "Em xin phép nghỉ việc từ tháng sau vì lý do cá nhân"
   - Expected: category = `resignation`

4. **Email ambiguous khiếu nại**: "Tôi muốn phản ánh về cách quản lý của anh B"
   - Expected: category = `complaint`

5. **Email không xác định được**: body chỉ có "OK" hoặc spam
   - Expected: category = `uncategorized`

## Kết quả mong đợi
- AI classifier trả về đúng 1 category, không giải thích
- Có confidence score, token_usage
- source = "ai"
- Timeout 15s, retry 3 lần với backoff 1s, 2s, 4s

## Test files
- `backend/tests/modules/gmail/test_classify_integration.py`
- `backend/tests/modules/gmail/test_classify_timeout.py`

## Trạng thái
- [ ] Chưa test
- [ ] Đang test
- [ ] Pass
- [ ] Fail (có bug)
