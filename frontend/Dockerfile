FROM node:22-slim AS base

ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable

# Build dependencies for native modules (sharp, protobufjs, @google/genai, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 make g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency files
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./

# Install dependencies (allowBuilds in pnpm-workspace.yaml controls native builds)
RUN pnpm install --frozen-lockfile

# Copy application code
COPY . .

# Build for production
RUN pnpm build

EXPOSE 3000

ENV HOSTNAME="0.0.0.0"

CMD ["pnpm", "start"]
