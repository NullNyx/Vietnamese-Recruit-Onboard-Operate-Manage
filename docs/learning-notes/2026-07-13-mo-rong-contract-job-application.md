# Task
Mở rộng contract Job Application theo issue #201.

# What I changed
Bổ sung `intent`, `application_source` và `has_cv` ở kết quả phân loại; lưu `intent` và `has_cv` độc lập trong Job Application; thêm migration 068 và API/frontend fields. Category Gmail legacy vẫn được giữ.

# The real problem
Intent ứng tuyển, nguồn hồ sơ và việc có CV là ba sự kiện khác nhau nhưng contract cũ dùng category và attachment để suy luận lẫn nhau.

# Why this solution
Giữ category cũ để không làm vỡ workflow, đồng thời thêm các field ổn định ở boundary và persistence. Ingestion vẫn là boundary duy nhất tạo Job Application, nên AI không có đường promote Candidate.

# Production shape
Migration expand trước, backfill dữ liệu cũ idempotently, sau đó application service ghi contract mới cho dữ liệu mới.

# Other possible approaches
1. Đổi hẳn `email.category` từ `recruitment` sang `job_application`, phù hợp khi mọi consumer đã migrate đồng bộ.
2. Lưu contract trong một JSONB duy nhất, phù hợp với schema thay đổi rất nhanh nhưng kém truy vấn và kiểm soát kiểu.

# Why I did not choose those alternatives
Đổi category ngay tạo breaking change cho Gmail label và workflow hiện hữu. JSONB làm mất contract rõ ràng và khó bảo đảm dữ liệu legacy.

# Key concepts to learn
Expand/contract migration, backward compatibility, idempotent ingestion, stable domain contract.

# Common mistakes
Không đồng nhất có attachment với intent ứng tuyển; không dùng AI callback để tạo Candidate; không backfill dữ liệu legacy có điều kiện.

# Small example
Một email referral có CV: `intent=job_application`, `source=employee_referral`, `has_cv=true`, sender vẫn là người giới thiệu.

# How to think about this next time
Tách từng trục domain độc lập trước khi thiết kế schema; giữ legacy read path trong giai đoạn expand và chỉ thay đổi write path tại một application boundary.
