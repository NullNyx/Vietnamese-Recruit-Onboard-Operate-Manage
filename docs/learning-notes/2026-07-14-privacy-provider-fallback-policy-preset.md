# Task
Triển khai #204: privacy, consent độc lập và AI Policy Preset cho Organization AI Configuration.

# What I changed
- Thêm consent riêng cho AI Automation và AI Assistant; bật capability phải có data policy chung và consent tương ứng.
- Thêm `AIPolicyPreset` có version (`conservative`, `balanced`, `high_recall`), không expose raw threshold.
- Thêm migration 070, API response và endpoint consent/policy preset; cập nhật client TypeScript.
- Thêm policy boundary cho provider fallback: chỉ fallback khi cùng privacy boundary và đạt quality floor.
- Bổ sung test application-service cho consent độc lập, preset và fallback policy.

# The real problem
Một cờ `data_policy_accepted` không chứng minh Organization chấp nhận từng capability. Ngoài ra, cho HR nhập threshold trực tiếp làm policy khó kiểm soát và không tái lập.

# Why this solution
Consent được kiểm tra tại application boundary trước khi enable, còn preset chỉ nhận enum đã version hóa. Như vậy UI không thể vượt qua guardrail bằng cách gửi threshold tùy ý.

# Production shape
Database lưu các cờ consent và preset version; admin API trả trạng thái đã mask, service kiểm tra credential/health/data policy/consent trước khi bật. Migration có server default để an toàn khi nâng cấp dữ liệu cũ.

# Other possible approaches
1. Gộp consent vào một cờ duy nhất: phù hợp với sản phẩm nhỏ chỉ có một capability AI.
2. Cho Organization tự nhập confidence threshold: phù hợp khi đã có calibration và governance riêng cho từng tenant.

# Why I did not choose those alternatives
Repo có hai capability với phạm vi dữ liệu khác nhau nên consent chung không đủ hẹp. Deployment single-Organization cũng chưa có evaluation/gov­ernance cho threshold tùy biến; preset trung tâm an toàn và tái lập hơn.

# Key concepts to learn
Application-service boundary, capability consent, versioned policy, migration default, human-in-the-loop, privacy policy enforcement.

# Common mistakes
- Chỉ kiểm tra toggle mà quên kiểm tra consent.
- Lưu threshold tùy ý của Organization như một policy chính thức.
- Đặt scalar enum của FastAPI thành query parameter trong khi client gửi JSON body.

# Small example
`data_policy_accepted=true`, `ai_automation_consent=true`, `ai_assistant_consent=false` chỉ cho phép bật AI Automation; AI Assistant vẫn bị từ chối.

# How to think about this next time
Tách ba lớp: policy chung về dữ liệu, consent theo capability, và preset vận hành version hóa. Mọi đường bật capability phải đi qua cùng một application service, không tin vào UI.
