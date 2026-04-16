# Leads Repair API - Frontend Quick Guide

## Base path

- `/v1/leads/repair`

## Required endpoints

1. `POST /v1/leads/repair`
- Receives wizard lead payload
- Validates + sanitizes + persists
- Applies rate limit, dedupe and optional idempotency
- Response:

```json
{
  "success": true,
  "data": {
    "leadId": "uuid",
    "status": "new",
    "createdAt": "2026-04-16T17:05:33.113941",
    "whatsappUrl": "https://wa.me/..."
  }
}
```

2. `GET /v1/leads/repair/{leadId}`
- Returns lead detail + status history + notes

3. `GET /v1/leads/repair`
- Paged list with filters
- Query params:
  - `status`
  - `dateFrom`
  - `dateTo`
  - `repairType`
  - `urgency`
  - `contactChannel`
  - `page` (default 1)
  - `size` (default 20, max 100)

4. `PATCH /v1/leads/repair/{leadId}/status`
- Updates operational status (`new`, `contacted`, `qualified`, `discarded`, `converted`)
- Writes audit row into `lead_status_history`

## Optional endpoints

1. `POST /v1/leads/repair/whatsapp-link`
- Receives same payload as create endpoint
- Returns only message + url

2. `POST /v1/leads/repair/{leadId}/notes`
- Adds internal note to existing lead

## Payload contract (POST /repair)

```json
{
  "brand": "Apple",
  "model": "iPhone 13",
  "repairType": "pantalla rota",
  "urgency": "hoy",
  "description": "No responde el touch",
  "contactChannel": "whatsapp",
  "contact": "+5491160011122",
  "wizardSource": "budget_wizard_v1",
  "utm": {
    "source": "google",
    "medium": "cpc",
    "campaign": "wizard-repair",
    "content": "cta-1",
    "term": "arreglo iphone"
  },
  "metadata": {
    "ip": "203.0.113.10",
    "userAgent": "Mozilla/5.0",
    "referrer": "https://example.com"
  }
}
```

## Error format

```json
{
  "success": false,
  "errorCode": "VALIDATION_ERROR",
  "message": "Invalid request payload.",
  "fieldErrors": [
    {
      "field": "repairType",
      "message": "Field required"
    }
  ]
}
```

## Antispam behavior

- Rate limit per `ip + user-agent`
- Dedupe by fingerprint `brand + model + repairType + contact` within short window
- Duplicate submissions are persisted with status `duplicated` and `duplicateOf` link
- Optional `Idempotency-Key` header:
  - same key + same payload: returns same lead
  - same key + different payload: `409 IDEMPOTENCY_CONFLICT`

## Suggested frontend usage

1. Call `POST /v1/leads/repair` when wizard is submitted.
2. Redirect user to returned `whatsappUrl`.
3. Save `leadId` for eventual status polling.
4. For retries from client/network errors, reuse `Idempotency-Key`.

## Environment variables

- `LEADS_WHATSAPP_NUMBER`
- `LEADS_DEDUPE_WINDOW_SECONDS` (default: `600`)
- `LEADS_RATE_LIMIT_REQUESTS` (default: `30`)
- `LEADS_RATE_LIMIT_WINDOW_SECONDS` (default: `60`)
