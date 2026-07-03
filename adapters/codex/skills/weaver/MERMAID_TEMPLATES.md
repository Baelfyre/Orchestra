# Mermaid Templates

Replace placeholders only with confirmed project facts.

## Class Diagram

```mermaid
classDiagram
    class ClassA {
        +operation()
    }
    class ClassB
    ClassA --> ClassB : confirmed relationship
```

## Use Case Approximation

Mermaid has no native UML use-case syntax. Use a labeled flowchart or choose PlantUML for formal notation.

```mermaid
flowchart LR
    Actor["Actor: Role"]
    subgraph System["System Boundary"]
        UC1([User goal])
    end
    Actor --> UC1
```

## Sequence Diagram

```mermaid
sequenceDiagram
    actor User
    participant UI
    participant Service
    User->>UI: Confirmed action
    UI->>Service: Confirmed request
    Service-->>UI: Confirmed response
    UI-->>User: Visible result
```

## ERD

```mermaid
erDiagram
    ENTITY_A ||--o{ ENTITY_B : confirmed_relationship
    ENTITY_A {
        int id PK
    }
    ENTITY_B {
        int id PK
        int entity_a_id FK
    }
```

## Flowchart

```mermaid
flowchart TD
    Start([Trigger]) --> Action[Confirmed action]
    Action --> Decision{Confirmed condition?}
    Decision -->|Yes| Success([Outcome])
    Decision -->|No| Recovery[Recovery action]
```

## Architecture Diagram

```mermaid
flowchart LR
    Actor[External actor]
    subgraph System[System boundary]
        UI[UI]
        Service[Service]
        Store[(Data store)]
        UI --> Service
        Service --> Store
    end
    Actor --> UI
```

## Deployment Diagram

```mermaid
flowchart TB
    subgraph ClientNode[Client node]
        Client[Client artifact]
    end
    subgraph ServerNode[Server node]
        App[Application artifact]
        DB[(Database)]
        App --> DB
    end
    Client -->|Confirmed protocol| App
```
