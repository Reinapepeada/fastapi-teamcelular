from __future__ import annotations

import hashlib
import json
import re
import threading
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import quote

from sqlalchemy import desc, func
from sqlmodel import Session, select

from core.settings import get_settings
from core.timezone import now_argentina_naive, to_argentina_datetime
from database.models.lead import (
    LeadContactChannel,
    LeadInteraction,
    LeadInteractionCreateRequest,
    LeadMetadata,
    LeadNote,
    LeadRepair,
    LeadRepairCreateRequest,
    LeadRepairStatus,
    LeadStatusHistory,
    LeadUtm,
)

_PHONE_CLEAN_RE = re.compile(r"\D+")

_RATE_LIMIT_LOCK = threading.Lock()
_RATE_LIMIT_BUCKETS: dict[str, deque[float]] = defaultdict(deque)


class LeadServiceError(Exception):
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        field_errors: list[dict[str, str]] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.field_errors = field_errors

    def to_detail(self) -> dict[str, Any]:
        detail: dict[str, Any] = {
            "errorCode": self.error_code,
            "message": self.message,
        }
        if self.field_errors:
            detail["fieldErrors"] = self.field_errors
        return detail


@dataclass
class LeadCreateResult:
    lead: LeadRepair
    whatsapp_url: str
    replayed: bool


@dataclass
class LeadStatusUpdateResult:
    lead: LeadRepair
    old_status: str
    new_status: str
    changed_at: datetime


@dataclass
class LeadMetricsResult:
    total_leads: int
    total_real_leads: int
    converted_leads: int
    conversion_rate: float
    by_status: list[dict[str, Any]]
    by_contact_channel: list[dict[str, Any]]
    by_date: list[dict[str, Any]]


@dataclass
class LeadInteractionsResult:
    total_interactions: int
    by_event: list[dict[str, Any]]
    by_cta_name: list[dict[str, Any]]
    by_cta_variant: list[dict[str, Any]]
    by_page: list[dict[str, Any]]
    by_location: list[dict[str, Any]]
    by_date: list[dict[str, Any]]


def reset_lead_runtime_state_for_tests() -> None:
    """Clear in-memory anti-spam state used by rate limiting."""
    with _RATE_LIMIT_LOCK:
        _RATE_LIMIT_BUCKETS.clear()


def _enforce_rate_limit(ip: str, user_agent: str, scope: str = "lead") -> None:
    settings = get_settings()
    max_requests = settings.leads_rate_limit_requests
    window_seconds = settings.leads_rate_limit_window_seconds

    if max_requests <= 0 or window_seconds <= 0:
        return

    now_ts = datetime.now().timestamp()
    key = f"{scope}:{ip}|{user_agent}"

    with _RATE_LIMIT_LOCK:
        bucket = _RATE_LIMIT_BUCKETS[key]
        min_allowed = now_ts - float(window_seconds)
        while bucket and bucket[0] < min_allowed:
            bucket.popleft()

        if len(bucket) >= max_requests:
            raise LeadServiceError(
                status_code=429,
                error_code="RATE_LIMIT_EXCEEDED",
                message="Too many requests from this client. Please try again later.",
            )

        bucket.append(now_ts)


def _normalize_contact(contact: str, contact_channel: LeadContactChannel) -> str:
    clean = contact.strip()

    if contact_channel == LeadContactChannel.EMAIL:
        return clean.lower()

    numeric = _PHONE_CLEAN_RE.sub("", clean)
    if not numeric:
        return clean
    return f"+{numeric}" if clean.startswith("+") else numeric


def _compute_fingerprint_hash(
    brand: str,
    model: str,
    repair_type: str,
    contact: str | None,
) -> str:
    normalized_contact = (contact or "").lower()
    raw = f"{brand.lower()}|{model.lower()}|{repair_type.lower()}|{normalized_contact}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _payload_hash(payload_dict: dict[str, Any]) -> str:
    stable_json = json.dumps(payload_dict, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(stable_json.encode("utf-8")).hexdigest()


def _extract_client_metadata(
    payload_metadata: LeadMetadata | None,
    request_ip: str | None,
    request_user_agent: str | None,
    request_referrer: str | None,
) -> tuple[str, str, str | None]:
    ip = (payload_metadata.ip if payload_metadata else None) or request_ip or "unknown"
    user_agent = (
        (payload_metadata.user_agent if payload_metadata else None)
        or request_user_agent
        or "unknown"
    )
    referrer = (payload_metadata.referrer if payload_metadata else None) or request_referrer
    return ip, user_agent, referrer


def _utm_as_dict(utm: LeadUtm | None) -> dict[str, str | None]:
    if utm is None:
        return {
            "source": None,
            "medium": None,
            "campaign": None,
            "content": None,
            "term": None,
        }
    return {
        "source": utm.source,
        "medium": utm.medium,
        "campaign": utm.campaign,
        "content": utm.content,
        "term": utm.term,
    }


def _urgency_label(value: str) -> str:
    labels = {
        "hoy": "Hoy",
        "esta_semana": "Esta semana",
        "sin_urgencia": "Sin urgencia",
    }
    return labels.get(value, value)


def _channel_label(value: str) -> str:
    labels = {
        "whatsapp": "WhatsApp",
        "llamada": "Llamada",
        "email": "Email",
    }
    return labels.get(value, value)


def build_whatsapp_message(
    *,
    brand: str,
    model: str,
    repair_type: str,
    urgency: str,
    description: str | None,
    contact_channel: str,
    contact: str | None,
) -> str:
    desc = description or "Sin descripcion"
    lines = [
        "Hola! Quiero cotizar una reparacion:",
        f"Marca: {brand}",
        f"Modelo: {model}",
        f"Falla: {repair_type}",
        f"Urgencia: {_urgency_label(urgency)}",
        f"Descripcion: {desc}",
        f"Canal preferido: {_channel_label(contact_channel)}",
    ]
    if contact:
        lines.append(f"Contacto: {contact}")
    return "\n".join(lines)


def build_whatsapp_url(message: str) -> str:
    settings = get_settings()
    base = "https://wa.me"
    phone = settings.leads_whatsapp_number.strip()
    encoded_message = quote(message, safe="")
    if phone:
        return f"{base}/{phone}?text={encoded_message}"
    return f"{base}/?text={encoded_message}"


def _serialize_payload_for_idempotency(
    payload: LeadRepairCreateRequest,
    normalized_contact: str | None,
    ip: str,
    user_agent: str,
    referrer: str | None,
) -> dict[str, Any]:
    utm = _utm_as_dict(payload.utm)
    return {
        "brand": payload.brand,
        "model": payload.model,
        "repairType": payload.repair_type,
        "urgency": payload.urgency.value,
        "description": payload.description,
        "contactChannel": payload.contact_channel.value,
        "contact": normalized_contact,
        "leadAttemptId": payload.lead_attempt_id,
        "wizardSource": payload.wizard_source,
        "utm": utm,
        "metadata": {
            "ip": ip,
            "userAgent": user_agent,
            "referrer": referrer,
        },
    }


def get_whatsapp_link(payload: LeadRepairCreateRequest) -> tuple[str, str]:
    normalized_contact = _normalize_contact(payload.contact or "", payload.contact_channel)
    message = build_whatsapp_message(
        brand=payload.brand,
        model=payload.model,
        repair_type=payload.repair_type,
        urgency=payload.urgency.value,
        description=payload.description,
        contact_channel=payload.contact_channel.value,
        contact=normalized_contact,
    )
    return message, build_whatsapp_url(message)


def create_repair_lead(
    payload: LeadRepairCreateRequest,
    session: Session,
    request_ip: str | None,
    request_user_agent: str | None,
    request_referrer: str | None,
    idempotency_key: str | None,
) -> LeadCreateResult:
    ip, user_agent, referrer = _extract_client_metadata(
        payload_metadata=payload.metadata,
        request_ip=request_ip,
        request_user_agent=request_user_agent,
        request_referrer=request_referrer,
    )
    _enforce_rate_limit(ip=ip, user_agent=user_agent, scope="lead")

    normalized_contact = _normalize_contact(payload.contact or "", payload.contact_channel) or None
    payload_dict = _serialize_payload_for_idempotency(
        payload=payload,
        normalized_contact=normalized_contact,
        ip=ip,
        user_agent=user_agent,
        referrer=referrer,
    )
    payload_hash = _payload_hash(payload_dict)
    fingerprint_hash = _compute_fingerprint_hash(
        brand=payload.brand,
        model=payload.model,
        repair_type=payload.repair_type,
        contact=normalized_contact,
    )

    message = build_whatsapp_message(
        brand=payload.brand,
        model=payload.model,
        repair_type=payload.repair_type,
        urgency=payload.urgency.value,
        description=payload.description,
        contact_channel=payload.contact_channel.value,
        contact=normalized_contact,
    )
    whatsapp_url = build_whatsapp_url(message)

    if idempotency_key:
        existing_by_key = session.exec(
            select(LeadRepair).where(LeadRepair.idempotency_key == idempotency_key)
        ).first()
        if existing_by_key:
            if existing_by_key.payload_hash and existing_by_key.payload_hash != payload_hash:
                raise LeadServiceError(
                    status_code=409,
                    error_code="IDEMPOTENCY_CONFLICT",
                    message="Idempotency-Key was already used with a different payload.",
                )
            return LeadCreateResult(lead=existing_by_key, whatsapp_url=whatsapp_url, replayed=True)

    settings = get_settings()
    now = now_argentina_naive()
    dedupe_threshold = now - timedelta(seconds=settings.leads_dedupe_window_seconds)

    duplicate_target = session.exec(
        select(LeadRepair)
        .where(
            LeadRepair.fingerprint_hash == fingerprint_hash,
            LeadRepair.created_at >= dedupe_threshold,
            LeadRepair.status != LeadRepairStatus.DUPLICATED.value,
        )
        .order_by(desc(LeadRepair.created_at))
    ).first()

    status_value = LeadRepairStatus.NEW.value
    duplicate_of = None
    changed_by = "system"
    if duplicate_target:
        status_value = LeadRepairStatus.DUPLICATED.value
        duplicate_of = duplicate_target.id
        changed_by = "dedupe"

    utm = _utm_as_dict(payload.utm)
    contact_value = normalized_contact or ""
    lead = LeadRepair(
        brand=payload.brand,
        model=payload.model,
        repair_type=payload.repair_type,
        urgency=payload.urgency.value,
        description=payload.description,
        contact_channel=payload.contact_channel.value,
        contact=contact_value,
        lead_attempt_id=payload.lead_attempt_id,
        wizard_source=payload.wizard_source,
        status=status_value,
        duplicate_of=duplicate_of,
        fingerprint_hash=fingerprint_hash,
        idempotency_key=idempotency_key,
        payload_hash=payload_hash,
        utm_source=utm["source"],
        utm_medium=utm["medium"],
        utm_campaign=utm["campaign"],
        utm_content=utm["content"],
        utm_term=utm["term"],
        ip=ip,
        user_agent=user_agent,
        referrer=referrer,
    )

    try:
        session.add(lead)
        session.flush()

        status_history = LeadStatusHistory(
            lead_id=lead.id,
            old_status=None,
            new_status=status_value,
            changed_by=changed_by,
        )
        session.add(status_history)

        session.commit()
        session.refresh(lead)
        return LeadCreateResult(lead=lead, whatsapp_url=whatsapp_url, replayed=False)
    except Exception as exc:
        session.rollback()
        raise LeadServiceError(
            status_code=500,
            error_code="LEAD_CREATE_ERROR",
            message=f"Could not create lead: {exc}",
        ) from exc


def create_lead_interaction(
    payload: LeadInteractionCreateRequest,
    session: Session,
    request_ip: str | None,
    request_user_agent: str | None,
    request_referrer: str | None,
) -> LeadInteraction:
    ip = (payload.metadata.ip if payload.metadata else None) or request_ip or "unknown"
    user_agent = (
        (payload.metadata.user_agent if payload.metadata else None)
        or request_user_agent
        or "unknown"
    )
    referrer = (payload.metadata.referrer if payload.metadata else None) or request_referrer

    _enforce_rate_limit(ip=ip, user_agent=user_agent, scope="interaction")

    payload_data = payload.model_dump(by_alias=True, exclude_none=True)
    payload_data["metadata"] = {
        "ip": ip,
        "userAgent": user_agent,
        "referrer": referrer,
    }

    interaction = LeadInteraction(
        event_name=payload.event_name,
        cta_name=payload.cta_name,
        cta_location=payload.cta_location,
        cta_variant=payload.cta_variant,
        destination=payload.destination,
        page_path=payload.page_path,
        page_title=payload.page_title,
        lead_id=payload.lead_id,
        lead_attempt_id=payload.lead_attempt_id,
        form_name=payload.form_name,
        form_location=payload.form_location,
        form_version=payload.form_version,
        step_index=payload.step_index,
        step_id=payload.step_id,
        step_label=payload.step_label,
        total_steps=payload.total_steps,
        brand=payload.brand,
        model=payload.model,
        repair_type=payload.repair_type,
        urgency=payload.urgency,
        contact_channel=payload.contact_channel,
        contact=payload.contact,
        description=payload.description,
        payload_json=json.dumps(payload_data, sort_keys=True, separators=(",", ":"), ensure_ascii=True),
        ip=ip,
        user_agent=user_agent,
        referrer=referrer,
    )

    try:
        session.add(interaction)
        session.commit()
        session.refresh(interaction)
        return interaction
    except Exception as exc:
        session.rollback()
        raise LeadServiceError(
            status_code=500,
            error_code="LEAD_INTERACTION_CREATE_ERROR",
            message=f"Could not create lead interaction: {exc}",
        ) from exc


def _build_filtered_interactions_query(
    *,
    event_name: str | None,
    cta_variant: str | None,
    cta_location: str | None,
    page_path: str | None,
    lead_attempt_id: str | None,
    date_from: datetime | None,
    date_to: datetime | None,
):
    query = select(LeadInteraction)

    if event_name:
        query = query.where(LeadInteraction.event_name == event_name)
    if cta_variant:
        query = query.where(LeadInteraction.cta_variant == cta_variant)
    if cta_location:
        query = query.where(LeadInteraction.cta_location == cta_location)
    if page_path:
        query = query.where(LeadInteraction.page_path == page_path)
    if lead_attempt_id:
        query = query.where(LeadInteraction.lead_attempt_id == lead_attempt_id)
    if date_from is not None:
        query = query.where(LeadInteraction.created_at >= date_from)
    if date_to is not None:
        query = query.where(LeadInteraction.created_at <= date_to)

    return query


def list_lead_interactions(
    *,
    session: Session,
    event_name: str | None,
    cta_variant: str | None,
    cta_location: str | None,
    page_path: str | None,
    lead_attempt_id: str | None,
    date_from: datetime | None,
    date_to: datetime | None,
    page: int,
    size: int,
) -> tuple[list[LeadInteraction], int]:
    query = _build_filtered_interactions_query(
        event_name=event_name,
        cta_variant=cta_variant,
        cta_location=cta_location,
        page_path=page_path,
        lead_attempt_id=lead_attempt_id,
        date_from=date_from,
        date_to=date_to,
    )

    total_stmt = select(func.count()).select_from(query.order_by(None).subquery())
    total = session.execute(total_stmt).scalar_one()

    rows = session.exec(
        query.order_by(desc(LeadInteraction.created_at)).offset((page - 1) * size).limit(size)
    ).all()
    return rows, int(total)


def get_lead_interactions_metrics(
    *,
    session: Session,
    event_name: str | None,
    cta_variant: str | None,
    cta_location: str | None,
    page_path: str | None,
    lead_attempt_id: str | None,
    date_from: datetime | None,
    date_to: datetime | None,
) -> LeadInteractionsResult:
    filtered_query = _build_filtered_interactions_query(
        event_name=event_name,
        cta_variant=cta_variant,
        cta_location=cta_location,
        page_path=page_path,
        lead_attempt_id=lead_attempt_id,
        date_from=date_from,
        date_to=date_to,
    )
    filtered_subquery = filtered_query.subquery()

    total_interactions = int(
        session.execute(select(func.count()).select_from(filtered_subquery)).scalar_one()
    )

    event_rows = session.execute(
        select(filtered_subquery.c.event_name, func.count().label("total"))
        .group_by(filtered_subquery.c.event_name)
        .order_by(func.count().desc())
    ).all()

    cta_name_rows = session.execute(
        select(filtered_subquery.c.cta_name, func.count().label("total"))
        .group_by(filtered_subquery.c.cta_name)
        .order_by(func.count().desc())
    ).all()

    variant_rows = session.execute(
        select(filtered_subquery.c.cta_variant, func.count().label("total"))
        .group_by(filtered_subquery.c.cta_variant)
        .order_by(func.count().desc())
    ).all()

    page_rows = session.execute(
        select(filtered_subquery.c.page_path, func.count().label("total"))
        .group_by(filtered_subquery.c.page_path)
        .order_by(func.count().desc())
    ).all()

    location_rows = session.execute(
        select(filtered_subquery.c.cta_location, func.count().label("total"))
        .group_by(filtered_subquery.c.cta_location)
        .order_by(func.count().desc())
    ).all()

    date_bucket = func.date(filtered_subquery.c.created_at)
    date_rows = session.execute(
        select(date_bucket.label("bucket_date"), func.count().label("total"))
        .group_by(date_bucket)
        .order_by(date_bucket.asc())
    ).all()

    return LeadInteractionsResult(
        total_interactions=total_interactions,
        by_event=[{"key": str(row[0]), "total": int(row[1])} for row in event_rows],
        by_cta_name=[{"key": str(row[0]), "total": int(row[1])} for row in cta_name_rows],
        by_cta_variant=[{"key": str(row[0]), "total": int(row[1])} for row in variant_rows],
        by_page=[{"key": str(row[0]), "total": int(row[1])} for row in page_rows],
        by_location=[{"key": str(row[0]), "total": int(row[1])} for row in location_rows],
        by_date=[{"date": str(row[0]), "total": int(row[1])} for row in date_rows],
    )


def build_interaction_out(interaction: LeadInteraction) -> dict[str, Any]:
    return {
        "interaction_id": interaction.id,
        "event_name": interaction.event_name,
        "cta_name": interaction.cta_name,
        "cta_location": interaction.cta_location,
        "cta_variant": interaction.cta_variant,
        "destination": interaction.destination,
        "page_path": interaction.page_path,
        "page_title": interaction.page_title,
        "lead_id": interaction.lead_id,
        "lead_attempt_id": interaction.lead_attempt_id,
        "form_name": interaction.form_name,
        "form_location": interaction.form_location,
        "form_version": interaction.form_version,
        "step_index": interaction.step_index,
        "step_id": interaction.step_id,
        "step_label": interaction.step_label,
        "total_steps": interaction.total_steps,
        "brand": interaction.brand,
        "model": interaction.model,
        "repair_type": interaction.repair_type,
        "urgency": interaction.urgency,
        "contact_channel": interaction.contact_channel,
        "contact": interaction.contact,
        "description": interaction.description,
        "payload_json": interaction.payload_json,
        "ip": interaction.ip,
        "user_agent": interaction.user_agent,
        "referrer": interaction.referrer,
        "created_at": to_argentina_datetime(interaction.created_at),
    }


def get_repair_lead_or_404(lead_id: str, session: Session) -> LeadRepair:
    lead = session.get(LeadRepair, lead_id)
    if not lead:
        raise LeadServiceError(
            status_code=404,
            error_code="LEAD_NOT_FOUND",
            message="Lead not found.",
        )
    return lead


def _build_filtered_leads_query(
    *,
    status: LeadRepairStatus | None,
    date_from: datetime | None,
    date_to: datetime | None,
    repair_type: str | None,
    urgency: str | None,
    contact_channel: str | None,
):
    query = select(LeadRepair)

    if status is not None:
        query = query.where(LeadRepair.status == status.value)
    if date_from is not None:
        query = query.where(LeadRepair.created_at >= date_from)
    if date_to is not None:
        query = query.where(LeadRepair.created_at <= date_to)
    if repair_type:
        query = query.where(LeadRepair.repair_type == repair_type)
    if urgency:
        query = query.where(LeadRepair.urgency == urgency)
    if contact_channel:
        query = query.where(LeadRepair.contact_channel == contact_channel)

    return query


def list_repair_leads(
    *,
    session: Session,
    status: LeadRepairStatus | None,
    date_from: datetime | None,
    date_to: datetime | None,
    repair_type: str | None,
    urgency: str | None,
    contact_channel: str | None,
    page: int,
    size: int,
) -> tuple[list[LeadRepair], int]:
    query = _build_filtered_leads_query(
        status=status,
        date_from=date_from,
        date_to=date_to,
        repair_type=repair_type,
        urgency=urgency,
        contact_channel=contact_channel,
    )

    total_stmt = select(func.count()).select_from(query.order_by(None).subquery())
    total = session.execute(total_stmt).scalar_one()

    rows = session.exec(
        query.order_by(desc(LeadRepair.created_at)).offset((page - 1) * size).limit(size)
    ).all()
    return rows, int(total)


def get_repair_leads_metrics(
    *,
    session: Session,
    status: LeadRepairStatus | None,
    date_from: datetime | None,
    date_to: datetime | None,
    repair_type: str | None,
    urgency: str | None,
    contact_channel: str | None,
) -> LeadMetricsResult:
    filtered_query = _build_filtered_leads_query(
        status=status,
        date_from=date_from,
        date_to=date_to,
        repair_type=repair_type,
        urgency=urgency,
        contact_channel=contact_channel,
    )
    filtered_subquery = filtered_query.subquery()

    total_leads = int(session.execute(select(func.count()).select_from(filtered_subquery)).scalar_one())

    total_real_leads = int(
        session.execute(
            select(func.count())
            .select_from(filtered_subquery)
            .where(filtered_subquery.c.status != LeadRepairStatus.DUPLICATED.value)
        ).scalar_one()
    )

    converted_leads = int(
        session.execute(
            select(func.count())
            .select_from(filtered_subquery)
            .where(filtered_subquery.c.status == LeadRepairStatus.CONVERTED.value)
        ).scalar_one()
    )

    conversion_rate = 0.0
    if total_real_leads > 0:
        conversion_rate = round(converted_leads / total_real_leads, 6)

    status_rows = session.execute(
        select(filtered_subquery.c.status, func.count().label("total"))
        .group_by(filtered_subquery.c.status)
        .order_by(func.count().desc())
    ).all()

    channel_rows = session.execute(
        select(filtered_subquery.c.contact_channel, func.count().label("total"))
        .group_by(filtered_subquery.c.contact_channel)
        .order_by(func.count().desc())
    ).all()

    date_bucket = func.date(filtered_subquery.c.created_at)
    date_rows = session.execute(
        select(date_bucket.label("bucket_date"), func.count().label("total"))
        .group_by(date_bucket)
        .order_by(date_bucket.asc())
    ).all()

    return LeadMetricsResult(
        total_leads=total_leads,
        total_real_leads=total_real_leads,
        converted_leads=converted_leads,
        conversion_rate=conversion_rate,
        by_status=[
            {
                "status": str(row[0]),
                "total": int(row[1]),
            }
            for row in status_rows
        ],
        by_contact_channel=[
            {
                "contact_channel": str(row[0]),
                "total": int(row[1]),
            }
            for row in channel_rows
        ],
        by_date=[
            {
                "date": str(row[0]),
                "total": int(row[1]),
            }
            for row in date_rows
        ],
    )


def get_status_history(lead_id: str, session: Session) -> list[LeadStatusHistory]:
    return session.exec(
        select(LeadStatusHistory)
        .where(LeadStatusHistory.lead_id == lead_id)
        .order_by(LeadStatusHistory.changed_at.asc())
    ).all()


def get_notes(lead_id: str, session: Session) -> list[LeadNote]:
    return session.exec(
        select(LeadNote).where(LeadNote.lead_id == lead_id).order_by(LeadNote.created_at.desc())
    ).all()


def update_repair_lead_status(
    lead_id: str,
    new_status: LeadRepairStatus,
    changed_by: str,
    session: Session,
) -> LeadStatusUpdateResult:
    lead = get_repair_lead_or_404(lead_id=lead_id, session=session)

    if lead.status == LeadRepairStatus.DUPLICATED.value:
        raise LeadServiceError(
            status_code=409,
            error_code="DUPLICATED_LEAD_IMMUTABLE",
            message="Duplicated leads cannot change status.",
        )

    old_status = lead.status
    if old_status == new_status.value:
        return LeadStatusUpdateResult(
            lead=lead,
            old_status=old_status,
            new_status=new_status.value,
            changed_at=now_argentina_naive(),
        )

    try:
        lead.status = new_status.value
        lead.updated_at = now_argentina_naive()

        history = LeadStatusHistory(
            lead_id=lead.id,
            old_status=old_status,
            new_status=new_status.value,
            changed_by=changed_by,
        )

        session.add(lead)
        session.add(history)
        session.commit()
        session.refresh(lead)

        return LeadStatusUpdateResult(
            lead=lead,
            old_status=old_status,
            new_status=new_status.value,
            changed_at=history.changed_at,
        )
    except Exception as exc:
        session.rollback()
        raise LeadServiceError(
            status_code=500,
            error_code="LEAD_STATUS_UPDATE_ERROR",
            message=f"Could not update lead status: {exc}",
        ) from exc


def add_repair_lead_note(
    lead_id: str,
    note: str,
    created_by: str,
    session: Session,
) -> LeadNote:
    lead = get_repair_lead_or_404(lead_id=lead_id, session=session)

    new_note = LeadNote(
        lead_id=lead.id,
        note=note,
        created_by=created_by,
    )

    try:
        lead.updated_at = now_argentina_naive()
        session.add(lead)
        session.add(new_note)
        session.commit()
        session.refresh(new_note)
        return new_note
    except Exception as exc:
        session.rollback()
        raise LeadServiceError(
            status_code=500,
            error_code="LEAD_NOTE_CREATE_ERROR",
            message=f"Could not add note: {exc}",
        ) from exc


def build_lead_out(
    lead: LeadRepair,
    *,
    include_history: bool,
    include_notes: bool,
    status_history: list[LeadStatusHistory] | None = None,
    notes: list[LeadNote] | None = None,
) -> dict[str, Any]:
    message = build_whatsapp_message(
        brand=lead.brand,
        model=lead.model,
        repair_type=lead.repair_type,
        urgency=lead.urgency,
        description=lead.description,
        contact_channel=lead.contact_channel,
        contact=lead.contact or "",
    )

    utm_data = {
        "source": lead.utm_source,
        "medium": lead.utm_medium,
        "campaign": lead.utm_campaign,
        "content": lead.utm_content,
        "term": lead.utm_term,
    }
    metadata_data = {
        "ip": lead.ip,
        "user_agent": lead.user_agent,
        "referrer": lead.referrer,
    }

    output: dict[str, Any] = {
        "lead_id": lead.id,
        "brand": lead.brand,
        "model": lead.model,
        "repair_type": lead.repair_type,
        "urgency": lead.urgency,
        "description": lead.description,
        "contact_channel": lead.contact_channel,
        "contact": lead.contact,
        "lead_attempt_id": lead.lead_attempt_id,
        "wizard_source": lead.wizard_source,
        "status": lead.status,
        "duplicate_of": lead.duplicate_of,
        "created_at": to_argentina_datetime(lead.created_at),
        "updated_at": to_argentina_datetime(lead.updated_at),
        "whatsapp_url": build_whatsapp_url(message),
        "utm": utm_data if any(utm_data.values()) else None,
        "metadata": metadata_data if any(metadata_data.values()) else None,
        "status_history": [],
        "notes": [],
    }

    if include_history and status_history is not None:
        output["status_history"] = [
            {
                "old_status": item.old_status,
                "new_status": item.new_status,
                "changed_by": item.changed_by,
                "changed_at": to_argentina_datetime(item.changed_at),
            }
            for item in status_history
        ]

    if include_notes and notes is not None:
        output["notes"] = [
            {
                "id": note.id,
                "note": note.note,
                "created_by": note.created_by,
                "created_at": to_argentina_datetime(note.created_at),
            }
            for note in notes
        ]

    return output
