# Query Plan and Tenant Isolation Guide

## Query-Plan Evidence

Use the engine's read-only or safely bounded plan facility appropriate to the environment. `EXPLAIN` may estimate only; `EXPLAIN ANALYZE` or equivalent can execute the statement and requires execution authority, safe parameters, and a non-production target for mutations or expensive reads.

Capture:

- engine/version, schema and statistics revision, representative parameter shape, and plan format;
- estimated versus actual rows at the first material divergence;
- access method, join type/order, filters, rows removed, sorts, memory grants, spills, loops, and elapsed/I/O metrics where available;
- parameter-sensitive behavior and whether the captured plan is reusable or atypical;
- the invariant and workload that an index or query change must preserve.

Common evidence patterns:

- severe estimate error can indicate stale statistics, correlated predicates, skew, or an expression the estimator cannot model;
- a sequential scan is not automatically wrong, especially for small tables or low-selectivity predicates;
- an index seek plus many lookups can cost more than a scan;
- functions, implicit conversions, leading wildcards, or mismatched collations can make a predicate non-sargable;
- adding an index trades read benefit for write, storage, maintenance, and lock cost.

Do not claim improvement from plan shape alone. Compare result correctness and measured behavior under representative parameters.

## Tenant Isolation Mechanics

For shared-table models, evaluate whether tenant identity is part of:

- primary or alternate identity where business identifiers are tenant-local;
- composite foreign keys, so a child cannot reference another tenant's parent;
- unique constraints, so uniqueness scope matches the domain;
- leading or otherwise justified index columns for tenant-scoped access paths;
- every read, write, aggregation, background job, export, and maintenance predicate.

Database row-level security can add defense in depth, but verify policy coverage, owner/bypass roles, session-context setup, connection-pool reset, prepared statements, maintenance paths, and failure behavior. A query filter in an ORM is not by itself a database isolation guarantee.

Use adversarial validation with two synthetic tenants in a non-production environment: attempt cross-tenant inserts, relationship changes, direct-key reads, aggregates, bulk operations, and pooled-connection reuse. Cipher owns the authorization policy; Chronicler owns schema, predicate, key, and row-policy mechanics; Overseer owns the acceptance evidence.
