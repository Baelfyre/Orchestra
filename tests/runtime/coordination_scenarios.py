from __future__ import annotations

from dataclasses import dataclass


class ScenarioContractViolation(ValueError):
    """Raised when a Phase 4 scenario contract is incomplete or contradictory."""


class DuplicateBusinessOperationError(ScenarioContractViolation):
    """Raised when a business operation is repeated outside signal-replay semantics."""


@dataclass(frozen=True, slots=True)
class OwnershipMatrix:
    assignments: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        layers = tuple(layer for layer, _ in self.assignments)
        owners = tuple(owner for _, owner in self.assignments)
        if not self.assignments or any(not layer or not owner for layer, owner in self.assignments):
            raise ScenarioContractViolation("ownership assignments must be non-empty")
        if len(set(layers)) != len(layers):
            raise ScenarioContractViolation("each affected layer requires exactly one accountable owner")
        if "the-tuner" in owners:
            raise ScenarioContractViolation("The Tuner cannot hold scenario ownership")

    def owner_for(self, layer: str) -> str | None:
        return dict(self.assignments).get(layer)

    def require_layers(self, layers: tuple[str, ...]) -> None:
        missing = tuple(layer for layer in layers if self.owner_for(layer) is None)
        if missing:
            raise ScenarioContractViolation(
                f"missing accountable owner for: {','.join(sorted(missing))}"
            )

    def without_layer(self, layer: str) -> OwnershipMatrix:
        return OwnershipMatrix(
            tuple(item for item in self.assignments if item[0] != layer)
        )


@dataclass(frozen=True, slots=True)
class RoutePlan:
    required_specialists: tuple[str, ...]

    def validate(self, selected_specialists: tuple[str, ...]) -> tuple[str, ...]:
        selected = tuple(sorted(set(selected_specialists)))
        required = tuple(sorted(set(self.required_specialists)))
        if selected != required:
            raise ScenarioContractViolation(
                f"route plan requires exactly: {','.join(required)}"
            )
        return selected


@dataclass(frozen=True, slots=True)
class IdempotencyContract:
    owner_ref: str
    operation_key: str
    duplicate_disposition: str

    def validate(self) -> None:
        if not self.owner_ref or not self.operation_key:
            raise ScenarioContractViolation(
                "business idempotency requires an owner and operation key"
            )
        if self.owner_ref == "the-tuner":
            raise ScenarioContractViolation(
                "The Tuner cannot own business idempotency"
            )


class BusinessOperationLedger:
    def __init__(self) -> None:
        self._accepted: set[str] = set()

    def accept(self, operation_identity: str) -> str:
        if operation_identity in self._accepted:
            raise DuplicateBusinessOperationError(operation_identity)
        self._accepted.add(operation_identity)
        return operation_identity


@dataclass(frozen=True, slots=True)
class TransactionOutcome:
    committed_writes: tuple[str, ...]
    rolled_back_writes: tuple[str, ...]
    failed_write: str | None
    partial_success: bool
    failure_evidence_ref: str | None


@dataclass(frozen=True, slots=True)
class TransactionBoundary:
    owner_ref: str
    rollback_required: bool
    partial_success_allowed: bool

    def execute(
        self,
        dependent_writes: tuple[str, ...],
        *,
        fail_after: int | None = None,
        failure_evidence_ref: str | None = None,
    ) -> TransactionOutcome:
        if not self.owner_ref or self.owner_ref == "the-tuner":
            raise ScenarioContractViolation("transaction boundary requires an accountable owner")
        if not dependent_writes:
            raise ScenarioContractViolation("transaction boundary requires dependent writes")
        if fail_after is not None and (fail_after < 0 or fail_after >= len(dependent_writes)):
            raise ScenarioContractViolation("fail_after must identify an existing dependent write")
        if fail_after is not None and not failure_evidence_ref:
            raise ScenarioContractViolation(
                "dependent-write failure requires an evidence reference"
            )

        written: list[str] = []
        for index, write in enumerate(dependent_writes):
            if fail_after is not None and index == fail_after:
                if self.rollback_required:
                    return TransactionOutcome(
                        (),
                        tuple(written),
                        write,
                        False,
                        failure_evidence_ref,
                    )
                if written and not self.partial_success_allowed:
                    raise ScenarioContractViolation(
                        "partial success is prohibited by the transaction contract"
                    )
                return TransactionOutcome(
                    tuple(written),
                    (),
                    write,
                    bool(written),
                    failure_evidence_ref,
                )
            written.append(write)

        return TransactionOutcome(tuple(written), (), None, False, None)


@dataclass(frozen=True, slots=True)
class AuthorizationContract:
    ui_behavior_required: bool
    api_authorization_required: bool

    def validate(
        self,
        *,
        ui_behavior_applied: bool,
        api_authorized: bool,
    ) -> None:
        if self.api_authorization_required and not api_authorized:
            raise ScenarioContractViolation(
                "UI visibility cannot substitute for API authorization"
            )
        if self.ui_behavior_required and not ui_behavior_applied:
            raise ScenarioContractViolation(
                "API authorization cannot substitute for required UI behavior"
            )


@dataclass(frozen=True, slots=True)
class CompatibilityWindow:
    label: str
    minimum_version: int
    maximum_version: int

    def supports(self, version: int) -> bool:
        return self.minimum_version <= version <= self.maximum_version


@dataclass(frozen=True, slots=True)
class MixedVersionContract:
    assumptions: tuple[str, ...]
    client_windows: tuple[CompatibilityWindow, ...]
    application_window: CompatibilityWindow
    schema_window: CompatibilityWindow
    supported_combinations: tuple[tuple[int, int, int], ...]

    def __post_init__(self) -> None:
        if len(self.assumptions) < 2 or any(not item.strip() for item in self.assumptions):
            raise ScenarioContractViolation(
                "mixed-version contract requires explicit old and new client assumptions"
            )
        if not self.client_windows or not self.supported_combinations:
            raise ScenarioContractViolation(
                "mixed-version contract requires client windows and supported combinations"
            )

    def validate_versions(
        self,
        *,
        client_version: int,
        application_version: int,
        schema_version: int,
    ) -> None:
        if not any(window.supports(client_version) for window in self.client_windows):
            raise ScenarioContractViolation("client version is outside the compatibility window")
        if not self.application_window.supports(application_version):
            raise ScenarioContractViolation(
                "application version is outside the compatibility window"
            )
        if not self.schema_window.supports(schema_version):
            raise ScenarioContractViolation("schema version is outside the migration window")
        if (
            client_version,
            application_version,
            schema_version,
        ) not in self.supported_combinations:
            raise ScenarioContractViolation(
                "client, application, and schema versions are contradictory"
            )


@dataclass(frozen=True, slots=True)
class CoordinationScenario:
    scenario_id: str
    title: str
    source_reference: str
    affected_layers: tuple[str, ...]
    required_specialists: tuple[str, ...]
    ownership: OwnershipMatrix
    required_reentry: tuple[str, ...]
    required_review_refs: tuple[str, ...] = ()
    generated_artifact_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    variants: tuple[str, ...] = ()
    route_plan: RoutePlan | None = None
    idempotency_contract: IdempotencyContract | None = None
    transaction_boundary: TransactionBoundary | None = None
    authorization_contract: AuthorizationContract | None = None
    mixed_version_contract: MixedVersionContract | None = None

    def __post_init__(self) -> None:
        self.ownership.require_layers(self.affected_layers)
        if "the-tuner" in self.required_specialists:
            raise ScenarioContractViolation(
                "The Tuner cannot be a required implementation route"
            )

    def owner_for(self, layer: str) -> str | None:
        return self.ownership.owner_for(layer)


SCENARIOS = (
    CoordinationScenario(
        "SCN-01",
        "strict-CSP and initialization-order incident",
        "incident.strict-csp-initialization-order",
        ("architecture", "security", "validation"),
        ("cipher", "clockwork", "overseer"),
        OwnershipMatrix(
            (
                ("architecture", "clockwork"),
                ("security", "cipher"),
                ("validation", "overseer"),
            )
        ),
        ("clockwork", "overseer"),
        required_review_refs=("review.initialization-order",),
        generated_artifact_refs=("artifact.scn01-generated",),
        evidence_refs=(
            "evidence.scn01-generated",
            "evidence.scn01-validation",
        ),
    ),
    CoordinationScenario(
        "SCN-02",
        "simple isolated single-owner bypass",
        "scenario.single-owner-bypass",
        ("execution",),
        ("conductor",),
        OwnershipMatrix((("execution", "conductor"),)),
        (),
        variants=("scribe", "ponytail"),
    ),
    CoordinationScenario(
        "SCN-03",
        "retry duplicate record and idempotency ownership",
        "scenario.retry-idempotency",
        ("persistence", "service", "validation"),
        ("chronicler", "overseer", "ponytail"),
        OwnershipMatrix(
            (
                ("persistence", "chronicler"),
                ("service", "ponytail"),
                ("validation", "overseer"),
            )
        ),
        (),
        idempotency_contract=IdempotencyContract(
            "chronicler",
            "request-identity",
            "reject-duplicate-business-operation",
        ),
    ),
    CoordinationScenario(
        "SCN-04",
        "partial transaction and rollback boundary",
        "scenario.partial-transaction",
        ("persistence", "service", "validation"),
        ("chronicler", "overseer", "ponytail"),
        OwnershipMatrix(
            (
                ("persistence", "chronicler"),
                ("service", "ponytail"),
                ("validation", "overseer"),
            )
        ),
        ("chronicler", "overseer"),
        transaction_boundary=TransactionBoundary(
            "chronicler",
            rollback_required=True,
            partial_success_allowed=False,
        ),
        evidence_refs=(
            "evidence.scn04-dependent-write-failure",
            "evidence.phase3",
        ),
    ),
    CoordinationScenario(
        "SCN-05",
        "UI and API authorization mismatch",
        "scenario.ui-api-authorization",
        ("security", "ui", "validation"),
        ("cipher", "cloak", "overseer"),
        OwnershipMatrix(
            (
                ("security", "cipher"),
                ("ui", "cloak"),
                ("validation", "overseer"),
            )
        ),
        ("cloak", "cipher"),
        route_plan=RoutePlan(("cloak", "cipher")),
        authorization_contract=AuthorizationContract(
            ui_behavior_required=True,
            api_authorization_required=True,
        ),
    ),
    CoordinationScenario(
        "SCN-06",
        "mixed-version migration and stale-contract handling",
        "scenario.mixed-version-migration",
        ("application", "persistence", "validation"),
        ("chronicler", "overseer", "ponytail"),
        OwnershipMatrix(
            (
                ("application", "ponytail"),
                ("persistence", "chronicler"),
                ("validation", "overseer"),
            )
        ),
        ("ponytail", "chronicler", "overseer"),
        mixed_version_contract=MixedVersionContract(
            assumptions=(
                "old clients require the version-one response contract",
                "new clients require the version-two response contract",
            ),
            client_windows=(
                CompatibilityWindow("old-client", 1, 1),
                CompatibilityWindow("new-client", 2, 2),
            ),
            application_window=CompatibilityWindow("application-window", 1, 2),
            schema_window=CompatibilityWindow("migration-window", 1, 2),
            supported_combinations=(
                (1, 1, 1),
                (1, 1, 2),
                (2, 1, 2),
                (2, 2, 2),
            ),
        ),
    ),
)

SCENARIO_BY_ID = {scenario.scenario_id: scenario for scenario in SCENARIOS}
