# GOV-937 WSL 2 Bubblewrap Hardening Qualification

Disposition: **`HOST_ARCHITECTURE_NOT_FIT`**. This is a bounded synthetic qualification of a test-only Bubblewrap profile, not host-engine, Cipher, or production evidence. Cipher remains **NOT_QUALIFIED**. No production activation or authority change occurred.

## Evidence identity and scope

- Fresh `origin/main`: commit `b215a48b678e8708a8a6e7123f5ee1893d3f4f15`, tree `fac2140e41e81bdf243ddc6c389b38c0453ad28c`.
- PR #981 before this update: `JEO/issue-937-r2d-readiness-20261020`, commit `93f6bfc88faeb6c9c79c5b1f5ea1b453b3c4c789`, tree `0b8e557900ba3d5b05bee39fc8284828422f24cb`; clean, six commits ahead and zero behind `origin/main`.
- PR #981 is OPEN and draft. Frozen PR #977 remains unchanged.
- Preview source was identity-checked at commit `d23fc66accc3f3a52a2ab494e8ce655b42ae57b5`, tree `5aa714e88c0f3e4739e564c4008b2974125cbe34`, clean. This is source verification only, not live runtime parity.
- The dedicated WSL/Bubblewrap hardening schema is **NOT_FOUND**. The earlier WSL feasibility record is related evidence, not a schema. This record received structural JSON and invariant checks only.
- All boundary probes used fresh synthetic candidate, canary, socket, and scratch fixtures. No repository source, host drives, real user data, credentials, external model, or live Cipher was accessed. The helper and its `/tmp` fixtures are removed after recording.
- No WSL or distribution configuration was changed; no installation, elevation, reboot, shutdown, or termination was used. WSL commands started Ubuntu for the probes; at the final inventory Ubuntu was Running and `docker-desktop` was Stopped.

## Trust boundary observed

```text
Windows Codex host (actual review engine is outside the tested boundary; not run)
  -> ordinary Ubuntu WSL (writable C:/D: 9p mounts and Windows interop; Seccomp=0, NoNewPrivs=0)
    -> manually constructed Bubblewrap test child
       (synthetic candidate only, read-only; fresh tmpfs root; user/PID/network/cgroup namespaces;
        NoNewPrivs=1; zero effective capabilities; seccomp only when the caller supplies its FD;
        file descriptors remain inherited unless the caller closes them)
```

The ordinary distribution is not an isolated assessment host. Only the explicit child profile was tested. The profile is a test harness, not a production launcher, and no evidence establishes that the Windows Codex host launches work through it.

## Q0–Q6 results

| Unit | Result | Observed evidence |
|---|---|---|
| Q0: read-only inventory and scope | **PASS** | Windows 11 Home Single Language build 26300; WSL `2.7.11.0`; kernel `6.18.33.2-microsoft-standard-WSL2`; Ubuntu 26.04, UID 1000; Bubblewrap `0.11.1`; util-linux `2.41.3`. Configuration was not changed. The ordinary distro exposes writable `/mnt/c` and `/mnt/d` 9p mounts and interop. |
| Q1: required seccomp | **FAIL** | A test-only libseccomp filter compiled to 72 BPF bytes (SHA-256 `76d1d0c2e89ae30f1d3fca9529ad8ced888034f6bec58d16d92260a1c8aa709f`) and loaded in Bubblewrap: child `Seccomp=2`, one filter, `getppid` denied with `EPERM`, and `getuid` allowed. An invalid filter FD failed closed before target start. However, omitting `--seccomp` let the target run with `Seccomp=0`, zero filters. There is no required-filter production launcher gate. |
| Q2: resource bounds | **PARTIAL** | Per-process `RLIMIT_AS=512 MiB` rejected a 1 GiB allocation. `RLIMIT_CPU=1 s` terminated `/usr/bin/yes` with exit 137 after 1.11 s, before a 4 s watchdog. Cgroup v2 is mounted read-write, but UID 1000 has no writable delegated child cgroup; current `init.scope` is not writable, `cpu.max=max 100000`, `memory.max=max`, and `pids.max=4282`. Aggregate CPU, memory, and PID quotas were not established. |
| Q3: child-process policy | **FAIL** | At `RLIMIT_NPROC=128`, fork+exec, raw `clone`, and `clone3` were allowed. Limits 8 and 32 prevented Bubblewrap namespace setup with `Resource temporarily unavailable`, so they did not establish a useful child policy. A `vfork` denial probe was **BLOCKED** because no safe compiler/tracer was available. `CHILD_PROCESS_POLICY_UNQUALIFIED`. |
| Q4: descriptor and original isolation checks | **FAIL** | When the parent explicitly passed a synthetic canary FD and synthetic Unix-socket FD, both appeared in the child (two matching descriptors). A separate test-harness invocation using subprocess `close_fds` exposed zero matching descriptors and passed the original synthetic isolation checks. That parent behavior is not proven for the production Codex host. Other test-harness checks passed: approved candidate read; forbidden canary and symlink denial; read-only write denial; no `/mnt/c`, `/mnt/d`, or interop paths in child; PID/network/cgroup namespace separation; nested user namespace denied; `NoNewPrivs=1`, zero effective capabilities; no routes and TEST-NET connection denied (`errno=101`); timeout exit 124 with no later write; unchanged candidate hash and entries; cleanup; two-process `/proc` view. |
| Q5: production-fit decision | **FAIL** | Required controls are not jointly enforced: filter omission permits an unfiltered target, aggregate cgroup limits are unavailable, process creation is allowed, and inherited descriptors cross the boundary unless a caller-specific close-fds behavior is applied. The actual Windows Codex review engine was not run inside this sandbox; no candidate-bound substantive Cipher findings were produced. `HOST_ARCHITECTURE_NOT_FIT`; Cipher remains **NOT_QUALIFIED**. |
| Q6: evidence and local repository validation | **PASS** | This report and its machine record contain observed PASS/FAIL/BLOCKED outcomes, probe and helper digests, limitations, and the decision. Structural JSON/invariant, governance, architecture-boundary, and diff checks passed as listed below. Exact-head hosted checks run after push are reported separately. No dedicated WSL schema was found. |

### Synthetic probe digests

The helper SHA-256 was `37503eb53aa77004b99db9885c2f106a3cbc5d3c8ca42248c0d5d15a244887c3`. The BPF program hash is recorded under Q1. Harness command-argv SHA-256 values:

| Probe | argv SHA-256 |
|---|---|
| Q1 invalid filter FD | `f110d1dde33134fc2d5a50cbc8a7df9dc1a3500fd58c70088f1de54b62892b93` |
| Q1 seccomp filter | `241a4b623c7616a248f0aec4f749980a7045bf964739dc736b41a8819edfe99c` |
| Q2 RLIMIT_AS | `07cd9289b04b434ca0be0ffc00c886e8ba55add7aa9f5c3c7f5e73ce2358471d` |
| Q2 RLIMIT_CPU | `f60e9d8280a98cf01602b5864635c747464d693b0412506f0444befcdac61559` |
| Q3 process policy | `39948476d618e2a736fda617a17a585fef50496df4ab4f30d163715304b45b87` |
| Q4 cancellation | `be87884ee97b631f6ff56fc9a74cb7bab12443d3029cfa9a5f5e5b2c8c2b3a3e` |
| Q4 full and close-fds launcher comparison | `cc50ed0d26df1c25f80aa8d32d26f1c1bf4a87bac829bee2ef01e7edcbaa3596` (same argv; distinct `pass_fds` setup, as machine record notes) |

The synthetic candidate SHA-256 was `6d38d170d592cf4ef2d8c4cc080410c2ad244752be464d90240fe1344136a004`. Canary contents were not recorded. Scratch cleanup returned PASS and verified the temporary fixture path absent.

### Local repository validation

- `git diff --check`: PASS.
- `python scripts/governance_check.py --strict`: PASS, 0 errors and 0 warnings.
- `python scripts/validation/validate_architecture_boundaries.py`: PASS (`RUNTIME_ARCHITECTURE_BOUNDARIES=PASS`).
- JSON parse and invariant checks for this record: PASS; seven ordered Q0–Q6 results, overall disposition `HOST_ARCHITECTURE_NOT_FIT`, and Cipher status `NOT_QUALIFIED`.
- Dedicated WSL hardening schema lookup: NOT_FOUND; validation is structural JSON and task-specific invariants only.
- Full repository test suite: NOT RUN; this documentation-only update does not change runtime code. The Q1–Q4 synthetic host probes are recorded above.

## Security decision and next boundary

This host does not meet the acceptance criterion for further Cipher qualification: a candidate read succeeded, but prohibited operations and resource behavior are not all denied by mandatory, host-enforced controls. The separate test harness's close-fds success does not establish enforcement by the Codex host. No remediation that would install software, change WSL configuration, elevate privileges, or expand authority was attempted.

Do not activate Bubblewrap for production Cipher. A separately authorized evaluation may consider a host-owned, tool-less snapshot-only assessment broker or a separately qualified runner with mandatory seccomp, delegated aggregate quotas, process policy, descriptor closure, and exact server-bound candidate identity. Neither alternative is implemented or approved here. R2C trusted-receipt activation, production Cipher execution, and AlteredEgo Phase 2 authorization remain pending their existing human decisions.

The previous [WSL feasibility record](GOV-937-WSL2-isolation-feasibility-2026-10-21.md) remains as historical baseline; this hardening result supersedes its optimistic `WSL_QUALIFICATION_CANDIDATE` disposition for the tested host architecture.

No protected policy, validator, whitelist, receipt authority, runtime authority, installed runtime, or production setting changed. PR #977 and the GOV-937 decision packet were preserved. No PR was merged.
