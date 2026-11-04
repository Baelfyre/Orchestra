# GOV-937 WSL 2 Isolation Feasibility

Disposition: **WSL_QUALIFICATION_CANDIDATE** for further consideration based on bounded synthetic tests. **Cipher and production routing remain NOT_QUALIFIED.** WSL 2 alone is not an isolation boundary; this result applies only to the tested existing Bubblewrap profile.

## Scope and evidence identity

- Inventory was read-only. No WSL feature or package was installed, no elevation or reboot was used, no WSL configuration or distribution settings were changed, and no real-file canary or user data was used.
- Fresh `origin/main`: commit `b215a48b678e8708a8a6e7123f5ee1893d3f4f15`, tree `fac2140e41e81bdf243ddc6c389b38c0453ad28c`.
- PR #981 before this update: branch `JEO/issue-937-r2d-readiness-20261020`, commit `81d0f0ab0328672b22572c75aad14fddaa5f1e7e`, tree `7c17738d9d4195193abafba87436a2ad20dfea8e`. The worktree was clean and ahead-only (5 ahead, 0 behind) in `scripts/preflight_sync_check.py`.
- Preview source instructions were identity-checked at commit `d23fc66accc3f3a52a2ab494e8ce655b42ae57b5`, tree `5aa714e88c0f3e4739e564c4008b2974125cbe34`, clean. This records source verification only, not specialist execution or runtime parity.
- The dedicated WSL feasibility JSON schema was **NOT_FOUND**. The adjacent VM qualification record is related evidence, not a WSL schema. The machine-readable WSL record is structurally valid JSON, without claiming validation against a repository schema.

## Read-only host inventory

| Surface | Observed state |
|---|---|
| Windows | Windows 11 Home Single Language, version `10.0.26300`, build `26300`, 64-bit; current token was not Administrator. |
| WSL | WSL `2.7.11.0`; kernel `6.18.33.2-microsoft-standard-WSL2`; WSLg `1.0.73.2`; default version 2 and default distribution `Ubuntu`. |
| Distributions before inspection | `Ubuntu` (Stopped, WSL 2) and `docker-desktop` (Stopped, WSL 2). The historically mentioned `OrchestraReview` distribution was **NOT_FOUND**. |
| Distribution after probes | `Ubuntu` and `docker-desktop` were both Stopped. No shutdown or terminate command was used. |
| Ubuntu | `Ubuntu 26.04 LTS`, effective UID `1000`. `/mnt/c` and `/mnt/d` were mounted as writable 9p Windows-drive mounts in the ordinary distro context. |
| Windows interop | Enabled in the ordinary distro context through `/proc/sys/fs/binfmt_misc/WSLInterop`. |
| Ordinary process controls | Effective capabilities were zero, `NoNewPrivs=0`, `Seccomp=0`, and `Seccomp_filters=0`. The distro exposed cgroup v2 mounted read-write. |
| Existing isolation tools | Bubblewrap `0.11.1`; util-linux `unshare 2.41.3`. A rootless user/mount/network/PID namespace probe succeeded without configuration changes. |
| Container-runtime inventory | `podman`, `nerdctl`, `runc`, and `crun` were not found. `docker` resolved to a Windows CLI path through interop and was not invoked; the stopped `docker-desktop` distribution was not inspected or activated. |

The ordinary Ubuntu distro is not safe for candidate-only review: it exposes writable `C:\` and `D:\` mounts and Windows interop, with no seccomp or no-new-privileges control by default. A preinstalled rootless Bubblewrap profile was therefore evaluated as a separate process boundary.

## Synthetic Bubblewrap profile

The tested command created a fresh tmpfs root and fresh `/proc` and `/dev`, exposed only read-only system executable/library paths and a synthetic candidate bind-mounted read-only at `/candidate`, cleared the environment, and did not expose `/home`, host drives, WSL integration paths, host sockets, or inherited credentials. `/tmp` and `/run` inside the sandbox were 4 MiB tmpfs mounts. The profile used unshared user, PID, network, and cgroup namespaces; `--disable-userns` plus `--assert-userns-disabled`; dropped all effective capabilities; and ran through `setpriv --no-new-privs` as UID `1000`.

The approved candidate and a separate forbidden canary were synthetic files under one unique WSL `/tmp` scratch directory. Only the candidate directory was mounted into Bubblewrap. The canary content is not recorded. The helper removed only its own scratch directory and verified cleanup.

## Probe results

The first harness attempt stopped at a harness assertion that compared PID namespace IDs from two distinct Bubblewrap invocations. Earlier file-boundary checks had passed and cleanup passed; this was not an observed isolation breach. The corrected helper compared PID 1 and the current process within the same invocation. Its SHA-256 was `8090E61F3D81CAF110B696B175C4DD0E4777DB04937E71295D7E8E5C3D2608B8`.

| Probe | Result | Evidence |
|---|---|---|
| Approved synthetic candidate read | PASS | Exact expected synthetic text was read from `/candidate`. |
| Forbidden synthetic canary read | PASS | The canary was not mounted; read failed. Contents were not emitted. |
| Symlink escape read | PASS | Candidate symlink to the unmounted `/forbidden` path could not be read. |
| Candidate write | PASS | Write through the read-only bind failed; no output file appeared in the candidate fixture. |
| Windows drive and WSL mount paths | PASS | `/mnt/c`, `/mnt/d`, and `/mnt/wsl` were absent in the sandbox. |
| Windows interop visibility | PASS | `/init`, `WSLInterop`, and `cmd.exe` were absent in the sandbox; no Windows executable was launched. |
| PID and network namespace separation | PASS | Sandbox PID namespace `pid:[4026532256]` differed from outer `pid:[4026532221]`; sandbox network namespace `net:[4026532359]` differed from outer `net:[4026531833]`. PID 1 and the current process shared the sandbox PID namespace. |
| Child process inheritance | PASS | A spawned child stayed in the sandbox PID namespace and remained unable to access the unmounted canary and Windows drive paths. |
| Nested user namespace | PASS | A nested `unshare --user --map-root-user` attempt was denied. |
| No-new-privileges and effective capabilities | PASS | `NoNewPrivs=1`; effective capability mask was zero. |
| Network egress | PASS | No non-loopback route was present; a connection attempt to reserved TEST-NET address `192.0.2.1:9` was denied inside the network namespace. The helper did not retain the exact errno. |
| Timeout/cancellation | PASS | `timeout` returned `124` for a sandboxed sleep operation. |
| Scratch cleanup | PASS | The helper's unique `/tmp/orchestra-937-wsl-qual.*` directory was absent after exit. |
| Seccomp syscall filter | BLOCKED | `Seccomp=0`; no filter was active. |
| Cgroup resource limits | BLOCKED | A cgroup namespace was distinct, but no CPU, memory, or PID limits were configured or tested. |
| Denying child-process creation | BLOCKED | The profile allows child creation; only confinement inheritance was demonstrated. |

The corrected helper ran at the exact WSL environment observed above. It did not mount or read the Orchestra repository, access host-sensitive data, call an external model, or invoke Cipher. No actual substantive specialist findings were produced.

## Security disposition and remaining limits

The synthetic evidence supports further review of this preinstalled Bubblewrap mechanism for candidate-only, non-authorizing assessment. It does **not** qualify the Ubuntu distro itself, a hostile-code execution service, the Codex host, Cipher, or production routing. The distinction matters: selected filesystem and network denials were enforced in the explicit test profile, while the distro outside that profile remained host-integrated.

Before any real-host or production Cipher consideration, a separate authorized review must determine whether the missing syscall filtering, CPU/memory/PID limits, child-process policy, and exact candidate-path binding can be satisfied by an independently controlled runner. No such runner was implemented here. If those controls cannot be established, evaluate the tool-less snapshot-only assessment broker; that design is not implemented or activated by this result.

No receipt resolver, validator, policy, whitelist, runtime authority, Cipher route, installed runtime, or production setting changed. PR #977 remains frozen. The R2C human-authority gate remains unchanged. No PR was merged, and no next implementation campaign was started.

The detailed inventory and per-probe machine record is [GOV-937-WSL2-isolation-feasibility-2026-10-21.json](GOV-937-WSL2-isolation-feasibility-2026-10-21.json). The separate [VM isolation qualification](GOV-937-VM-isolation-qualification-2026-10-21.json) remains `BLOCKED_VM_UNAVAILABLE`; this WSL candidate is not VM evidence.
