"""Machine-local adaptive memory foundation for Orchestra A1.

This package is intentionally not wired into RouterService, RuntimeComposition,
authority, capability, governance, specialist context, or lifecycle activation.
It defines machine-local evidence, profile, privacy, export, deletion, and
recovery contracts only.
"""

from .models import (
    AdaptiveObservation,
    AdaptivePattern,
    AdaptiveProfile,
    AdaptiveScope,
    ADAPTIVE_MEMORY_RULE_VERSION,
    ADAPTIVE_OBSERVATION_SCHEMA_VERSION,
    ADAPTIVE_PROFILE_SCHEMA_VERSION,
    NON_LEARNABLE_SUBJECT_ROOTS,
)
from .observations import (
    append_explicit_preference,
    append_inferred_candidate,
    append_preference_removal,
    append_retrospective_outcome,
)
from .privacy import build_export_bundle, delete_scope, export_bundle, prune_expired
from .profile import materialize_profile
from .store import (
    ADAPTIVE_STORE_LAYOUT_VERSION,
    AdaptiveStoreLayout,
    JsonlAdaptiveStore,
    assert_store_outside_repository,
    default_adaptive_home,
)

__all__ = [
    "AdaptiveObservation",
    "AdaptivePattern",
    "AdaptiveProfile",
    "AdaptiveScope",
    "AdaptiveStoreLayout",
    "JsonlAdaptiveStore",
    "ADAPTIVE_MEMORY_RULE_VERSION",
    "ADAPTIVE_OBSERVATION_SCHEMA_VERSION",
    "ADAPTIVE_PROFILE_SCHEMA_VERSION",
    "ADAPTIVE_STORE_LAYOUT_VERSION",
    "NON_LEARNABLE_SUBJECT_ROOTS",
    "append_explicit_preference",
    "append_inferred_candidate",
    "append_preference_removal",
    "append_retrospective_outcome",
    "assert_store_outside_repository",
    "build_export_bundle",
    "default_adaptive_home",
    "delete_scope",
    "export_bundle",
    "materialize_profile",
    "prune_expired",
]
