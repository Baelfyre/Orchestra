# Diagram Notation Guide

## Purpose
This guide provides a token-efficient, practical reference for Weaver to ensure accurate and consistent diagram notation. It establishes standard semantics for connectors, shapes, arrows, and labels across various diagram types.

## Source-of-Truth Rule
- **Never invent** unsupported flows, relationships, multiplicity, cardinality, actors, components, or labels.
- Notation must strictly reflect the provided source of truth.

## Diagram Type Before Notation
- Notation must match the diagram type.
- Do not mix UML semantics with standard flowcharts unless explicitly requested.
- Establish the specific diagram type (e.g., Sequence, Class, Activity, ERD, Architecture) before selecting notation elements.

## Connector Direction
- Arrow direction must convey specific meaning based on context:
  - Control flow
  - Data flow
  - Dependency
  - Call
  - Ownership
  - Inheritance
  - Realization
  - Navigation
  - Message direction

## Arrowhead Semantics
- **Solid arrow**: Denotes normal flow, synchronous call, association, or dependency (depending on diagram type).
- **Dashed arrow**: Denotes dependency, return message, realization, or annotation.
- **Hollow triangle**: Denotes generalization or realization in UML.
- **Return arrows**: Must be used for responses/returns in sequence diagrams.

## Line Type Semantics
- **Solid lines**: Typically represent strong relationships, synchronous communication, or direct structural links.
- **Dashed lines**: Typically represent weak relationships, asynchronous communication, dependencies, or conceptual links.

## Shape Semantics
- **Rectangle**: Process, component, class, object, or system element depending on diagram type.
- **Diamond**: Aggregation or composition in UML class diagrams; decision/branching condition in flowcharts and activity diagrams.
- **Database cylinder**: Represents a data store, not an active process.
- **Actor stick figure / actor node**: Represents an external role, not an internal system component.
- **Rounded rectangle / terminator**: Use for start/end points exclusively in flowchart notation.

## Labels and Guards
- Labels should describe meaning: action, relationship name, guard condition, protocol, multiplicity, cardinality, message, or decision outcome.
- **Decision exits**: Must use clear branch terms (e.g., Yes/No) or guard conditions.
- **Architecture connectors**: Include protocol or interaction type only when confirmed.
- **ERD relationships**: Use relationship names and cardinality only when supported by schema evidence.

## Jump Lines
- Jump lines (line hops) are readability aids only.
- They must not replace proper layout restructuring or diagram splitting.

## Probe Lines and Callouts
- Probe lines or callouts are purely annotations.
- They should never be treated as system relationships, process flows, or structural connectors.

## Layout and Readability
- Keep crossings to a minimum.
- Group logically related elements.
- Maintain consistent spacing and flow direction (e.g., Top-Down or Left-Right).

## ERD Notation
- **Crowâ€™s foot**: Use for relationship cardinality (1:1, 1:N, M:N).
- Display primary keys (PK) and foreign keys (FK) distinctly.

## UML Class Diagram Notation
- Use proper visibility markers (`+` public, `-` private, `#` protected, `~` package).
- Distinguish between composition (filled diamond) and aggregation (hollow diamond).

## UML Sequence Diagram Notation
- Actors initiate the flow.
- Ensure correct use of activation boxes (lifelines).
- Differentiate between synchronous (solid arrow) and asynchronous (open arrow) messages.

## UML Activity Diagram Notation
- Clearly mark Start and End nodes.
- Use synchronization bars (fork/join) for parallel execution paths.

## UML Use Case Diagram Notation
- Keep use cases inside the system boundary.
- Actors remain outside the system boundary.
- Use `<<include>>` and `<<extend>>` correctly for use case relationships.

## Architecture and Component Diagram Notation
- Clearly define boundaries (e.g., trust boundaries, network zones).
- Interfaces should be explicitly modeled (ports/sockets) if required by the architecture depth.

## Deployment Diagram Notation
- Model physical or virtual execution environments (nodes).
- Show artifacts deployed on those nodes.

## Workflow and Flowchart Notation
- Keep flow logic linear and branch conditions explicit.
- Use standard shapes (process, decision, input/output).

## Mermaid and PlantUML Limitations
- Acknowledge that complex layouts may require simplification or splitting if the rendering engine fails to produce a readable graph.
- Prefer semantic correctness over forcing a specific layout engine behavior.

## Notation Review Checklist
- [ ] Does the notation match the declared diagram type?
- [ ] Do the arrow directions make semantic sense?
- [ ] Are all relationships backed by the source of truth?
- [ ] Are labels clear, concise, and accurate?
- [ ] Is the diagram readable without relying excessively on jump lines?

## Weaver Output Discipline
- Focus on producing accurate, parsable diagram code.
- Avoid unnecessary commentary; let the diagram speak for itself.
