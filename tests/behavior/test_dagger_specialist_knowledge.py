from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "skills" / "dagger"
CODEX = ROOT / "adapters" / "codex" / "skills" / "dagger"

REQUIRED_SUPPORT = [
    "STRESS_TESTING_FOUNDATIONS_GUIDE.md",
    "SAFETY_GATES.md",
    "TEST_EXECUTION_PROTOCOL.md",
    "FAILURE_MODE_MATRIX.md",
    "RESILIENCE_SCORECARD.md",
    "LOAD_STRESS_WORKLOAD_GUIDE.md",
    "CONCURRENCY_RESOURCE_PRESSURE_GUIDE.md",
    "FAULT_INJECTION_RECOVERY_GUIDE.md",
    "RESILIENCE_TOOLING_EVIDENCE_GUIDE.md",
    "examples/bounded-load-recovery-example.md",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def require(text: str, *needles: str) -> None:
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise AssertionError(f"Missing required Dagger knowledge markers: {missing}")


def main() -> None:
    for relative in REQUIRED_SUPPORT:
        source = SOURCE / relative
        mirror = CODEX / relative
        if not source.is_file():
            raise AssertionError(f"Missing canonical Dagger support file: {relative}")
        if not mirror.is_file():
            raise AssertionError(f"Missing Codex Dagger support file: {relative}")
        if source.read_bytes() != mirror.read_bytes():
            raise AssertionError(f"Dagger source/Codex support parity failed: {relative}")

    workload = read(SOURCE / "LOAD_STRESS_WORKLOAD_GUIDE.md")
    require(
        workload,
        "open arrival rate",
        "closed active-user population",
        "warm-up",
        "steady-state",
        "coordinated omission",
        "generator saturation",
        "latency histogram",
        "Planning stays `PLANNING_ONLY`",
    )

    concurrency = read(SOURCE / "CONCURRENCY_RESOURCE_PRESSURE_GUIDE.md")
    require(
        concurrency,
        "lost update",
        "duplicate effect",
        "idempotency keys",
        "deterministic coordination",
        "| Connections |",
        "Queue",
        "Stop at the first approved threshold",
        "residual state",
    )

    fault = read(SOURCE / "FAULT_INJECTION_RECOVERY_GUIDE.md")
    require(
        fault,
        "Fault taxonomy",
        "retry amplification",
        "RTO",
        "RPO",
        "Reconciliation time",
        "Evidence timeline",
        "keep the scenario planning-only",
    )

    tooling = read(SOURCE / "RESILIENCE_TOOLING_EVIDENCE_GUIDE.md")
    require(
        tooling,
        "Load generator",
        "Network fault proxy",
        "command/config hash",
        "generator saturation",
        "`PLANNED`",
        "`PASS_FOR_TESTED_ENVELOPE`",
        "does not authorize installing or running it",
    )

    safety = read(SOURCE / "SAFETY_GATES.md")
    require(
        safety,
        "Production connectivity blocked or explicitly isolated",
        "Workload or fault ceiling",
        "Load-generator health monitored separately",
        "Abort control tested",
        "Unknown telemetry or an untested abort path blocks execution",
    )

    protocol = read(SOURCE / "TEST_EXECUTION_PROTOCOL.md")
    require(
        protocol,
        "single failure hypothesis",
        "generator can stop without depending on the impaired target",
        "Approval for one scenario does not authorize the next escalation",
        "configuration hash",
        "Never report an average alone",
        "Continue observation through the recovery window",
    )

    skill = read(SOURCE / "SKILL.md")
    for filename in [
        "LOAD_STRESS_WORKLOAD_GUIDE.md",
        "CONCURRENCY_RESOURCE_PRESSURE_GUIDE.md",
        "FAULT_INJECTION_RECOVERY_GUIDE.md",
        "RESILIENCE_TOOLING_EVIDENCE_GUIDE.md",
        "SAFETY_GATES.md",
        "TEST_EXECUTION_PROTOCOL.md",
    ]:
        if filename not in skill:
            raise AssertionError(f"Dagger progressive disclosure does not reference {filename}")
    require(
        skill,
        "Knowledge work alone does not satisfy the execution gate",
        "planning patterns, not standing commands to run",
        "Do not infer permission",
    )

    example = read(SOURCE / "examples" / "bounded-load-recovery-example.md")
    require(
        example,
        "Mode: `PLANNED`; no traffic generated",
        "Open arrival model",
        "Stop conditions",
        "No execution occurred",
        "must not be reported as passed",
    )

    guardrail = read(ROOT / "scripts" / "dagger_guardrail.py")
    require(
        guardrail,
        '"execution_mode": "validation_only"',
        '"live_execution": "blocked"',
        "Phase 2 is simulation-only",
    )

    if (SOURCE / "patterns").exists():
        raise AssertionError("SK5 audit selected Markdown-only depth; unexpected Dagger patterns directory was added")

    print(
        "Dagger specialist knowledge regression passed for "
        f"{len(REQUIRED_SUPPORT)} mirrored support files with live execution still blocked."
    )


if __name__ == "__main__":
    main()
