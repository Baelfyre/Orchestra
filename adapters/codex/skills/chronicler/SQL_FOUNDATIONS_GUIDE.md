# SQL Foundations Guide

## Purpose
This guide provides token-efficient, practical reference material for Chronicler when handling general SQL tasks. It is designed to aid in query construction, reasoning, report logic, and database operations without over-engineering or deviating from established sources of truth.

## Core SQL Responsibilities
- Construct correct, efficient, and secure SQL queries.
- Validate data models and logic against business requirements.
- Ensure all queries rely only on confirmed schema structures.
- Support accurate database reporting and analytics.

## Query Source of Truth
- **Never invent** tables, columns, relationships, constraints, or report rules.
- **Never invent** business logic at the query layer unless explicitly directed.
- Always trace queries back to the actual schema, migration files, or explicit requirements provided.
- If the schema is unconfirmed, state assumptions clearly before proposing queries.

## SELECT Query Reasoning
- Select only required columns (avoid `SELECT *` in production queries).
- Filter early in the `WHERE` clause to minimize data processed.
- Ensure aliases are clear, descriptive, and consistent.

## Logical Query Order
Keep in mind the engine's evaluation order when designing and reasoning about queries:
1. `FROM` / `JOIN`
2. `WHERE`
3. `GROUP BY`
4. `HAVING`
5. `SELECT`
6. `ORDER BY`
7. `LIMIT` / `OFFSET`

## Joins
- **INNER JOIN**: Default for strict intersections.
- **LEFT JOIN**: For optional relationships. Beware of unexpected row multiplication.
- **RIGHT/FULL JOIN**: Use sparingly and purposefully.
- Always join on explicit, indexed foreign keys or well-defined relational columns.

## Subqueries
- Use subqueries in `WHERE` or `FROM` clauses when CTEs or joins are impractical.
- Prefer `EXISTS` over `IN` for correlated subqueries checking existence.
- Ensure subqueries return the expected cardinality (single vs. multiple rows).

## Common Table Expressions
- Use CTEs (`WITH` clause) for readability, especially for multi-step data transformations.
- Break down complex logic into sequential, named CTEs.
- Be aware of engine-specific CTE materialization behavior.

## SQL Operators
- Use `IN`, `BETWEEN`, `LIKE`, and exact matches (`=`) appropriately.
- Prefer explicit logic over complex nested operators.
- Handle logical operator precedence with clear grouping `()`.

## Aggregation
- Use `COUNT`, `SUM`, `AVG`, `MIN`, `MAX` logically aligned with the `GROUP BY` clause.
- Ensure all non-aggregated `SELECT` columns appear in `GROUP BY`.
- Use `HAVING` to filter on aggregated results, not `WHERE`.

## Window Functions
- Use window functions (`OVER (PARTITION BY ... ORDER BY ...)`) for running totals, rankings (`ROW_NUMBER()`, `RANK()`), and moving averages.
- Window functions preserve row-level detail while calculating aggregates.

## Views
- Propose views to encapsulate complex, frequently used query logic.
- Ensure views do not introduce severe performance degradation (e.g., nested views without materialization).
- Do not use views to hide poor physical schema design.

## Database Reports
- Align report logic precisely with the business definitions of metrics.
- Group and aggregate data cleanly for consumption by presentation layers.
- Avoid placing UI formatting inside report queries; return raw typed data.

## Validation Queries
- Write validation queries to verify constraints, find orphans, or check data integrity.
- Focus on queries that return rows *only* if an invariant is violated.

## Data Integrity
- Ensure `FOREIGN KEY`, `UNIQUE`, and `CHECK` constraints reflect the business logic intended by the queries.
- Do not rely entirely on queries to enforce data integrity; rely on the schema definition.

## Transactions
- Group logically linked mutations (INSERT/UPDATE/DELETE) into atomic transactions.
- Use `BEGIN`, `COMMIT`, and `ROLLBACK` appropriately.
- Minimize transaction duration to reduce lock contention.

## Indexing
- Ensure queries can utilize existing indexes (e.g., matching leftmost prefixes, avoiding functions on indexed columns).
- Propose new indexes only when justified by query plans and access patterns.

## NULL Handling
- Remember that `NULL` propagates. `NULL = NULL` is false; use `IS NULL`.
- Use `COALESCE` or `IFNULL` to handle missing data gracefully.
- Account for `NOT IN` behavior when subqueries might return `NULL`.

## Date and Time Handling
- Standardize on UTC for storage unless strongly dictated otherwise.
- Use explicit date intervals and bounded logic (`>= start AND < end`) over functions on date columns for index safety.

## Security and Privacy Awareness
- Assume all queries operate in a context where data exposure is a risk.
- Do not write queries that inadvertently expose PII or cross tenant boundaries.
- **Route security and privacy policy to Cipher.**

## Engine-Specific Behavior
- Adapt syntax to the target engine (PostgreSQL, MySQL, SQL Server, SQLite, etc.) only when specifically requested.
- Stick to standard ANSI SQL by default.

## Chronicler Output Discipline
- Output concise, correct SQL.
- Provide minimal, targeted explanations.
- **Do not** write bloated essays.

### Routing Notes
If a task touches on domains outside pure persistence and SQL reasoning, follow these routing rules:
- **Diagrams (ERDs, Schema Visuals):** Route to Weaver.
- **Documentation Prose:** Route to Scribe.
- **Testing Strategy:** Route to Overseer.
- **Security and Privacy Policy:** Route to Cipher.
- **Implementation or Execution:** Route to Ponytail when appropriate.
