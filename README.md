# Vroom HR

Open-source HR platform cho doanh nghiệp Việt Nam — self-hosted, một deployment phục vụ một công ty.

## Recruit → Onboard → Manage

Vroom HR tập trung vào backbone flow: **email tuyển dụng → AI classify → CV parse → Candidate → HR review → Interview → Accept → Onboarding → Employee**.

Mỗi bước có audit, mỗi action có boundary rõ.

## Quick Start

```bash
# Clone
git clone https://github.com/your-org/Vietnamese-Recruit-Onboard-Operate-Manage.git
cd Vietnamese-Recruit-Onboard-Operate-Manage

# Start infrastructure
docker compose up -d postgres redis

# Backend
cd backend
cp .env.example .env
uv sync && uv run alembic upgrade head
uvicorn src.main:app --reload --port 8000

# Frontend
cd ../frontend
cp .env.example .env
pnpm install && pnpm dev
```

Visit `http://localhost:3000` — landing page hiện ra, click "Đăng nhập" để vào demo.

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

AGPL v3 — see [LICENSE]../LICENSE) for full text.

## Links

- Landing page: `http://localhost:3000`
- Demo login: `http://localhost:3000/login`
- Product docs: [docs/project/foundation/](./docs/project/foundation/)
- GitHub: https://github.com/your-org/vroom-hr
