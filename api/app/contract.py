from typing import Any


CONTRACT_VERSION = "v1"


def normalize_contract_response(payload: dict[str, Any]) -> dict[str, Any]:
    """Keep only fields from the stable public response contract."""
    normalized = dict(payload)

    normalized.pop("mode", None)
    normalized.pop("date_filter", None)
    normalized.pop("available_fields", None)
    normalized.pop("upstream_unavailable", None)
    normalized.pop("upstream_error", None)
    normalized.pop("fulltext", None)
    normalized.pop("start_date", None)
    normalized.pop("end_date", None)

    normalized["contract_version"] = CONTRACT_VERSION

    return normalized