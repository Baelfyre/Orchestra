# Weaver Quick Diagram Plan

## Diagram Needed
- Sequence diagram for employee update.

## Objective
- Document the confirmed request and persistence order.

## Inputs Required
- Controller, service, repository, and database call path.

## Recommended Format
- Mermaid

## Draft Diagram

```mermaid
sequenceDiagram
    actor HR
    participant UI as Employee Editor
    participant Service as Employee Service
    participant Repo as Employee Repository
    HR->>UI: Submit confirmed changes
    UI->>Service: updateEmployee(data)
    Service->>Repo: update(employee)
    Repo-->>Service: update result
    Service-->>UI: success or validation error
```

## Missing Evidence
- Transaction boundary
- Database failure behavior
- Audit logging behavior
