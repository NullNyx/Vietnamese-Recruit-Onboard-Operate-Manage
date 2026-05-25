# Docker & WSL2 Environment

## Setup

- Docker Desktop is NOT installed on Windows
- Docker Engine and Docker Compose are installed natively inside WSL2 Ubuntu-24.04
- Project path in WSL: `/home/nullnyx/projects/Vietnamese-Recruit-Onboard-Operate-Manage/`

## Rules

- All Docker commands (`docker`, `docker compose`) MUST be run inside WSL2 Ubuntu
- Use the WSL native project path, not the Windows mount path (`/mnt/c/...`)
- When running docker compose, use: `docker compose -f /home/nullnyx/projects/Vietnamese-Recruit-Onboard-Operate-Manage/docker-compose.infra.yml`
- Any command that depends on Docker (database migrations, seeding, etc.) must also run from WSL

## Infrastructure Services

Defined in `docker-compose.infra.yml`:

- postgres
- redis
- minio
