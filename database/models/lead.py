from __future__ import annotations

import re
import uuid
from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field as PydField, field_validator
from sqlalchemy import CheckConstraint
from sqlmodel import Field, SQLModel

from core.timezone import now_argentina_naive

_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")
_MULTI_SPACE_RE = re.compile(r"\s+")
_HTML_TAG_RE = re.compile(r"<[^>]*>")


def sanitize_text(value: str) -> str:
    """Basic payload sanitization for user-provided strings."""
    clean = _CONTROL_CHARS_RE.sub("", value)
    clean = _HTML_TAG_RE.sub("", clean)
    clean = _MULTI_SPACE_RE.sub(" ", clean)
    return clean.strip()


class LeadUrgency(str, Enum):
    HOY = "hoy"
    ESTA_SEMANA = "esta_semana"
    SIN_URGENCIA = "sin_urgencia"


class LeadContactChannel(str, Enum):
    WHATSAPP = "whatsapp"
    LLAMADA = "llamada"
    EMAIL = "email"


class LeadRepairStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    DISCARDED = "discarded"
    CONVERTED = "converted"
    DUPLICATED = "duplicated"


class LeadRepair(SQLModel, table=True):
    __tablename__ = "leads_repair"
    __table_args__ = (
        CheckConstraint(
            "urgency IN ('hoy', 'esta_semana', 'sin_urgencia')",
            name="ck_leads_repair_urgency",
        ),
        CheckConstraint(
            "contact_channel IN ('whatsapp', 'llamada', 'email')",
            name="ck_leads_repair_contact_channel",
        ),
        CheckConstraint(
            "status IN ('new', 'contacted', 'qualified', 'discarded', 'converted', 'duplicated')",
            name="ck_leads_repair_status",
        ),
    )

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    brand: str = Field(nullable=False)
    model: str = Field(nullable=False)
    repair_type: str = Field(nullable=False, index=True)
    urgency: str = Field(nullable=False, index=True)
    description: str | None = Field(default=None, nullable=True)
    contact_channel: str = Field(nullable=False, index=True)
    contact: str | None = Field(default=None, nullable=True)
    lead_attempt_id: str | None = Field(default=None, nullable=True, index=True)
    wizard_source: str | None = Field(default=None, nullable=True)
    status: str = Field(default=LeadRepairStatus.NEW.value, nullable=False, index=True)
    duplicate_of: str | None = Field(default=None, foreign_key="leads_repair.id", index=True)
    fingerprint_hash: str = Field(nullable=False, index=True)
    idempotency_key: str | None = Field(default=None, nullable=True, unique=True, index=True)
    payload_hash: str | None = Field(default=None, nullable=True)

    utm_source: str | None = Field(default=None, nullable=True)
    utm_medium: str | None = Field(default=None, nullable=True)
    utm_campaign: str | None = Field(default=None, nullable=True)
    utm_content: str | None = Field(default=None, nullable=True)
    utm_term: str | None = Field(default=None, nullable=True)

    ip: str | None = Field(default=None, nullable=True)
    user_agent: str | None = Field(default=None, nullable=True)
    referrer: str | None = Field(default=None, nullable=True)

    created_at: datetime = Field(default_factory=now_argentina_naive, index=True)
    updated_at: datetime = Field(
        default_factory=now_argentina_naive,
        sa_column_kwargs={"onupdate": now_argentina_naive},
    )


class LeadInteraction(SQLModel, table=True):
    __tablename__ = "lead_interactions"
    __table_args__ = (
        CheckConstraint("event_name <> ''", name="ck_lead_interactions_event_name"),
    )

    id: int | None = Field(default=None, primary_key=True)
    event_name: str = Field(nullable=False, index=True)
    cta_name: str = Field(nullable=False, index=True)
    cta_location: str = Field(nullable=False, index=True)
    cta_variant: str = Field(nullable=False, index=True)
    destination: str | None = Field(default=None, nullable=True)
    page_path: str = Field(nullable=False, index=True)
    page_title: str | None = Field(default=None, nullable=True)
    lead_id: str | None = Field(default=None, foreign_key="leads_repair.id", nullable=True, index=True)
    lead_attempt_id: str | None = Field(default=None, nullable=True, index=True)
    form_name: str | None = Field(default=None, nullable=True, index=True)
    form_location: str | None = Field(default=None, nullable=True)
    form_version: str | None = Field(default=None, nullable=True)
    interaction_type: str | None = Field(default=None, nullable=True, index=True)
    occurred_at: datetime | None = Field(default=None, nullable=True, index=True)
    step_index: int | None = Field(default=None, nullable=True)
    step_id: str | None = Field(default=None, nullable=True)
    step_label: str | None = Field(default=None, nullable=True)
    total_steps: int | None = Field(default=None, nullable=True)
    brand: str | None = Field(default=None, nullable=True)
    model: str | None = Field(default=None, nullable=True)
    repair_type: str | None = Field(default=None, nullable=True)
    urgency: str | None = Field(default=None, nullable=True)
    contact_channel: str | None = Field(default=None, nullable=True)
    contact: str | None = Field(default=None, nullable=True)
    description: str | None = Field(default=None, nullable=True)
    payload_json: str = Field(nullable=False)
    ip: str | None = Field(default=None, nullable=True)
    user_agent: str | None = Field(default=None, nullable=True)
    referrer: str | None = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=now_argentina_naive, index=True)


class LeadStatusHistory(SQLModel, table=True):
    __tablename__ = "lead_status_history"
    __table_args__ = (
        CheckConstraint(
            "new_status IN ('new', 'contacted', 'qualified', 'discarded', 'converted', 'duplicated')",
            name="ck_lead_status_history_new_status",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    lead_id: str = Field(foreign_key="leads_repair.id", nullable=False, index=True)
    old_status: str | None = Field(default=None, nullable=True)
    new_status: str = Field(nullable=False)
    changed_by: str = Field(default="system", nullable=False)
    changed_at: datetime = Field(default_factory=now_argentina_naive, nullable=False)


class LeadNote(SQLModel, table=True):
    __tablename__ = "lead_notes"

    id: int | None = Field(default=None, primary_key=True)
    lead_id: str = Field(foreign_key="leads_repair.id", nullable=False, index=True)
    note: str = Field(nullable=False)
    created_by: str = Field(default="system", nullable=False)
    created_at: datetime = Field(default_factory=now_argentina_naive, nullable=False)


class LeadUtm(BaseModel):
    source: str | None = PydField(default=None, max_length=120)
    medium: str | None = PydField(default=None, max_length=120)
    campaign: str | None = PydField(default=None, max_length=120)
    content: str | None = PydField(default=None, max_length=120)
    term: str | None = PydField(default=None, max_length=120)

    model_config = ConfigDict(extra="forbid")

    @field_validator("source", "medium", "campaign", "content", "term", mode="before")
    @classmethod
    def sanitize_utm(cls, value: str | None) -> str | None:
        if value is None:
            return None
        clean = sanitize_text(str(value))
        return clean or None


class LeadMetadata(BaseModel):
    ip: str | None = PydField(default=None, max_length=80)
    user_agent: str | None = PydField(default=None, alias="userAgent", max_length=400)
    referrer: str | None = PydField(default=None, max_length=400)

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    @field_validator("ip", "user_agent", "referrer", mode="before")
    @classmethod
    def sanitize_metadata(cls, value: str | None) -> str | None:
        if value is None:
            return None
        clean = sanitize_text(str(value))
        return clean or None


class LeadRepairCreateRequest(BaseModel):
    brand: str = PydField(..., min_length=2, max_length=80)
    model: str = PydField(..., min_length=2, max_length=80)
    repair_type: str = PydField(..., alias="repairType", min_length=2, max_length=120)
    urgency: LeadUrgency
    description: str | None = PydField(default=None, max_length=1000)
    contact_channel: LeadContactChannel = PydField(..., alias="contactChannel")
    contact: str | None = PydField(default=None, max_length=120)
    lead_attempt_id: str | None = PydField(default=None, alias="leadAttemptId", max_length=120)
    wizard_source: str | None = PydField(default=None, alias="wizardSource", max_length=120)
    utm: LeadUtm | None = None
    metadata: LeadMetadata | None = None

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "brand": "Apple",
                "model": "iPhone 13",
                "repairType": "pantalla rota",
                "urgency": "hoy",
                "description": "No responde el touch en mitad de pantalla",
                "contactChannel": "whatsapp",
                "contact": "+5491160011122",
                "leadAttemptId": "lead-attempt-abc123",
                "wizardSource": "budget_wizard_v1",
                "utm": {
                    "source": "google",
                    "medium": "cpc",
                    "campaign": "wizard-repair",
                },
                "metadata": {
                    "ip": "203.0.113.10",
                    "userAgent": "Mozilla/5.0",
                    "referrer": "https://teamcelular.example/form",
                },
            }
        },
    )

    @field_validator("brand", "model", "repair_type", mode="before")
    @classmethod
    def sanitize_required(cls, value: str) -> str:
        clean = sanitize_text(str(value))
        if not clean:
            raise ValueError("must not be empty")
        return clean

    @field_validator("contact", mode="before")
    @classmethod
    def sanitize_contact(cls, value: str | None) -> str | None:
        if value is None:
            return None
        clean = sanitize_text(str(value))
        return clean or None

    @field_validator("description", "lead_attempt_id", "wizard_source", mode="before")
    @classmethod
    def sanitize_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        clean = sanitize_text(str(value))
        return clean or None


class LeadInteractionCreateRequest(BaseModel):
    event_name: str = PydField(..., alias="eventName", min_length=2, max_length=80)
    cta_name: str = PydField(..., alias="ctaName", min_length=2, max_length=120)
    cta_location: str = PydField(..., alias="ctaLocation", min_length=2, max_length=120)
    cta_variant: str = PydField(..., alias="ctaVariant", min_length=2, max_length=40)
    destination: str | None = PydField(default=None, max_length=400)
    page_path: str = PydField(..., alias="pagePath", min_length=1, max_length=400)
    page_title: str | None = PydField(default=None, alias="pageTitle", max_length=200)
    lead_id: str | None = PydField(default=None, alias="leadId", max_length=36)
    lead_attempt_id: str | None = PydField(default=None, alias="leadAttemptId", max_length=120)
    form_name: str | None = PydField(default=None, alias="formName", max_length=80)
    form_location: str | None = PydField(default=None, alias="formLocation", max_length=120)
    form_version: str | None = PydField(default=None, alias="formVersion", max_length=40)
    interaction_type: str | None = PydField(default=None, alias="interactionType", max_length=100)
    occurred_at: datetime | None = PydField(default=None, alias="occurredAt")
    step_index: int | None = PydField(default=None, alias="stepIndex", ge=1)
    step_id: str | None = PydField(default=None, alias="stepId", max_length=80)
    step_label: str | None = PydField(default=None, alias="stepLabel", max_length=80)
    total_steps: int | None = PydField(default=None, alias="totalSteps", ge=1)
    brand: str | None = PydField(default=None, max_length=80)
    model: str | None = PydField(default=None, max_length=80)
    repair_type: str | None = PydField(default=None, alias="repairType", max_length=120)
    urgency: str | None = PydField(default=None, max_length=40)
    contact_channel: str | None = PydField(default=None, alias="contactChannel", max_length=40)
    contact: str | None = PydField(default=None, max_length=120)
    description: str | None = PydField(default=None, max_length=1000)
    metadata: LeadMetadata | None = None

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "eventName": "cta_click",
                "ctaName": "reparaciones_hero_whatsapp",
                "ctaLocation": "reparaciones_hero",
                "ctaVariant": "whatsapp",
                "destination": "https://wa.me/5491151034595?text=Hola",
                "pagePath": "/reparaciones",
                "pageTitle": "Servicios de reparacion de celulares en CABA | Team Celular",
                "leadAttemptId": "lead-attempt-abc123",
                "formName": "repair_budget_wizard",
                "formLocation": "presupuesto_reparacion",
                "formVersion": "v1",
                "stepIndex": 4,
                "stepId": "contact",
                "stepLabel": "Contacto",
                "totalSteps": 4,
                "brand": "Apple",
                "model": "iPhone 13",
                "repairType": "Pantalla",
                "urgency": "hoy",
                "contactChannel": "whatsapp",
                "metadata": {
                    "ip": "203.0.113.10",
                    "userAgent": "Mozilla/5.0",
                    "referrer": "https://teamcelular.example/reparaciones",
                },
            }
        },
    )

    @field_validator(
        "event_name",
        "cta_name",
        "cta_location",
        "cta_variant",
        "page_path",
        mode="before",
    )
    @classmethod
    def sanitize_required_text(cls, value: str) -> str:
        clean = sanitize_text(str(value))
        if not clean:
            raise ValueError("must not be empty")
        return clean

    @field_validator(
        "destination",
        "page_title",
        "lead_id",
        "lead_attempt_id",
        "form_name",
        "form_location",
        "form_version",
        "step_id",
        "step_label",
        "brand",
        "model",
        "repair_type",
        "urgency",
        "contact_channel",
        "contact",
        "description",
        mode="before",
    )
    @classmethod
    def sanitize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        clean = sanitize_text(str(value))
        return clean or None


class LeadStatusUpdateRequest(BaseModel):
    status: LeadRepairStatus
    changed_by: str | None = PydField(default="system", alias="changedBy", max_length=80)

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "status": "contacted",
                "changedBy": "ops-agent-1",
            }
        },
    )

    @field_validator("status")
    @classmethod
    def validate_target_status(cls, value: LeadRepairStatus) -> LeadRepairStatus:
        if value == LeadRepairStatus.DUPLICATED:
            raise ValueError("duplicated cannot be set manually")
        return value

    @field_validator("changed_by", mode="before")
    @classmethod
    def sanitize_changed_by(cls, value: str | None) -> str:
        if value is None:
            return "system"
        clean = sanitize_text(str(value))
        return clean or "system"


class LeadNoteCreateRequest(BaseModel):
    note: str = PydField(..., min_length=2, max_length=2000)
    created_by: str | None = PydField(default="system", alias="createdBy", max_length=80)

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "note": "Cliente pide llamada luego de las 18hs",
                "createdBy": "ops-agent-1",
            }
        },
    )

    @field_validator("note", mode="before")
    @classmethod
    def sanitize_note(cls, value: str) -> str:
        clean = sanitize_text(str(value))
        if not clean:
            raise ValueError("must not be empty")
        return clean

    @field_validator("created_by", mode="before")
    @classmethod
    def sanitize_creator(cls, value: str | None) -> str:
        if value is None:
            return "system"
        clean = sanitize_text(str(value))
        return clean or "system"


class LeadStatusHistoryOut(BaseModel):
    old_status: str | None = PydField(alias="oldStatus")
    new_status: str = PydField(alias="newStatus")
    changed_by: str = PydField(alias="changedBy")
    changed_at: datetime = PydField(alias="changedAt")

    model_config = ConfigDict(populate_by_name=True)


class LeadNoteOut(BaseModel):
    id: int
    note: str
    created_by: str = PydField(alias="createdBy")
    created_at: datetime = PydField(alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)


class LeadRepairOut(BaseModel):
    lead_id: str = PydField(alias="leadId")
    brand: str
    model: str
    repair_type: str = PydField(alias="repairType")
    urgency: LeadUrgency
    description: str | None = None
    contact_channel: LeadContactChannel = PydField(alias="contactChannel")
    contact: str | None = None
    lead_attempt_id: str | None = PydField(default=None, alias="leadAttemptId")
    wizard_source: str | None = PydField(default=None, alias="wizardSource")
    status: str
    duplicate_of: str | None = PydField(default=None, alias="duplicateOf")
    created_at: datetime = PydField(alias="createdAt")
    updated_at: datetime = PydField(alias="updatedAt")
    whatsapp_url: str = PydField(alias="whatsappUrl")
    utm: LeadUtm | None = None
    metadata: LeadMetadata | None = None
    status_history: list[LeadStatusHistoryOut] = PydField(default_factory=list, alias="statusHistory")
    notes: list[LeadNoteOut] = PydField(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


class LeadListData(BaseModel):
    items: list[LeadRepairOut]
    total: int
    page: int
    size: int
    pages: int


class LeadCreateData(BaseModel):
    lead_id: str = PydField(alias="leadId")
    status: str
    created_at: datetime = PydField(alias="createdAt")
    whatsapp_url: str = PydField(alias="whatsappUrl")

    model_config = ConfigDict(populate_by_name=True)


class LeadCreateResponse(BaseModel):
    success: Literal[True] = True
    data: LeadCreateData

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "data": {
                    "leadId": "b8f8036b-65b5-4d74-9d6b-4662678d9748",
                    "status": "new",
                    "createdAt": "2026-04-16T17:05:33.113941",
                    "whatsappUrl": "https://wa.me/5491160011122?text=Hola%21...",
                },
            }
        }
    )


class LeadDetailResponse(BaseModel):
    success: Literal[True] = True
    data: LeadRepairOut


class LeadListResponse(BaseModel):
    success: Literal[True] = True
    data: LeadListData


class LeadInteractionData(BaseModel):
    interaction_id: int = PydField(alias="interactionId")
    created_at: datetime = PydField(alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)


class LeadInteractionResponse(BaseModel):
    success: Literal[True] = True
    data: LeadInteractionData


class LeadInteractionOut(BaseModel):
    interaction_id: int = PydField(alias="interactionId")
    event_name: str = PydField(alias="eventName")
    cta_name: str = PydField(alias="ctaName")
    cta_location: str = PydField(alias="ctaLocation")
    cta_variant: str = PydField(alias="ctaVariant")
    destination: str | None = None
    page_path: str = PydField(alias="pagePath")
    page_title: str | None = PydField(default=None, alias="pageTitle")
    lead_id: str | None = PydField(default=None, alias="leadId")
    lead_attempt_id: str | None = PydField(default=None, alias="leadAttemptId")
    form_name: str | None = PydField(default=None, alias="formName")
    form_location: str | None = PydField(default=None, alias="formLocation")
    form_version: str | None = PydField(default=None, alias="formVersion")
    interaction_type: str | None = PydField(default=None, alias="interactionType")
    occurred_at: datetime | None = PydField(default=None, alias="occurredAt")
    step_index: int | None = PydField(default=None, alias="stepIndex")
    step_id: str | None = PydField(default=None, alias="stepId")
    step_label: str | None = PydField(default=None, alias="stepLabel")
    total_steps: int | None = PydField(default=None, alias="totalSteps")
    brand: str | None = None
    model: str | None = None
    repair_type: str | None = PydField(default=None, alias="repairType")
    urgency: str | None = None
    contact_channel: str | None = PydField(default=None, alias="contactChannel")
    contact: str | None = None
    description: str | None = None
    payload_json: str = PydField(alias="payloadJson")
    ip: str | None = None
    user_agent: str | None = PydField(default=None, alias="userAgent")
    referrer: str | None = None
    created_at: datetime = PydField(alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)


class LeadInteractionListData(BaseModel):
    items: list[LeadInteractionOut]
    total: int
    page: int
    size: int
    pages: int


class LeadInteractionListResponse(BaseModel):
    success: Literal[True] = True
    data: LeadInteractionListData


class LeadInteractionMetricItem(BaseModel):
    key: str
    total: int


class LeadInteractionMetricsData(BaseModel):
    total_interactions: int = PydField(alias="totalInteractions")
    by_event: list[LeadInteractionMetricItem] = PydField(alias="byEvent")
    by_cta_name: list[LeadInteractionMetricItem] = PydField(alias="byCtaName")
    by_cta_variant: list[LeadInteractionMetricItem] = PydField(alias="byCtaVariant")
    by_page: list[LeadInteractionMetricItem] = PydField(alias="byPage")
    by_location: list[LeadInteractionMetricItem] = PydField(alias="byLocation")
    by_date: list[LeadMetricsDateItem] = PydField(alias="byDate")

    model_config = ConfigDict(populate_by_name=True)


class LeadInteractionMetricsResponse(BaseModel):
    success: Literal[True] = True
    data: LeadInteractionMetricsData


class LeadMetricsStatusItem(BaseModel):
    status: str
    total: int


class LeadMetricsChannelItem(BaseModel):
    contact_channel: str = PydField(alias="contactChannel")
    total: int

    model_config = ConfigDict(populate_by_name=True)


class LeadMetricsDateItem(BaseModel):
    date: str
    total: int


class LeadMetricsData(BaseModel):
    total_leads: int = PydField(alias="totalLeads")
    total_real_leads: int = PydField(alias="totalRealLeads")
    converted_leads: int = PydField(alias="convertedLeads")
    conversion_rate: float = PydField(alias="conversionRate")
    by_status: list[LeadMetricsStatusItem] = PydField(alias="byStatus")
    by_contact_channel: list[LeadMetricsChannelItem] = PydField(alias="byContactChannel")
    by_date: list[LeadMetricsDateItem] = PydField(alias="byDate")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "totalLeads": 1240,
                "totalRealLeads": 1180,
                "convertedLeads": 302,
                "conversionRate": 0.255932,
                "byStatus": [
                    {"status": "new", "total": 500},
                    {"status": "contacted", "total": 240},
                    {"status": "qualified", "total": 138},
                    {"status": "converted", "total": 302},
                    {"status": "discarded", "total": 60},
                ],
                "byContactChannel": [
                    {"contactChannel": "whatsapp", "total": 900},
                    {"contactChannel": "llamada", "total": 220},
                    {"contactChannel": "email", "total": 120},
                ],
                "byDate": [
                    {"date": "2026-04-14", "total": 410},
                    {"date": "2026-04-15", "total": 389},
                    {"date": "2026-04-16", "total": 441},
                ],
            }
        },
    )


class LeadMetricsResponse(BaseModel):
    success: Literal[True] = True
    data: LeadMetricsData


class LeadStatusUpdateData(BaseModel):
    lead_id: str = PydField(alias="leadId")
    old_status: str = PydField(alias="oldStatus")
    new_status: str = PydField(alias="newStatus")
    changed_at: datetime = PydField(alias="changedAt")

    model_config = ConfigDict(populate_by_name=True)


class LeadStatusUpdateResponse(BaseModel):
    success: Literal[True] = True
    data: LeadStatusUpdateData


class LeadWhatsappLinkData(BaseModel):
    message: str
    whatsapp_url: str = PydField(alias="whatsappUrl")

    model_config = ConfigDict(populate_by_name=True)


class LeadWhatsappLinkResponse(BaseModel):
    success: Literal[True] = True
    data: LeadWhatsappLinkData


class LeadNoteData(BaseModel):
    lead_id: str = PydField(alias="leadId")
    note_id: int = PydField(alias="noteId")
    created_at: datetime = PydField(alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)


class LeadNoteResponse(BaseModel):
    success: Literal[True] = True
    data: LeadNoteData


class LeadErrorField(BaseModel):
    field: str
    message: str


class LeadErrorResponse(BaseModel):
    success: Literal[False] = False
    error_code: str = PydField(alias="errorCode")
    message: str
    field_errors: list[LeadErrorField] | None = PydField(default=None, alias="fieldErrors")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "success": False,
                "errorCode": "VALIDATION_ERROR",
                "message": "Invalid request payload.",
                "fieldErrors": [
                    {"field": "repairType", "message": "Field required"},
                ],
            }
        },
    )
