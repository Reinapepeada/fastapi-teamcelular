import os
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

# Ensure DB config exists before importing project modules that initialize engine.
os.environ.setdefault("DATABASE_URL", "sqlite:///./tests_bootstrap.db")
os.environ.setdefault("LEADS_RATE_LIMIT_REQUESTS", "1000")
os.environ.setdefault("LEADS_RATE_LIMIT_WINDOW_SECONDS", "60")
os.environ.setdefault("LEADS_DEDUPE_WINDOW_SECONDS", "600")
os.environ.setdefault("LEADS_WHATSAPP_NUMBER", "5491112345678")

from database.connection.SQLConection import get_session
from database.models.lead import LeadRepairCreateRequest
from routers.leads_r import router as leads_router
from services.lead_s import get_whatsapp_link, reset_lead_runtime_state_for_tests


@pytest.fixture
def client(tmp_path: Path):
    db_path = tmp_path / "leads_api_test.db"
    engine = create_engine(
        f"sqlite:///{db_path.as_posix()}",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)

    app = FastAPI()
    app.include_router(leads_router)

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    reset_lead_runtime_state_for_tests()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_payload() -> dict:
    return {
        "brand": "Apple",
        "model": "iPhone 13",
        "repairType": "pantalla rota",
        "urgency": "hoy",
        "description": "Pantalla con grietas y sin touch",
        "contactChannel": "whatsapp",
        "contact": "+54 9 11 5555 1234",
        "wizardSource": "budget_wizard_v1",
        "utm": {
            "source": "google",
            "medium": "cpc",
            "campaign": "repair-ads",
        },
        "metadata": {
            "ip": "203.0.113.10",
            "userAgent": "pytest-agent",
            "referrer": "https://example.com/repairs",
        },
    }


def test_unit_whatsapp_link_builder_normalizes_contact_email():
    payload = LeadRepairCreateRequest.model_validate(
        {
            "brand": "Samsung",
            "model": "S22",
            "repairType": "bateria",
            "urgency": "esta_semana",
            "contactChannel": "email",
            "contact": "CLIENTE@MAIL.COM ",
        }
    )

    message, url = get_whatsapp_link(payload)

    assert "Contacto: cliente@mail.com" in message
    assert "https://wa.me/" in url
    assert "Marca%3A%20Samsung" in url


def test_create_lead_and_get_detail(client: TestClient, sample_payload: dict):
    response = client.post("/v1/leads/repair", json=sample_payload)
    assert response.status_code == 201

    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "new"
    assert "wa.me" in body["data"]["whatsappUrl"]

    lead_id = body["data"]["leadId"]
    detail_response = client.get(f"/v1/leads/repair/{lead_id}")
    assert detail_response.status_code == 200

    detail_body = detail_response.json()
    assert detail_body["success"] is True
    assert detail_body["data"]["leadId"] == lead_id
    assert detail_body["data"]["repairType"] == "pantalla rota"


def test_deduplication_marks_second_lead_as_duplicated(client: TestClient, sample_payload: dict):
    first = client.post("/v1/leads/repair", json=sample_payload)
    second = client.post("/v1/leads/repair", json=sample_payload)

    assert first.status_code == 201
    assert second.status_code == 201

    first_body = first.json()["data"]
    second_body = second.json()["data"]

    assert first_body["status"] == "new"
    assert second_body["status"] == "duplicated"
    assert first_body["leadId"] != second_body["leadId"]

    duplicated_detail = client.get(f"/v1/leads/repair/{second_body['leadId']}")
    assert duplicated_detail.status_code == 200
    assert duplicated_detail.json()["data"]["duplicateOf"] == first_body["leadId"]


def test_idempotency_key_returns_same_lead(client: TestClient, sample_payload: dict):
    headers = {"Idempotency-Key": "repair-lead-123"}

    first = client.post("/v1/leads/repair", json=sample_payload, headers=headers)
    second = client.post("/v1/leads/repair", json=sample_payload, headers=headers)

    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["data"]["leadId"] == second.json()["data"]["leadId"]


def test_list_filters_and_status_update_with_history(client: TestClient, sample_payload: dict):
    created = client.post("/v1/leads/repair", json=sample_payload).json()["data"]
    lead_id = created["leadId"]

    update = client.patch(
        f"/v1/leads/repair/{lead_id}/status",
        json={"status": "contacted", "changedBy": "ops-agent"},
    )
    assert update.status_code == 200
    assert update.json()["data"]["newStatus"] == "contacted"

    listing = client.get("/v1/leads/repair", params={"status": "contacted", "page": 1, "size": 10})
    assert listing.status_code == 200
    list_body = listing.json()["data"]
    assert list_body["total"] >= 1
    assert any(item["leadId"] == lead_id for item in list_body["items"])

    detail = client.get(f"/v1/leads/repair/{lead_id}")
    assert detail.status_code == 200
    history = detail.json()["data"]["statusHistory"]
    assert any(item["newStatus"] == "contacted" for item in history)


def test_add_note_to_lead(client: TestClient, sample_payload: dict):
    created = client.post("/v1/leads/repair", json=sample_payload).json()["data"]
    lead_id = created["leadId"]

    note_resp = client.post(
        f"/v1/leads/repair/{lead_id}/notes",
        json={"note": "Cliente pide visita despues de las 18hs", "createdBy": "agent-1"},
    )
    assert note_resp.status_code == 201

    detail = client.get(f"/v1/leads/repair/{lead_id}")
    assert detail.status_code == 200
    notes = detail.json()["data"]["notes"]
    assert len(notes) == 1
    assert notes[0]["createdBy"] == "agent-1"


def test_metrics_endpoint_returns_exact_aggregates(client: TestClient, sample_payload: dict):
    payload_1 = {**sample_payload, "contact": "+5491111111111", "model": "iPhone 13"}
    payload_2 = {
        **sample_payload,
        "contact": "cliente2@example.com",
        "contactChannel": "email",
        "model": "iPhone 14",
    }
    payload_3 = {
        **sample_payload,
        "contact": "5491122222222",
        "contactChannel": "llamada",
        "model": "iPhone 15",
    }

    lead_1 = client.post("/v1/leads/repair", json=payload_1)
    lead_2 = client.post("/v1/leads/repair", json=payload_2)
    lead_3 = client.post("/v1/leads/repair", json=payload_3)
    duplicated = client.post("/v1/leads/repair", json=payload_1)

    assert lead_1.status_code == 201
    assert lead_2.status_code == 201
    assert lead_3.status_code == 201
    assert duplicated.status_code == 201

    lead_1_id = lead_1.json()["data"]["leadId"]
    update_resp = client.patch(
        f"/v1/leads/repair/{lead_1_id}/status",
        json={"status": "converted", "changedBy": "ops-kpi"},
    )
    assert update_resp.status_code == 200

    metrics_resp = client.get("/v1/leads/repair/metrics")
    assert metrics_resp.status_code == 200
    metrics = metrics_resp.json()["data"]

    assert metrics["totalLeads"] == 4
    assert metrics["totalRealLeads"] == 3
    assert metrics["convertedLeads"] == 1
    assert metrics["conversionRate"] == pytest.approx(1 / 3, rel=1e-6)

    by_status = {item["status"]: item["total"] for item in metrics["byStatus"]}
    assert by_status["converted"] == 1
    assert by_status["duplicated"] == 1

    filtered_metrics_resp = client.get(
        "/v1/leads/repair/metrics",
        params={"contactChannel": "email"},
    )
    assert filtered_metrics_resp.status_code == 200
    filtered_metrics = filtered_metrics_resp.json()["data"]

    assert filtered_metrics["totalLeads"] == 1
    assert filtered_metrics["totalRealLeads"] == 1
    assert filtered_metrics["convertedLeads"] == 0
