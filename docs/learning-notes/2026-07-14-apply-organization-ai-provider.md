# Task

Áp dụng cấu hình provider/model/API key của Organization vào AI Assistant runtime.

# What I changed

- Thêm `AIProviderRuntimeConfig` và resolver `get_runtime_config()` trong `OrganizationAIConfigService`.
- Assistant đọc provider từ `organization_ai_configurations` khi Organization đã cấu hình.
- Chỉ fallback về `ASSISTANT_LLM_*` khi chưa có Organization config.
- Employee Assistant dùng cùng provider resolution boundary.
- Hỗ trợ gateway response dạng `{"data": {"choices": [...]}}`.
- Thêm regression tests cho provider resolution, disabled capability, dependency wiring và wrapped response.

# The real problem

Organization AI Settings lưu provider `api.cline.bot`, model và encrypted API key trong PostgreSQL, nhưng Assistant container chỉ đọc environment `ASSISTANT_LLM_*`. Hai nguồn cấu hình không có precedence contract. Sau khi wiring được sửa, provider Cline trả response hợp lệ nhưng bọc payload trong `data`, khiến OpenAI SDK không điền `response.choices`.

# Why this solution

Một resolver dùng chung giữ credential resolution và capability state trong Organization service. Fallback chỉ xảy ra trước khi setup để local bootstrap vẫn chạy; khi đã có config, hệ thống không âm thầm dùng provider khác. Parser tương thích được giới hạn tại LLM client, giữ application service độc lập với SDK/provider layout.

# Production shape

- Organization config là nguồn sự thật cho provider/model/credential.
- Capability disabled trả lỗi cấu hình, không fallback im lặng.
- Credential vẫn được decrypt trong backend, không gửi ra frontend.
- Assistant client mới được tạo từ runtime settings của Organization.
- Provider adapter chấp nhận OpenAI response chuẩn và gateway wrapper đã biết.

# Other possible approaches

1. Copy Organization config vào environment khi deploy/restart. Phù hợp deployment đơn giản, ít request-time lookup.
2. Tạo một shared `ProviderClientFactory` cho Gmail Automation, HR Assistant và Employee Assistant. Phù hợp khi cần telemetry, pooling và policy enforcement đồng nhất ở nhiều module.
3. Giữ Assistant env-only và bỏ UI Organization provider. Phù hợp sản phẩm operator-managed, không phù hợp ADR hiện tại.

# Why I did not choose those alternatives

- Đồng bộ qua environment tạo stale config sau khi HR rotate key hoặc đổi model, đồng thời cần restart deployment.
- Factory dùng chung là hướng kiến trúc tốt hơn về dài hạn nhưng có blast radius lớn hơn root fix; hiện tại resolver dùng lại logic đã có.
- Bỏ Organization UI vi phạm ADR 0003 và user story về Organization AI Configuration.

# Key concepts to learn

- Configuration source of truth và precedence contract.
- Runtime dependency injection với FastAPI `Depends`.
- Encrypted credential resolution ở application boundary.
- OpenAI-compatible không luôn có nghĩa response JSON giống hệt OpenAI.
- Pydantic SDK có thể lưu unknown wrapper trong `model_extra`.

# Common mistakes

- Kiểm tra provider health chỉ bằng HTTP 200 mà không validate response shape.
- Để UI lưu config database nhưng runtime vẫn đọc env cũ.
- Fallback sang provider khác sau khi Organization đã cấu hình mà không audit.
- Giả định `response.choices` luôn tồn tại từ mọi OpenAI-compatible gateway.

# Small example

```python
runtime = await service.get_runtime_config(capability="assistant")
settings = AssistantSettings(
    base_url=runtime.base_url,
    model=runtime.model,
    api_key=runtime.api_key,
)
```

# How to think about this next time

Khi provider trong UI khác provider trong runtime, so sánh ba lớp: database row, dependency wiring và SDK request. Sau đó kiểm tra raw response shape từ provider thay vì chỉ nhìn HTTP status. Mọi fallback phải có điều kiện rõ ràng và không được che khuất config đã được HR chấp nhận.
