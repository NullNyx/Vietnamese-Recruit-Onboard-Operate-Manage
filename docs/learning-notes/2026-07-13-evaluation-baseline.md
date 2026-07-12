# Evaluation baseline cho Job Application classifier

## Task

Thiết lập evaluation baseline có thể tái lập cho classifier hiện tại (RulesClassifier + AIClassifier) để team đo được Job Application recall trước khi thay đổi production. Evaluation set phải được redaction, có version, và bao phủ các cohort khó: không có CV, referral, agency, multi-applicant, mixed-purpose, follow-up, misleading-attachment, mixed-language. Runner phải báo cáo recall, precision, review rate tổng thể và riêng từng cohort; ghi nhận model/prompt/policy/dataset version; thất bại rõ ràng khi contract không hợp lệ.

## What I changed

- Thêm module `src/modules/gmail/evaluation/`:
  - `_contract.py`: định nghĩa `EvaluationContract`, `EvaluationDataset`, `EvaluationItem`, `Prediction`, `EvaluationReport`, `MetricRow`, `VersionInfo`, `Predictor` callable alias và custom exception `EvaluationContractError`.
  - `__init__.py`: public API surface.
- Thêm test file `tests/modules/gmail/test_evaluation.py`: 23 tests phủ schema validation, metric computation (recall, precision, review rate), cohort breakdown, version recording, frozen predictions, JSON serialisability, và các invalid contract scenarios.
- Thêm CLI `scripts/evaluate_baseline.py`: entry point dòng lệnh nhận `--dataset`, `--frozen-predictions`, `--predictor`, `--needs-review-threshold`, `--output`.
- Thêm evaluation dataset mẫu `data/evaluation/v1.0.0/dataset.json`: 24 items redacted, version 1.0.0, coverage tất cả 8 cohorts.

## The real problem

Evaluation cho email classifier có 3 khó khăn chính:

1. **Reproducibility phụ thuộc provider**: production dùng RulesClassifier + AIClassifier (Gemma 4). Nếu baseline command gọi AIClassifier thật, kết quả không tái lập được vì LLM output không deterministic. Giải pháp: thiết kế evaluator nhận injectable Predictor hoặc frozen predictions, không phụ thuộc live provider.

2. **Multi-class metrics**: classifier có 14 categories, nhưng primary interest là Job Application (recruitment). "Overall recall" trong multi-class context đồng nghĩa với accuracy — không cùng ý nghĩa với binary recall. Giải pháp: báo cáo per-category metrics riêng, đặc biệt recruitment, kèm overall accuracy.

3. **Cohort analysis**: evaluation set phải có 8 cohort khó, mỗi item có thể thuộc nhiều cohort. Metric computation phải map item cohorts → statistics đúng, kể cả khi một item có cohorts overlap.

## Why this solution

- **Injectable Predictor** dạng simple callable `(EvaluationItem) → Prediction`: dễ test, dễ wrap classifier cũ/mới, dễ dùng trong CI (frozen predictions).
- **Validation trước khi chạy**: `EvaluationContract.__init__` validate schema (version, items, ground_truth, cohorts) và frozen predictions reference consistency. Fail early, fail clearly.
- **Stateless runner**: `EvaluationContract._run()` là static method; test có thể call nó trực tiếp với dataset + predictor mà không cần build file contract.
- **VersionInfo riêng**: không gắn version vào dataset schema; để dataset header chứa optional model/prompt/policy version fields.

## Production shape

- Evaluation dataset sống ở `data/evaluation/<version>/dataset.json`; baseline v1 ghi rõ `rules-classifier-v1`, prompt không áp dụng cho rules-only, policy threshold và dataset version.
- Evaluation contract được load một lần, validate schema, sau đó `contract.run(predictor=...)` trả report.
- Report có `to_dict()` → JSON serialisable → artifact cho CI.
- CLI command: `uv run python scripts/evaluate_baseline.py --dataset data/evaluation/v1.0.0/dataset.json --predictor rules --output report.json`.
- Invalid contract exit code 1 với message rõ ràng.

## Other possible approaches

### Approach A: Evaluation framework riêng, độc lập khỏi module gmail

Tạo `src/evaluation/` ở top-level, không phụ thuộc vào `src/modules/gmail/`. Dataset, report types, và runner sống hoàn toàn độc lập.

*Khi nào phù hợp*: Khi nhiều module khác nhau cần evaluation framework giống nhau (ví dụ: salary extraction, leave classification,...).

### Approach B: Tích hợp sâu vào ClassificationService hiện tại

Thêm method `ClassificationService.evaluate()` nhận dataset, chạy classifier production, trả metrics. Dùng chung DI container và settings.

*Khi nào phù hợp*: Khi chỉ có một classifier cần evaluate và muốn dùng lại toàn bộ production config (retry, timeout, AI provider).

### Approach C: Dataset version tracking qua git submodule hoặc separate repo

Evaluation dataset sống trong repo riêng (hoặc git submodule) để version độc lập với code version. Dùng tags/semver để reference.

*Khi nào phù hợp*: Khi evaluation dataset có dữ liệu nhạy cảm không muốn lưu trong code repo, hoặc dataset được maintain bởi team khác.

## Why I did not choose those alternatives

- **Approach A** — overengineering. Hiện tại chỉ có Gmail classifier cần evaluate. Nếu có thêm module khác sau này, refactor thành shared framework dễ hơn vì types đã tách biệt khỏi business logic (evaluation types có import `EmailCategory` từ gmail domain, dependency cụ thể và có chủ đích).

- **Approach B** — vi phạm single responsibility. ClassificationService đã lo classification pipeline (rules → AI → persist). Thêm evaluation vào service đó tạo dependency vòng: assessment gọi predictor nhưng predictor có thể là chính service đó. Ngoài ra không cho phép frozen predictions (cần thay thế AI bằng deterministic stub).

- **Approach C** — premature optimization. Với self-hosted deployment, dataset redaction là bắt buộc trước khi commit. Submodule tăng độ phức tạp CI. Nếu dataset phát triển >100MB thì mới cần xem xét.

## Key concepts to learn

- **Evaluation contract**: schema ràng buộc dataset format, validate trước khi chạy, từ chối sớm thay vì thất bại giữa chừng.
- **Frozen predictions**: capture output thật của predictor baseline một lần → tái lập evaluation không cần provider; không được tự điền ground truth như prediction.
- **Multi-class metrics**: per-category TP/FP/FN, overall accuracy, cohort metrics. Confusion matrix mental model.
- **Cohort tag system**: one item → many cohorts → sum metrics per cohort, handle overlap.

## Common mistakes

- **Overall recall** trong multi-class: recall micro-average = precision micro-average = accuracy. Dễ nhầm lẫn với binary recall (của recruitment category).
- **Cohort overlap**: nếu một item thuộc 2 cohorts, metrics của cohort đó không độc lập — cùng một FN count có thể xuất hiện ở cả 2 cohort. Cần document rõ ràng.
- **Dataset version mismatch**: dataset version 1.0.0 nhưng code mới thêm/bớt category → ground_truth validation fail. Cần update dataset hoặc làm backward-compatible mapping.

## Small example

```python
from src.modules.gmail.evaluation import EvaluationContract, EvaluationItem, Prediction

contract = EvaluationContract.from_json("data/evaluation/v1.0.0/dataset.json")

def my_predictor(item: EvaluationItem) -> Prediction:
    return Prediction(
        item_id=item.id,
        category=item.ground_truth,  # perfect predictor for demo
        confidence=0.9,
        source="demo",
    )

report = contract.run(predictor=my_predictor)
print(f"Recall: {report.overall.recall:.2f}")
print(f"Recruitment recall: {report.per_category['recruitment'].recall:.2f}")
for cohort, metrics in report.per_cohort.items():
    print(f"  {cohort}: recall={metrics.recall:.2f}")
```

## How to think about this next time

Bắt đầu bằng **contract definition**: types và validation trước, runner sau. Điều này buộc phải nghĩ về data format, error boundary, và use case từ đầu — thay vì code runner rồi mới thấy thiếu validation. Frozen predictions là kỹ thuật chung cho bất kỳ evaluation nào phụ thuộc external service: capture output một lần, replay trong CI.

Evaluation runner nên được thiết kế như pure function: `(dataset, predictor) → report`. Không side effects, không phụ thuộc IO. IO (load file, save report) là trách nhiệm của CLI layer, không phải evaluation core.
