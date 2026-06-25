# Vroom HR

Open-source HR platform cho doanh nghiệp Việt Nam — self-hosted, một deployment phục vụ một công ty.

## Recruit → Onboard → Manage

Vroom HR tập trung vào backbone flow: **email tuyển dụng → AI classify → CV parse → Candidate → HR review → Interview → Accept → Onboarding → Employee**.

Mỗi bước có audit, mỗi action có boundary rõ.

## Try First, Install Later

**Demo mode available** — thử Vroom HR không cần cài đặt:

1. Truy cập [Vroom HR Landing](https://vroom-hr.example.com/landing)
2. Click **"Dùng thử ngay"** — vào thẳng dashboard với demo session
3. Trải nghiệm recruitment → onboarding → employee flow
4. Thấy ok → click **"Cài đặt cho công ty"** để self-host

Demo yêu cầu backend với `AUTH_DEMO_ENABLED=true`.

## Self-Host Quick Start

```bash
# Clone
git clone https://github.com/NullNyx/Vietnamese-Recruit-Onboard-Operate-Manage.git
cd Vietnamese-Recruit-Onboard-Operate-Manage

# Start all services
docker compose up -d

# Configure (edit backend/.env with your Google OAuth credentials)
# Default: demo mode enabled for testing

# Visit http://localhost:3000/landing
```

## Documentation

| Tài liệu | Mô tả |
| -------- | ----- |
| [CONTEXT.md](./CONTEXT.md) | Domain terms, canonical language |
| [docs/landing/content.md](./docs/landing/content.md) | Landing page content source |
| [docs/project/foundation/](./docs/project/foundation/) | Product strategy, personas, UX tenets |
| [docs/decisions/](./docs/decisions/) | ADRs — architectural decisions |

## Tech Stack

- **Backend**: FastAPI + SQLModel + PostgreSQL + Redis
- **Frontend**: Next.js 14 + TypeScript + Tailwind + shadcn/ui
- **Auth**: Google OAuth2 + JWT (httpOnly cookies)
- **AI**: OpenAI-compatible APIs

## Features

- **Recruitment**: AI email classification, CV parsing, candidate pipeline, interview scheduling
- **Onboarding**: Checklist-driven process, task tracking, completion triggers Employee creation
- **Employee Management**: CRUD, departments, positions, documents
- **AI Assistant**: Read tools + Draft tools, HR confirms before any write
- **Audit**: Every admin action logged

## License

AGPL v3 — see [LICENSE](./LICENSE) for full text.

## Links

- Landing: `http://localhost:3000/landing`
- Demo: `http://localhost:3000/landing` → "Dùng thử ngay"
- Docs: [docs/project/foundation/](./docs/project/foundation/)
- GitHub: https://github.com/NullNyx/Vietnamese-Recruit-Onboard-Operate-Manage
