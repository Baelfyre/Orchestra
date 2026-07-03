# Project Profiles

Use only the profile supported by repository evidence. Project names never prove a technology or architecture.

## Java or JavaFX application

Signals include Maven or Gradle files, Java sources, JavaFX dependencies, FXML, controllers, services, repositories, and persistence configuration.

- Route visible screens and interaction to `cloak`.
- Route database semantics to `chronicler` and diagrams to `weaver`.
- Route normal verification and release evidence to `overseer`.
- Route security/privacy evidence to `cipher`; use a scanner separately for source-level findings.
- Recommend `dagger` only for an approved non-production pressure test.

## Web frontend

Signals include package manifests, TypeScript or JavaScript components, browser configuration, styles, and public assets.

- Route UX, accessibility, responsive behavior, forms, and dashboards to `cloak`.
- Use a framework specialist for implementation and `overseer` for test evidence.
- Add `cipher` only when authentication, sensitive data, dependencies, or privacy are in scope.

## AI collaboration platform

Signals include agent orchestration, model providers, workspaces, conversation APIs, authentication, events, or real-time collaboration.

- Resolve architecture and ownership boundaries before implementation.
- Use `cipher` for tenant, prompt, secret, and privacy evidence.
- Use `overseer` for concurrency, cancellation, failure, and regression evidence.
- Use `cloak` for collaboration state and user flows.

## Database project

Signals include schemas, migrations, SQL, seeds, ORM models, database configuration, ERDs, or data dictionaries.

- Use `chronicler` for integrity, constraints, migrations, SQL, and documentation.
- Use `weaver` for ERD notation and presentation.
- Use `cipher` for credentials, access, audit, and sensitive-data review.
- Use `overseer` for migration and constraint verification.

## Documentation project

Signals include README files, reports, design logs, handoffs, user guides, rubrics, or diagram-heavy documentation.

- Use `scribe` for audience, structure, clarity, and factual traceability.
- Use `weaver` for diagrams and a domain specialist to verify technical claims.
- Keep local prompts and agent configuration outside tracked project documentation unless explicitly approved.

## Portfolio or product presentation

Signals include public project pages, demonstrations, product screenshots, responsive layouts, and deployment metadata.

- Use `cloak` for task flow, hierarchy, accessibility, and responsive behavior.
- Use `scribe` for accurate project narrative.
- Add specialists only for artifacts that require separate technical validation.
