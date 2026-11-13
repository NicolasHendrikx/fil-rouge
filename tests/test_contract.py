"""Le contrat openapi.yml doit être respecté : mêmes routes, mêmes méthodes, mêmes codes."""

from pathlib import Path

import pytest
import yaml

from app.main import app

CONTRACT = Path(__file__).parent.parent / "openapi.yml"
METHODS = {"get", "post", "put", "patch", "delete"}


def operations(spec: dict) -> dict[tuple[str, str], set[str]]:
    """{(méthode, chemin): {codes de réponse}} pour toutes les opérations d'une spec OpenAPI."""
    return {
        (method.upper(), path): set(operation.get("responses", {}))
        for path, item in spec.get("paths", {}).items()
        for method, operation in item.items()
        if method in METHODS
    }


CONTRACT_OPERATIONS = operations(yaml.safe_load(CONTRACT.read_text(encoding="utf-8")))
APP_OPERATIONS = operations(app.openapi())


def test_app_exposes_every_route_of_the_contract():
    assert sorted(CONTRACT_OPERATIONS) == sorted(APP_OPERATIONS)


@pytest.mark.parametrize("operation", sorted(CONTRACT_OPERATIONS), ids=" ".join)
def test_route_declares_the_response_codes_of_the_contract(operation):
    assert APP_OPERATIONS.get(operation) == CONTRACT_OPERATIONS[operation]
