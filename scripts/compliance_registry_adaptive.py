from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from orchestra_runtime.registry_adaptive import (
    RegistryAdaptiveError,
    assess_release_delta,
    build_adaptive_receipt,
    evaluate_query_scoped_freshness,
    load_capability_surface,
    negotiate_capabilities,
    resolve_specialists,
    select_query_records,
)
from scripts import compliance_registry


def _values(values: Iterable[str] | None) -> tuple[str, ...]:
    return tuple(sorted(set(value.strip() for value in (values or ()) if value and value.strip())))


def _registry_identity(bundle: compliance_registry.VerifiedBundle) -> dict[str, Any]:
    return {
        "canonical_repository": compliance_registry.CANONICAL_REPOSITORY,
        "registry_version": bundle.manifest["registry_version"],
        "release_sequence": bundle.manifest["release_sequence"],
        "release_tag": bundle.manifest["release_tag"],
        "manifest_sha256": bundle.manifest_sha256,
    }


def capability_status(cache_root: Path) -> dict[str, Any]:
    bundle = compliance_registry._active_bundle(cache_root)
    surface = load_capability_surface(bundle.root, str(bundle.manifest["registry_version"]))
    negotiation = negotiate_capabilities(surface)
    return {
        "registry_identity": _registry_identity(bundle),
        "capability_surface": surface,
        "negotiation": negotiation,
    }


def adaptive_query(
    cache_root: Path,
    *,
    jurisdictions: Iterable[str] | None = None,
    providers: Iterable[str] | None = None,
    domains: Iterable[str] | None = None,
    source_id: str | None = None,
    obligation_id: str | None = None,
) -> dict[str, Any]:
    bundle = compliance_registry._active_bundle(cache_root)
    jurisdiction_ids = _values(jurisdictions)
    provider_ids = _values(providers)
    domain_ids = _values(domains)

    source_document = compliance_registry._json_load(bundle.root / "registry" / "sources.json")
    obligation_document = compliance_registry._json_load(bundle.root / "registry" / "obligations.json")
    source_status_document = compliance_registry._json_load(bundle.root / "registry" / "source-status.json")
    review_due_document = compliance_registry._json_load(bundle.root / "registry" / "review-due.json")
    sources = source_document.get("sources", [])
    obligations = obligation_document.get("obligations", [])
    source_status_entries = source_status_document.get("entries", [])
    review_due_entries = review_due_document.get("entries", [])
    if not isinstance(sources, list) or not all(isinstance(item, dict) for item in sources):
        raise compliance_registry.RegistryError("registry sources store is malformed")
    if not isinstance(obligations, list) or not all(isinstance(item, dict) for item in obligations):
        raise compliance_registry.RegistryError("registry obligations store is malformed")
    if not isinstance(source_status_entries, list) or not all(isinstance(item, dict) for item in source_status_entries):
        raise compliance_registry.RegistryError("registry source-status store is malformed")
    if not isinstance(review_due_entries, list) or not all(isinstance(item, dict) for item in review_due_entries):
        raise compliance_registry.RegistryError("registry review-due store is malformed")

    selected_sources, selected_obligations = select_query_records(
        sources,
        obligations,
        jurisdictions=jurisdiction_ids,
        providers=provider_ids,
        domains=domain_ids,
        source_id=source_id,
        obligation_id=obligation_id,
    )
    source_ids = tuple(sorted(str(item["source_id"]) for item in selected_sources))
    obligation_ids = tuple(sorted(str(item["obligation_id"]) for item in selected_obligations))
    freshness = evaluate_query_scoped_freshness(
        source_ids,
        source_status_entries,
        review_due_entries,
    )
    surface = load_capability_surface(bundle.root, str(bundle.manifest["registry_version"]))
    negotiation = negotiate_capabilities(surface)

    selected_domains: set[str] = set(domain_ids)
    for obligation in selected_obligations:
        values = obligation.get("domains", [])
        if isinstance(values, list):
            selected_domains.update(str(value) for value in values if str(value))
    routing = resolve_specialists(selected_domains)
    filters = {
        "jurisdictions": list(jurisdiction_ids),
        "providers": list(provider_ids),
        "domains": list(domain_ids),
        "source_id": source_id,
        "obligation_id": obligation_id,
    }
    receipt = build_adaptive_receipt(
        registry_identity=_registry_identity(bundle),
        filters=filters,
        source_ids=source_ids,
        obligation_ids=obligation_ids,
        negotiation=negotiation,
        freshness=freshness,
        routing=routing,
    )
    return {
        "registry_version": bundle.manifest["registry_version"],
        "release_sequence": bundle.manifest["release_sequence"],
        "release_tag": bundle.manifest["release_tag"],
        "manifest_sha256": bundle.manifest_sha256,
        "filters": filters,
        "receipt_filters": {
            "jurisdictions": ",".join(jurisdiction_ids),
            "providers": ",".join(provider_ids),
            "domains": ",".join(domain_ids),
            "source_id": source_id or "",
            "obligation_id": obligation_id or "",
        },
        "sources": selected_sources,
        "obligations": selected_obligations,
        "source_ids": list(source_ids),
        "obligation_ids": list(obligation_ids),
        "freshness": freshness,
        "capability_negotiation": negotiation,
        "routing": routing,
        "adaptive_receipt": receipt,
    }


def release_impact(delta_path: Path) -> dict[str, Any]:
    try:
        value = json.loads(delta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryAdaptiveError(f"cannot read release delta: {exc}") from exc
    if not isinstance(value, dict):
        raise RegistryAdaptiveError("release delta must contain a JSON object")
    return assess_release_delta(value)


def _emit(value: dict[str, Any]) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Adaptive consumer for the verified Orchestra Compliance Registry cache.")
    parser.add_argument("--cache-root", help="Override compliance cache root.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("capabilities")
    sub.add_parser("negotiate")
    query = sub.add_parser("query")
    query.add_argument("--jurisdiction", action="append", default=[])
    query.add_argument("--provider", action="append", default=[])
    query.add_argument("--domain", action="append", default=[])
    query.add_argument("--source-id")
    query.add_argument("--obligation-id")
    impact = sub.add_parser("release-impact")
    impact.add_argument("--delta", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cache_root = compliance_registry._cache_root(args.cache_root)
    try:
        if args.command in {"capabilities", "negotiate"}:
            result = capability_status(cache_root)
            _emit(result if args.command == "capabilities" else result["negotiation"])
        elif args.command == "query":
            _emit(
                adaptive_query(
                    cache_root,
                    jurisdictions=args.jurisdiction,
                    providers=args.provider,
                    domains=args.domain,
                    source_id=args.source_id,
                    obligation_id=args.obligation_id,
                )
            )
        elif args.command == "release-impact":
            _emit(release_impact(args.delta.resolve()))
        else:
            raise RegistryAdaptiveError(f"unsupported command: {args.command}")
        return 0
    except (compliance_registry.RegistryError, RegistryAdaptiveError) as exc:
        _emit({"registry_status": "ERROR", "error": str(exc)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
