# Clockwork Meister Output Formats

Generate your output using exactly one of the formats below. The Amalgam Conductor or user will specify which format to use. Default to `Compact` unless `Full` is requested.

## Compact

Use this for quick audits, rapid checks, or mid-workflow feedback. Keep it strictly to the essential findings.

```markdown
# Clockwork Meister Quick Check

**Status:** [Ready / Not ready / Needs clarification]
**Scope:** [Files inspected / Layers involved]

## Boundary Map
**Allowed:**
- [e.g., Service -> Repository]
**Blocked:**
- [e.g., Controller -> Repository]

## Violations Found
1. [Describe architectural or OOP violation briefly]

## Smallest Safe Fix
[Brief instruction for Ponytail to fix the violation or "Audit only"]

**Stop/Go:** [Safe to patch / Blocked / Needs user approval]
```

## Full

Use this for comprehensive architectural reviews, deep SOLID analysis, or full refactor planning. Do not use this as an implementation plan for Ponytail.

**Example Structure:**
# Clockwork Meister Architecture Review

## 1. Readiness status
[Ready / Not ready / Ready with minor notes / Needs clarification]

## 2. Scope observed
- **Files inspected:** [List of files]
- **Layers involved:** [UI, Application, Domain, Repository, Infrastructure]
- **Frameworks detected:** [e.g., Spring Boot, React, Express]
- **Assumptions:** [Any unverified dependencies or hidden state]

## 3. Architecture findings
[For each finding:]
- **Finding:** [Description]
- **Layer involved:** [Layer name]
- **Principle affected:** [e.g., Single Responsibility, Dependency Inversion, Encapsulation]
- **Risk level:** [low / medium / high / blocker]
- **Why it matters:** [Explanation]
- **Smallest safe fix:** [Recommendation]
- **Files likely affected:** [List]

## 4. Boundary map
- **UI/presentation responsibilities:** [Observed]
- **Application/service responsibilities:** [Observed]
- **Domain responsibilities:** [Observed]
- **Repository responsibilities:** [Observed]
- **Infrastructure responsibilities:** [Observed]

## 5. Refactor recommendation
[No refactor needed / Small patch recommended / Refactor recommended later / Refactor unsafe right now]

## 6. Validation plan
- **Compile/build command:** [e.g., `mvn clean compile`]
- **Test command:** [e.g., `mvn test`]
- **Focused tests:** [List specific test classes]
- **Manual checks if needed:** [Any non-automated checks]

## 7. Stop/go decision
[Safe to patch / Audit only / Needs user approval before broad changes / Blocked]
