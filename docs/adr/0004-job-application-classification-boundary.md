---
status: accepted
---

# Separate Job Application ingestion from Candidate promotion

Vroom will classify recruitment email using `job_application` rather than the narrower `cv` intent. A Job Application represents one person applying to at most one Job Opening, whether the message has a CV or comes directly, through an employee referral, or from an agency. AI Automation may create Job Applications, but only HR may promote them to Candidate; uncertain messages go to the Recruitment Inbox instead of being discarded or creating Candidate records. This boundary favors recall without allowing uncertain AI output to pollute the Candidate pipeline.

## Considered options

- Keep `cv` as both an email label and the trigger for Candidate creation. Rejected because it misses applications without attachments and conflates ingestion with admission into recruitment.
- Create Candidate immediately for every likely application. Rejected because ambiguous, incomplete, forwarded, and multi-applicant messages would create misleading Candidate records.
- Keep all decisions manual. Rejected because it preserves HR workload and does not address missed applications.

## Consequences

- One source email may yield multiple Job Applications; multiple messages may link to one application when they share a Gmail thread. Outside a thread, linking is proposed and confirmed rather than automatic.
- A Job Application can initially have no Job Opening, but after clarification targets at most one. One person applying to multiple openings has separate applications.
- `job_application` is the single routing intent when a message also has partner, internal, referral, or agency characteristics; those characteristics are stored as source attributes.
- AI-created applications that HR rejects become `dismissed` rather than being deleted, preserving idempotency and evaluation feedback.
- Existing Candidate records are not reconstructed. Migration creates Job Applications only for unresolved legacy `cv` emails that have not produced a Candidate.
