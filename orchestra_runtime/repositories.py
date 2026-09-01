"""Compatibility facade for concrete source repositories.

New infrastructure code should import from
``orchestra_runtime.infrastructure.persistence.repositories``. Application and
domain code should depend on ports instead of these concrete implementations.
"""

# ARCHITECTURE_COMPATIBILITY_FACADE
from .infrastructure.persistence.repositories import ManifestRepository, SkillSourceRepository

__all__ = ["ManifestRepository", "SkillSourceRepository"]
