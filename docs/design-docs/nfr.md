# NFR — Vroom HR

Mục tiêu: chốt non-functional requirements cho MVP theo quality attributes. Không lặp Security / Privacy detail, không lặp Architecture constraints.

## 1. Quality attributes

| Attribute | Target | Measurement |
| --- | --- | --- |
| Performance | Read/list API < 500ms p95; AI draft/summary < 5s | Timing from request to response |
| Reliability | No partial confirm; transient failures do not change entity state | Failed request leaves DB unchanged |
| Availability | Core onboarding functions that do not require AI remain available when AI provider is unavailable | Disable AI provider, verify core edit flows still work |
| Scalability | >= 5 concurrent HR users (target for MVP demo); document storage scales independently from relational database | Multi-user smoke test |
| Usability | Main flows reachable within 3 clicks from Dashboard | UX review / walkthrough |
| Portability | Core onboarding flows remain usable without external AI provider | Disable AI provider and verify core read/edit flows still work |
| Observability | System exposes counts for pending cases, overdue tasks, AI drafts, reminders; application errors traceable using correlation_id | Metrics endpoint / admin view |
| Security | Authentication required; authorization enforced; all client-server communication uses HTTPS/TLS; cross-site forged write requests rejected | Access test / transport check |
| Recoverability | Backup and restore preserve audit integrity; restore must not create orphaned document references | Restore test keeps audit trail intact |
| Compatibility | Supports modern Chromium browsers | Browser smoke test |
| Configurability | Core templates and external providers can be configured without code changes | Add/modify template without deploy

## 2. Attribute detail

### 2.1 Performance

- Read/list API target: < 500ms p95 for typical dataset without AI call
- AI draft / summary target: < 5s p95
- File upload default limit: 10MB configurable
- Dashboard initial load target: < 2s for typical active-case set

### 2.2 Reliability

- Write action must be atomic from HR point of view
- No partial confirm: either draft stays draft or write completes
- Retryable transient failures should not change entity state
- Background jobs should be idempotent

### 2.3 Availability

- Single deployment availability is acceptable for MVP
- Object storage / AI provider failures degrade gracefully
- Read-only operation remains available when AI provider is down

### 2.4 Scalability

- Target >= 5 concurrent HR users for MVP demo / thesis
- Core flows should not rely on shared mutable in-memory state
- Storage growth handled by object storage, not DB blob columns

### 2.5 Usability

- Main flows should be reachable within 3 clicks from Dashboard
- Empty / loading / error states exist on core screens
- AI output clearly labeled as suggestion or draft

### 2.6 Portability

- Self-hosted deployment on one company instance
- Core onboarding flows remain usable without external AI provider
- Config-driven external provider selection when AI is enabled

### 2.7 Observability

- Expose metrics for pending cases
- Expose metrics for overdue tasks
- Expose metrics for AI draft count
- Expose metrics for reminder count
- Important write actions auditable

### 2.8 Security

- Authentication required for all HR actions
- Authorization enforced by role / permission scope
- TLS required for client-server traffic
- Cross-site forged write requests rejected

### 2.9 Recoverability

- System supports backup and restore without losing audit integrity
- Restore process should preserve object references and audit trail

### 2.10 Compatibility

- Target modern Chromium browsers
- No dependency on special browser plugins for core flows

## 3. What is intentionally excluded

The following are design constraints or architecture decisions, not NFR:

- one-way module boundaries
- DTO-only integration contracts
- assistant tool interface shape
- repository access rules

## 4. Next step

Update checklist if needed, then move to Error / exception model.
