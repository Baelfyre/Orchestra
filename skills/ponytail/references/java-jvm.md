# Java and JVM Implementation Reference

## Use When

Load this reference only after repository evidence confirms Java or another JVM language. Preserve the configured JDK, Maven/Gradle wrapper, framework version, package layout, nullability conventions, and existing dependency-injection style.

## Core Java

Prefer clear immutable state where practical. Use interfaces and abstractions when they serve an existing boundary, not merely because Java permits them.

```java
public final class NameNormalizer {
    public static String normalize(String value) {
        return value == null ? "" : value.trim();
    }

    private NameNormalizer() {}
}
```

Use `final` where it reflects stable ownership and matches project style. Do not create utility classes for behavior that already belongs to a domain/service object.

## Collections and Optional Values

Program against the collection behavior the project expects. Avoid returning mutable internal collections directly.

Use `Optional` according to project convention, typically for return values representing absence rather than entity fields or every method parameter.

```java
public Optional<User> findById(long id) {
    return repository.findById(id);
}
```

Do not use `Optional.get()` without proving presence.

## Exceptions

- Catch exceptions only where the layer can recover, translate, or add meaningful context.
- Preserve the cause when wrapping.
- Do not use exceptions for ordinary control flow.
- Respect checked/unchecked exception conventions already established by the application.

```java
try {
    return parser.parse(input);
} catch (ParseException ex) {
    throw new ConfigurationException("Invalid configuration", ex);
}
```

## Resource Management

Use try-with-resources for `AutoCloseable` resources.

```java
try (var input = Files.newBufferedReader(path, StandardCharsets.UTF_8)) {
    return input.readLine();
}
```

Preserve transaction and connection ownership defined by the persistence layer.

## Concurrency

Do not add threads, executors, futures, reactive streams, or virtual-thread behavior without confirming the project's runtime and accepted architecture.

When concurrency is already present:
- identify shared mutable state;
- preserve executor ownership;
- propagate interruption where appropriate;
- preserve timeout and cancellation semantics;
- avoid holding locks across external I/O;
- keep retryable effects idempotent.

New concurrency ownership belongs to Clockwork.

## Maven and Gradle

Prefer repository wrappers when present:

```text
./mvnw ...
./gradlew ...
gradlew.bat ...
```

Do not substitute global Maven or Gradle when the wrapper is the project contract. Discover exact goals/tasks from the build file, wrapper, CI, and project docs.

## Spring and Dependency Injection

Confirm the framework and version before using annotations or APIs.

General principles:
- preserve constructor injection when established;
- keep controllers/adapters thin when service boundaries already exist;
- do not move transaction ownership without Chronicler/Clockwork agreement;
- do not weaken method or route authorization owned by Cipher;
- do not add a new bean abstraction for a single call site without an accepted reason.

```java
@Service
public final class AccountService {
    private final AccountRepository repository;

    public AccountService(AccountRepository repository) {
        this.repository = repository;
    }
}
```

## JPA and ORM Boundaries

Chronicler owns schema and persistence semantics. Ponytail may implement an accepted persistence contract.

- Respect entity identity and lifecycle rules.
- Do not expose persistence entities as API contracts when the architecture separates DTO/domain/entity models.
- Avoid accidental lazy-loading assumptions across closed transactions.
- Do not add cascade, orphan-removal, fetch-mode, or transaction changes without understanding their data effects.
- Preserve optimistic locking/version columns where present.

## Testing

Use the existing framework, commonly JUnit in Java repositories, and existing mocking/integration conventions.

```java
@Test
void normalizesWhitespace() {
    assertEquals("Ada", NameNormalizer.normalize("  Ada  "));
}
```

Prefer repository-provided integration harnesses for persistence and framework behavior instead of mocking away the contract being tested.

## Common Failure Patterns

Avoid:
- introducing interfaces with one implementation without an established boundary need;
- field injection when the repository uses constructor injection;
- swallowing `InterruptedException`;
- returning ORM entities through unrelated API layers when DTO separation exists;
- transaction annotations added as trial-and-error fixes;
- changing Java/JDK APIs without confirming the configured target version;
- editing generated sources instead of their generator inputs.
