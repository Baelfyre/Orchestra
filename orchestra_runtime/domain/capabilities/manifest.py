from __future__ import annotations

from dataclasses import dataclass

from ...shared.errors import CapabilityCollisionError, InvalidCapabilityConfigurationError
from ..execution.identity import RunIdentity
from ..governance.authority import AuthorityProvenance
from .core import CapabilityReasonCode, RuntimeCapabilityGrant, _identifier, _text


@dataclass(frozen=True, slots=True)
class RuntimeCapabilityManifest:
    """Immutable run-bound capability manifest owned by the capability domain."""

    manifest_id: str
    run_identity: RunIdentity
    policy_version: str
    grants: tuple[RuntimeCapabilityGrant, ...]
    provenance: AuthorityProvenance

    def __post_init__(self) -> None:
        manifest_id = _identifier(self.manifest_id, "manifest_id")
        grants = tuple(
            sorted(
                tuple(self.grants),
                key=lambda item: (item.capability.capability_id.casefold(), item.capability.capability_id),
            )
        )
        identities = [item.capability.capability_id.casefold() for item in grants]
        if not grants:
            raise InvalidCapabilityConfigurationError(
                "capability manifest requires at least one grant",
                CapabilityReasonCode.INVALID_MANIFEST,
                {"manifest_id": manifest_id},
            )
        if len(set(identities)) != len(identities):
            raise CapabilityCollisionError(
                "capability identities collide",
                CapabilityReasonCode.COLLISION,
                {"manifest_id": manifest_id},
            )
        object.__setattr__(self, "manifest_id", manifest_id)
        object.__setattr__(self, "policy_version", _text(self.policy_version, "policy_version"))
        object.__setattr__(self, "grants", grants)

    def to_dict(self) -> dict[str, object]:
        return {
            "manifest_id": self.manifest_id,
            "run_identity": self.run_identity.to_dict(),
            "policy_version": self.policy_version,
            "grants": [item.to_dict() for item in self.grants],
            "provenance": self.provenance.to_dict(),
        }


__all__ = ["RuntimeCapabilityManifest"]
