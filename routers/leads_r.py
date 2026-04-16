from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Header, HTTPException, Query, Request, Response, status

from database.connection.SQLConection import SessionDep
from database.models.lead import (
    LeadContactChannel,
    LeadCreateData,
    LeadCreateResponse,
    LeadDetailResponse,
    LeadErrorResponse,
    LeadListData,
    LeadListResponse,
    LeadNoteCreateRequest,
    LeadNoteData,
    LeadNoteResponse,
    LeadRepairCreateRequest,
    LeadRepairStatus,
    LeadStatusUpdateRequest,
    LeadStatusUpdateResponse,
    LeadStatusUpdateData,
    LeadUrgency,
    LeadWhatsappLinkData,
    LeadWhatsappLinkResponse,
)
from services.lead_s import (
    LeadServiceError,
    add_repair_lead_note,
    build_lead_out,
    create_repair_lead,
    get_notes,
    get_repair_lead_or_404,
    get_status_history,
    get_whatsapp_link,
    list_repair_leads,
    update_repair_lead_status,
)

router = APIRouter(prefix="/v1/leads", tags=["Repair Leads"])


def _raise_as_http(error: LeadServiceError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.to_detail())


@router.post(
    "/repair",
    response_model=LeadCreateResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": LeadErrorResponse},
        409: {"model": LeadErrorResponse},
        422: {"model": LeadErrorResponse},
        429: {"model": LeadErrorResponse},
    },
)
def create_repair_lead_endpoint(
    payload: LeadRepairCreateRequest,
    request: Request,
    response: Response,
    session: SessionDep,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    """Receive and persist a repair lead from the frontend wizard."""
    try:
        result = create_repair_lead(
            payload=payload,
            session=session,
            request_ip=request.client.host if request.client else None,
            request_user_agent=request.headers.get("user-agent"),
            request_referrer=request.headers.get("referer"),
            idempotency_key=idempotency_key,
        )

        if result.replayed:
            response.status_code = status.HTTP_200_OK

        return {
            "success": True,
            "data": LeadCreateData(
                lead_id=result.lead.id,
                status=result.lead.status,
                created_at=result.lead.created_at,
                whatsapp_url=result.whatsapp_url,
            ),
        }
    except LeadServiceError as err:
        _raise_as_http(err)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "errorCode": "LEAD_CREATE_UNEXPECTED_ERROR",
                "message": f"Unexpected error while creating lead: {exc}",
            },
        ) from exc


@router.post(
    "/repair/whatsapp-link",
    response_model=LeadWhatsappLinkResponse,
    responses={422: {"model": LeadErrorResponse}},
)
def build_repair_whatsapp_link_endpoint(payload: LeadRepairCreateRequest):
    """Build only the WhatsApp message and URL without persisting the lead."""
    try:
        message, whatsapp_url = get_whatsapp_link(payload)
        return {
            "success": True,
            "data": LeadWhatsappLinkData(message=message, whatsapp_url=whatsapp_url),
        }
    except LeadServiceError as err:
        _raise_as_http(err)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "errorCode": "WHATSAPP_LINK_BUILD_ERROR",
                "message": f"Unexpected error while building WhatsApp link: {exc}",
            },
        ) from exc


@router.get(
    "/repair",
    response_model=LeadListResponse,
    responses={400: {"model": LeadErrorResponse}},
)
def list_repair_leads_endpoint(
    session: SessionDep,
    status_filter: LeadRepairStatus | None = Query(default=None, alias="status"),
    date_from: datetime | None = Query(default=None, alias="dateFrom"),
    date_to: datetime | None = Query(default=None, alias="dateTo"),
    repair_type: str | None = Query(default=None, alias="repairType"),
    urgency: LeadUrgency | None = Query(default=None, alias="urgency"),
    contact_channel: LeadContactChannel | None = Query(default=None, alias="contactChannel"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
):
    """Paginated lead listing with operational filters."""
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=400,
            detail={
                "errorCode": "INVALID_DATE_RANGE",
                "message": "dateFrom must be less than or equal to dateTo.",
                "fieldErrors": [
                    {"field": "dateFrom", "message": "Must be <= dateTo"},
                ],
            },
        )

    try:
        rows, total = list_repair_leads(
            session=session,
            status=status_filter,
            date_from=date_from,
            date_to=date_to,
            repair_type=repair_type,
            urgency=urgency.value if urgency else None,
            contact_channel=contact_channel.value if contact_channel else None,
            page=page,
            size=size,
        )

        items = [
            build_lead_out(
                lead=item,
                include_history=False,
                include_notes=False,
            )
            for item in rows
        ]
        pages = (total + size - 1) // size if total > 0 else 0

        return {
            "success": True,
            "data": LeadListData(items=items, total=total, page=page, size=size, pages=pages),
        }
    except LeadServiceError as err:
        _raise_as_http(err)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "errorCode": "LEAD_LIST_UNEXPECTED_ERROR",
                "message": f"Unexpected error while listing leads: {exc}",
            },
        ) from exc


@router.get(
    "/repair/{lead_id}",
    response_model=LeadDetailResponse,
    responses={404: {"model": LeadErrorResponse}},
)
def get_repair_lead_endpoint(lead_id: str, session: SessionDep):
    """Get a lead with status history and internal notes."""
    try:
        lead = get_repair_lead_or_404(lead_id=lead_id, session=session)
        history = get_status_history(lead_id=lead_id, session=session)
        notes = get_notes(lead_id=lead_id, session=session)

        return {
            "success": True,
            "data": build_lead_out(
                lead=lead,
                include_history=True,
                include_notes=True,
                status_history=history,
                notes=notes,
            ),
        }
    except LeadServiceError as err:
        _raise_as_http(err)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "errorCode": "LEAD_GET_UNEXPECTED_ERROR",
                "message": f"Unexpected error while fetching lead: {exc}",
            },
        ) from exc


@router.patch(
    "/repair/{lead_id}/status",
    response_model=LeadStatusUpdateResponse,
    responses={
        404: {"model": LeadErrorResponse},
        409: {"model": LeadErrorResponse},
        422: {"model": LeadErrorResponse},
    },
)
def update_repair_lead_status_endpoint(
    lead_id: str,
    payload: LeadStatusUpdateRequest,
    session: SessionDep,
):
    """Update operational status and persist audit history."""
    try:
        result = update_repair_lead_status(
            lead_id=lead_id,
            new_status=payload.status,
            changed_by=payload.changed_by or "system",
            session=session,
        )
        return {
            "success": True,
            "data": LeadStatusUpdateData(
                lead_id=result.lead.id,
                old_status=result.old_status,
                new_status=result.new_status,
                changed_at=result.changed_at,
            ),
        }
    except LeadServiceError as err:
        _raise_as_http(err)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "errorCode": "LEAD_STATUS_UPDATE_UNEXPECTED_ERROR",
                "message": f"Unexpected error while updating status: {exc}",
            },
        ) from exc


@router.post(
    "/repair/{lead_id}/notes",
    response_model=LeadNoteResponse,
    status_code=status.HTTP_201_CREATED,
    responses={404: {"model": LeadErrorResponse}, 422: {"model": LeadErrorResponse}},
)
def create_repair_lead_note_endpoint(
    lead_id: str,
    payload: LeadNoteCreateRequest,
    session: SessionDep,
):
    """Add internal operational notes to an existing lead."""
    try:
        note = add_repair_lead_note(
            lead_id=lead_id,
            note=payload.note,
            created_by=payload.created_by or "system",
            session=session,
        )
        return {
            "success": True,
            "data": LeadNoteData(lead_id=lead_id, note_id=note.id, created_at=note.created_at),
        }
    except LeadServiceError as err:
        _raise_as_http(err)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "errorCode": "LEAD_NOTE_CREATE_UNEXPECTED_ERROR",
                "message": f"Unexpected error while creating note: {exc}",
            },
        ) from exc
