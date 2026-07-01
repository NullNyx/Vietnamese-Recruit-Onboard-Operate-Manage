# Vroom HR

Vroom HR is an open-source, self-hosted HR operations platform for Vietnamese
enterprises. Each company runs its own deployment (one database, one server).
This glossary fixes canonical domain terms so the team uses one word per
concept across specs, code, and docs.

## Actor Rule

**HR/Admin** is the sole actor. Every write action is performed by HR/Admin.
No employee-facing actor exists; no employee login or self-service surface.
Employee data provided as input (e.g. leave requests, profile updates) is
entered or imported by HR/Admin, not by the employee.
_Avoid_: Employee, Applicant, User as actor

## Language

**Organization**:
The single company that owns a given deployment. It is a singleton — exactly
one per running instance. Holds company-level settings (name, tax code,
timezone, holidays, allowed email domains). NOT a data-isolation boundary.
_Avoid_: Company, Tenant, Account, Client

**Tenant**:
A legacy term from the Policy Engine, where `tenant_id` was designed as a
multi-company isolation key. In the self-hosted model there is only one
company per deployment, so `tenant_id` is effectively a constant.
_Avoid_: using Tenant as if multiple companies share one deployment

**HR**:
The sole user role. Manages employee records, contracts, documents, and
operations for the Organization. Maps to the existing `admin` role.
_Avoid_: User (User is the auth-account concept)

**Employee**:
A person with an employment record in the system. Employee is the root entity
— all HR operations (contracts, documents, attendance, leave, payroll,
employment events) orbit this record. An Employee is NOT a system user — no
login, no self-service, no write access.
_Avoid_: User, Account, Member

**Employee Record**:
The aggregate of all data attached to one Employee: personal info, employment
status, contracts, documents, employment events. Source of truth for HR
operations. Exactly one record per Employee.
_Avoid_: Profile (too narrow), Staff file

**Employment Status**:
The current state of an Employee's relationship with the Organization.
Values: active / resigned / terminated / suspended. Stored directly on Employee.

**Document**:
A file attached to an Employee record (e.g. CCCD scan, diploma, insurance
card). Status: uploaded / verified / rejected / expired. Uploaded by HR.
_Avoid_: Attachment (too generic)

**Employment Event**:
A recorded change in an Employee's data or status. Types: profile_update,
promotion, transfer, status_change, termination, document_update,
contract_update. Stores before/after snapshot and actor.
_Avoid_: Audit log (audit log is the broader system concept)

**Contract**:
A legal document between the Organization and an Employee (labor contract,
offer letter, NDA). Status: draft / pending_signature / active / expired /
terminated / cancelled. One Employee may have multiple contracts.
_Avoid_: Employment contract (too narrow for NDA/offer)

**Contract Template**:
A reusable template for generating Contract drafts. Has versioning.
Status: active / archived.

**Contract Amendment**:
A supplementary document attached to an active Contract. Status: draft /
pending_signature / signed / cancelled.

## Recruitment (vertical slice 1)

The terms below belong to the Recruitment & Onboarding slice — the first
vertical built on Employee Record as the core module. They remain canonical
within that slice.

**Candidate**:
A person being considered for employment, created (auto or manually) from a
parsed CV. Moves through a pipeline: new → reviewing → interview_scheduled →
accepted/rejected/archived. A Candidate is NOT an Employee.
_Avoid_: Applicant, Employee

**Job Opening**:
A specific hiring need for one Position in the Organization. Its Department is
derived from that Position. It optionally groups Candidates being considered
and tracks target headcount. Lifecycle: draft → open → closed/cancelled.
_Avoid_: Recruitment Plan, Hiring Plan, Vacancy, Requisition

**Backbone Flow**:
The first vertical slice: incoming email → AI intent classification → CV
parsing → Candidate → HR review → interview scheduling → accept →
congratulations email → onboarding. This is slice 1, not the product boundary.
_Avoid_: treating this as the only flow

**Onboarding**:
A checklist-driven process managed by HR, rooted in Onboarding Case. No
Employee record is created automatically during onboarding.
_Avoid_: Promotion, Hiring

**Onboarding Case**:
Root entity for the onboarding process. Status: in_progress → completed /
cancelled. Candidate stays a Candidate until HR closes the case.

**Onboarding Task**:
A single item in an Onboarding Case checklist.
Status: pending / in_progress / completed / blocked.

## AI Capabilities

**AI Automation**:
Background AI tasks that run on an event, with no conversation: email intent
classification, CV parsing, document extraction.
_Avoid_: calling this "the AI Agent"

**AI Assistant**:
A conversational assistant for HR only. It can READ data from Employee Records,
recruitment, and onboarding; DRAFT actions (e.g. compose contract, generate
reminder); and SUMMARIZE data. It never writes — structural safety: no tool
in the LLM's toolset can write to the database. HR confirms every write.
_Avoid_: Chatbot (too generic), Agent (implies autonomous writes)

**AI Agent (autonomous)**:
Hypothetical future capability where AI decides and executes writes on its own.
Explicitly out of scope.
_Avoid_: using "Agent" for the current Assistant

## AI Assistant Internals

**Tool**:
A typed function the AI Assistant can invoke. Exactly two kinds: Read-Tool and
Draft-Tool. The LLM never has a write-capable tool.
_Avoid_: Function, Plugin, Skill

**Read-Tool**:
Executes a real read against existing services, returns live data.
Safe to call freely.
_Avoid_: Query (reserved for command/query layer)

**Draft-Tool**:
Returns a structured Draft Action (action type + params + preview) without
writing. The LLM can only propose; it cannot act.
_Avoid_: Write-tool, Action-tool

**Draft Action**:
The structured proposal returned by a Draft-Tool. HR reviews; on confirm, the
frontend calls the real write endpoint directly (never the LLM).
_Avoid_: Auto-action, Command
