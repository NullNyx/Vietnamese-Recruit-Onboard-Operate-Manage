# 03 — Landing Page & Open Source Surface

## Mục tiêu

Thiết kế một lớp mặt tiền cho Vroom HR, tách khỏi ứng dụng vận hành:

- **Landing / marketing site** để kể câu chuyện sản phẩm, tạo trust, và dẫn người xem vào demo, docs, hoặc self-host.
- **Open-source repo surface** để hỗ trợ người dùng kỹ thuật, contributor, và self-host installer.

## Foundation liên quan

- `docs/project/foundation/01-product-statement.md`
- `docs/project/foundation/02-target-user-personas.md`
- `docs/project/foundation/03-user-journey.md`
- `docs/project/foundation/08-deployment-trust-security-principles.md`
- `docs/project/foundation/10-open-source-strategy.md`
- `docs/project/changes/00-file-lifecycle.md`

## Trạng thái hiện tại

- Vroom HR có app vận hành và README repo cơ bản.
- Chưa có landing site riêng kiểu `plane.so`.
- Repo GitHub chưa được tối ưu như một open-source front door: thiếu narrative, screenshots, setup story, trust story, và CTA rõ ràng.
- Không có separation rõ giữa:
  - marketing surface
  - product app
  - repo / docs surface

## Trạng thái mong muốn

- Có một landing site public cho Vroom HR.
- Có một repo surface gọn, dễ đọc, hướng tới self-host + contributor.
- Mỗi surface có nhiệm vụ riêng:
  - **Landing**: explain, persuade, capture interest.
  - **Repo**: install, inspect, contribute, verify.
  - **App**: operate the product.

## Hành trình người xem đề xuất

1. **First touch**
   - Người xem vào landing site.
   - Hiểu ngay Vroom HR là gì, dành cho ai, giải quyết vấn đề gì.

2. **Trust build**
   - Thấy self-host, one company per deployment, Google OAuth, audit log, open-source license.

3. **Product story**
   - Thấy backbone flow: Recruit → Onboard → Operate.
   - Thấy product modules, screenshots, and concrete use cases.

4. **Decision points**
   - Người xem chọn: demo, self-host, read docs, or view GitHub.

5. **Repo handoff**
   - Repo dẫn tới setup, architecture, contributing, security, and release notes.

## Landing page IA đề xuất

- Hero
- Problem / why Vroom HR
- Backbone flow overview
- Product pillars (Recruit, Onboard, Operate)
- Self-host + trust section
- Screenshots / product tour
- Open-source section
- Docs / setup / GitHub links
- CTA block
- Footer

## Repo surface yêu cầu tối thiểu

- README rõ ràng, ngắn, dễ scan
- Setup / local dev / deployment guide
- Architecture snapshot
- Screenshots / feature map
- License, security, contributing
- Link sang landing site và docs

## Các bước triển khai

1. Chốt scope và boundary giữa landing site, repo, và app.
2. Thiết kế IA cho landing site.
3. Viết narrative sản phẩm cho hero + backbone flow + trust sections.
4. Cập nhật repo README và docs entry points.
5. Xác định assets cần thiết: screenshot, logo, typography, color, CTA.
6. Giao task cho từng member theo surface.

## Rủi ro / lưu ý

- Không để landing site lấn vào app product surface.
- Không biến README thành landing page full marketing.
- Narrative phải đúng với code thật, tránh hứa quá scope hiện tại.
- Cần giữ nhất quán giữa landing copy, README, và product docs.
- Nếu đổi story hoặc module scope, phải cập nhật lại các surface liên quan.
