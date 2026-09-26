# Pocketful API Contract Specification — Stage 1

## Overview
This document specifies the exact REST API contract, request/response JSON schemas, headers, error formats, and behavioral invariants expected by the **Pocketful Stage 1 Test Harness** and grading suite in the WeAreDevelopers x BAND Dark Factory hackathon.

---

## 1. Global Protocol & Runtime Conventions

### 1.1 Content Types & Charset
- All requests and responses with bodies must use: `Content-Type: application/json; charset=utf-8`.
- Timestamps in all responses must be formatted as **RFC 3339** strings with explicit offsets (e.g. `2026-09-24T19:00:00+02:00` or `2026-09-24T11:04:03+00:00`).

### 1.2 Extensibility & Query Parameter Handling
- **Unknown request body fields** are silently ignored and must never cause an error (`400`/`422`).
- **Unknown query parameters** are silently ignored.

### 1.3 Identification & Keys
- IDs (`user_id`, `payment_id`, `request_id`, `split_id`, `settlement_id`) are opaque strings of at most 64 characters (e.g. `u_ada`, `p_7`, `rq_4`, `sp_2`, `set_1`).
- `Idempotency-Key` headers accept arbitrary client strings of 1 to 255 characters. Keys larger than 255 characters return `422 validation_failed`.

### 1.4 Numeric & Arithmetic Representation
- The system operates in a single declared currency per fixture with an integer minor unit specification (`minor_units`: `0`, `2`, or `3`).
- **All amounts are exact integer counts of minor units** (e.g. `1000` minor units with `minor_units: 2` represents €10.00).
- Amounts accept integral JSON numbers: `1000`, `1000.0`, and `1e3` are all valid representations of `1000`. Floating-point numbers with fractional minor units (e.g. `1.5`) or strings (e.g. `"1000"`) or booleans are rejected with `422 validation_failed`.
- Range limit: Single-request `amount` must satisfy `1 <= amount <= 1000000000` (1 billion). Values `< 1` or `> 1e9` return `422 validation_failed`.
- Total wallet balance across operations must stay within the exact IEEE 754 safe integer range `[-2^53, 2^53]`.

---

## 2. Standardized Error Response Envelope

Every HTTP `4xx` and `5xx` error response strictly adheres to the following envelope:

```json
{
  "error": {
    "code": "<error_code>",
    "message": "<human readable explanation, any wording>"
  }
}
```

The test harness asserts exclusively on the HTTP status code and the `error.code` string value.

### Canonical Error Codes Matrix

| HTTP Status | Error Code (`error.code`) | Trigger Condition |
|---|---|---|
| **400** | `malformed_request` | Body is not valid JSON, or a field has an invalid JSON type (e.g. object instead of string). |
| **400** | `missing_idempotency_key` | Required `Idempotency-Key` header is missing or empty on an idempotent write path. |
| **401** | `unauthenticated` | Missing, malformed, or invalid `Authorization: Bearer <token>` header; or incorrect credentials during login. |
| **403** | `forbidden` | Authenticated caller does not have permission to act on or view the resource (e.g. non-payer paying/declining a request, non-requester cancelling, non-operator calling `/settlements`). |
| **404** | `not_found` | Resource does not exist (unknown handle, unknown `request_id`, or resource hidden by visibility rules). |
| **409** | `email_taken` | Signup attempt with an email that is already registered. |
| **409** | `handle_taken` | Signup attempt where the handle derived from the email is already assigned to an existing user. |
| **409** | `insufficient_funds` | Payer's wallet balance is less than the transfer amount in `/payments`, `/requests/{id}/pay`, or aggregate `/settlements`. |
| **409** | `idempotency_key_reuse` | Reusing an `Idempotency-Key` with a different request body, method, or path. |
| **409** | `request_not_pending` | Attempting to pay, decline, or cancel a request that is not currently in `pending` status. |
| **422** | `self_payment` | Caller attempts to send a payment or settlement transfer to their own handle. |
| **422** | `self_request` | Caller attempts to request money from their own handle. |
| **422** | `validation_failed` | Missing required field; `amount` out of range `[1, 1000000000]`; `note` > 200 characters; `visibility` not `"public"` or `"private"`; password < 8 characters; invalid email format; invalid pagination params (`limit` < 1 or > 200, `offset` < 0); empty/duplicate handles in `/splits`; negative balances in fixture reset. |

---

## 3. Idempotency Protocol (§7)

The five idempotent write paths in Stage 1 are:
1. `POST /payments`
2. `POST /requests`
3. `POST /requests/{id}/pay`
4. `POST /splits`
5. `POST /settlements`

### Rules:
1. **Header Requirement**: `Idempotency-Key: <string>` (1 to 255 chars). Missing/empty -> `400 missing_idempotency_key`.
2. **User & Endpoint Scoping**: The key is scoped to the **authenticated user**, the **HTTP method**, and the **URL path**. Two distinct users may use the same key without conflict. The same user may use the same key on `/payments` and `/requests` without conflict.
3. **First Use**: Executes operation, mutates state, and returns **`201 Created`** with response body.
4. **Exact Replay**: Re-sending the identical key and identical JSON body returns **`200 OK`** with the identical response body recorded on first success. No state or balance changes occur.
5. **Replay Pay Specifics**: Replaying a paid request returns `200 OK` with the original payment response, even though the underlying request is already in `paid` status (does NOT return `409 request_not_pending`).
6. **Key Mismatch / Reuse**: Re-sending the same key with a different JSON payload (e.g. `{}` vs `{"visibility": "public"}`) returns **`409 idempotency_key_reuse`**.
7. **Failed Request Recovery**: If the original request failed with a `4xx` error (e.g. `409 insufficient_funds`), the key was NOT claimed for success. Reusing the key once the account is funded is treated as a **first use** and returns `201 Created`.
8. **Concurrent Requests**: Under simultaneous identical requests with an unused key, exactly one request returns `201` and executes the mutation; all other concurrent requests wait and return `200` with the matching body.

---

## 4. Complete Endpoint Reference

### 4.1 Health Check

```http
GET /health
```
- **Auth**: None
- **Response**: `200 OK`
```json
{ "status": "ok" }
```

---

### 4.2 Test Reset & Fixture Seeding

```http
POST /_test/reset
Content-Type: application/json
```
- **Auth**: None
- **Request Body**:
```json
{
  "currency": "EUR",
  "minor_units": 2,
  "users": [
    {
      "id": "u_ada",
      "email": "ada@example.com",
      "password": "correct horse",
      "display_name": "Ada",
      "handle": "ada",
      "balance": 10000
    },
    {
      "id": "u_bob",
      "email": "bob@example.com",
      "password": "correct horse",
      "display_name": "Bob",
      "handle": "bob",
      "balance": 2500
    }
  ],
  "payments": [
    {
      "id": "p_1",
      "from_user_id": "u_ada",
      "to_user_id": "u_bob",
      "amount": 500,
      "note": "coffee",
      "visibility": "public"
    }
  ],
  "requests": [
    {
      "id": "rq_1",
      "requester_id": "u_bob",
      "payer_id": "u_ada",
      "amount": 1200,
      "note": "taxi",
      "status": "pending"
    }
  ],
  "settlement_operator_ids": ["u_ada"]
}
```
- **Success Response**: `204 No Content`
- **Error Response**: If any seeded user has `balance < 0`, return `422 validation_failed` and leave previous state unmodified.
- **Rules**:
  - Replaces all database state with the fixture data.
  - `balance` is the wallet balance **after** seeded payments have been applied (do not replay seeded payments against balances).
  - Passwords in fixture must be hashed so users can immediately log in with their plain password.
  - `settlement_operator_ids` (default `[]`) grants permission to execute `/settlements`.

---

### 4.3 State Export & Import

```http
GET /_test/export
```
- **Auth**: None
- **Response**: `200 OK`
```json
{
  "track": "pocketful",
  "format_version": 1,
  "state": { ...opaque JSON object representing complete service state... }
}
```

```http
POST /_test/import
Content-Type: application/json

{
  "track": "pocketful",
  "format_version": 1,
  "state": { ... }
}
```
- **Auth**: None
- **Success Response**: `204 No Content`
- **Errors**: `400 malformed_request`, `422 validation_failed` (missing fields, invalid version, or invalid state without mutating destination).
- **Rules**: Atomically replaces state. Preserves users, balances, tokens, payments, requests, idempotent keys, retry records, and settlement operators.

---

### 4.4 Authentication

#### User Signup
```http
POST /auth/signup
Content-Type: application/json

{
  "email": "dee.ann+tag@example.com",
  "password": "correct horse",
  "display_name": "Dee"
}
```
- **Auth**: None
- **Derived Handle Rule**: Local part of email, lowercased, non `[a-z0-9_]` replaced by `_`, truncated to 20 characters (`"dee.ann+tag@example.com"` -> `"dee_ann_tag"`).
- **Initial Balance**: New users start with `balance = 0`.
- **Success Response**: `201 Created`
```json
{
  "user_id": "u_dee",
  "display_name": "Dee",
  "token": "tok_xyz..."
}
```
- **Errors**:
  - Password < 8 characters -> `422 validation_failed`
  - Email not `local@domain` format -> `422 validation_failed`
  - Email already exists -> `409 email_taken`
  - Derived handle already taken -> `409 handle_taken` (no user created)

#### User Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "ada@example.com",
  "password": "correct horse"
}
```
- **Auth**: None
- **Success Response**: `200 OK`
```json
{
  "user_id": "u_ada",
  "display_name": "Ada",
  "token": "tok_xyz..."
}
```
- **Errors**:
  - Wrong password or unknown email -> `401 unauthenticated`

---

### 4.5 Current Profile & Wallet (`GET /me`)

```http
GET /me
Authorization: Bearer <token>
```
- **Success Response**: `200 OK`
```json
{
  "user_id": "u_ada",
  "display_name": "Ada",
  "handle": "ada",
  "balance": 10000,
  "currency": "EUR",
  "minor_units": 2
}
```

---

### 4.6 Direct Payments (`POST /payments`)

**Idempotent Write Path**.
```http
POST /payments
Authorization: Bearer <token>
Idempotency-Key: 2f9c1a...
Content-Type: application/json

{
  "to_handle": "bob",
  "amount": 1500,
  "note": "dinner",
  "visibility": "public"
}
```
- **Defaults**: `note` defaults to `""`. `visibility` defaults to `"public"`.
- **Success Response (First Execution)**: `201 Created`
- **Success Response (Replay)**: `200 OK`
```json
{
  "payment_id": "p_7",
  "from_user_id": "u_ada",
  "from_handle": "ada",
  "to_user_id": "u_bob",
  "to_handle": "bob",
  "amount": 1500,
  "currency": "EUR",
  "note": "dinner",
  "visibility": "public",
  "request_id": null,
  "created_at": "2026-09-24T11:04:03+00:00"
}
```
- **Errors**:
  - Missing `Idempotency-Key` -> `400 missing_idempotency_key`
  - Caller balance < amount -> `409 insufficient_funds`
  - Reused key with different payload -> `409 idempotency_key_reuse`
  - `to_handle` is caller's handle -> `422 self_payment`
  - Unknown `to_handle` -> `404 not_found`
  - `amount` not integer or not in `[1, 1000000000]` -> `422 validation_failed`
  - `note` length > 200 runes (supports 200 4-byte emoji) or not string -> `422 validation_failed`
  - `visibility` not `"public"` or `"private"` -> `422 validation_failed`
  - Key length > 255 -> `422 validation_failed`
- **Invariants**: `note` stored and returned verbatim (byte-for-byte unicode/emoji preservation). Transfer is atomic: debit and credit occur in the same database transaction.

---

### 4.7 Payment Requests

#### Create Request (`POST /requests`)
**Idempotent Write Path**.
```http
POST /requests
Authorization: Bearer <token>
Idempotency-Key: 9b1f04...
Content-Type: application/json

{
  "payer_handle": "ada",
  "amount": 1200,
  "note": "taxi"
}
```
- **Caller**: Becomes `requester`.
- **Payer Balance**: **Not checked at creation time.** Can legally exceed payer balance.
- **Success Response**: `201 Created` (Replay: `200 OK`)
```json
{
  "request_id": "rq_4",
  "requester_id": "u_bob",
  "requester_handle": "bob",
  "payer_id": "u_ada",
  "payer_handle": "ada",
  "amount": 1200,
  "currency": "EUR",
  "note": "taxi",
  "status": "pending",
  "payment_id": null,
  "created_at": "2026-09-24T11:06:10+00:00"
}
```
- **Errors**:
  - Missing key -> `400 missing_idempotency_key`
  - `payer_handle` is caller's handle -> `422 self_request`
  - Unknown `payer_handle` -> `404 not_found`
  - Invalid amount or note -> `422 validation_failed`

#### Pay Request (`POST /requests/{id}/pay`)
**Idempotent Write Path**. Only the `payer` may call this.
```http
POST /requests/rq_4/pay
Authorization: Bearer <token>
Idempotency-Key: c41d88...
Content-Type: application/json

{
  "visibility": "private"
}
```
- **Body**: Accepts `visibility` only (optional, defaults to `"public"`).
- **Body Replay Strictness**: `{}` and `{"visibility": "public"}` are different JSON values; re-using a key across them returns `409 idempotency_key_reuse`.
- **Success Response**: `201 Created` (Replay: `200 OK`). Returns the created **payment** record:
```json
{
  "payment_id": "p_9",
  "from_user_id": "u_ada",
  "from_handle": "ada",
  "to_user_id": "u_bob",
  "to_handle": "bob",
  "amount": 1200,
  "currency": "EUR",
  "note": "taxi",
  "visibility": "private",
  "request_id": "rq_4",
  "created_at": "2026-09-24T11:07:00+00:00"
}
```
- **Errors**:
  - Request is not `pending` -> `409 request_not_pending` (except identical key replay, which returns `200 OK`)
  - Payer balance < request amount -> `409 insufficient_funds`
  - Caller is not the request's payer -> `403 forbidden`
  - Unknown request ID -> `404 not_found`
  - Key reuse with different body -> `409 idempotency_key_reuse`

#### Decline Request (`POST /requests/{id}/decline`)
- **Idempotency Key**: None.
- **Caller**: Payer only.
- **Success Response**: `200 OK` with request object, `"status": "declined"`.
- **Rules**: Declining an already-declined request returns `200 OK`. If `paid` or `cancelled`, returns `409 request_not_pending`. Not payer -> `403 forbidden`.

#### Cancel Request (`POST /requests/{id}/cancel`)
- **Idempotency Key**: None.
- **Caller**: Requester only.
- **Success Response**: `200 OK` with request object, `"status": "cancelled"`.
- **Rules**: Cancelling an already-cancelled request returns `200 OK`. If `paid` or `declined`, returns `409 request_not_pending`. Not requester -> `403 forbidden`.

#### List Requests (`GET /requests`)
```http
GET /requests?direction=incoming&status=pending&limit=50&offset=0
Authorization: Bearer <token>
```
- **Filter Parameters**:
  - `direction`: `incoming` (caller is payer), `outgoing` (caller is requester), or absent for both.
  - `status`: `pending`, `paid`, `declined`, `cancelled`, or absent for all.
  - `limit`: integer 1 to 200 (default `50`).
  - `offset`: integer >= 0 (default `0`).
- **Ordering**: Newest first by `created_at`.
- **Isolation**: Returns requests where caller is requester or payer ONLY. Never leaks to third parties.
- **Success Response**: `200 OK`
```json
{
  "requests": [ ... ],
  "has_more": false
}
```
- **Errors**: Invalid direction/status or limit/offset out of bounds -> `422 validation_failed`.

---

### 4.8 Bill Splits (`POST /splits`)

**Idempotent Write Path**.
```http
POST /splits
Authorization: Bearer <token>
Idempotency-Key: 7a3e52...
Content-Type: application/json

{
  "amount": 3000,
  "participant_handles": ["ada", "bob", "cy"],
  "note": "dinner"
}
```
- **Equal Split Arithmetic (§9)**:
  - Base share: `base = amount // n`
  - Remainder: `remainder = amount % n`
  - First `remainder` participants in `participant_handles` order receive `base + 1`. The remaining participants receive `base`.
  - Shares always sum exactly to `amount`.
- **Request Creation**: Creates one `pending` request for every participant **except the caller**, with caller as `requester`.
- **Single-Participant Split**: If `participant_handles` contains only the caller, creates 0 requests, returns `"requests": []`.
- **Balance Checking**: Never checks anyone's balance.
- **Success Response**: `201 Created` (Replay: `200 OK`)
```json
{
  "split_id": "sp_2",
  "amount": 3000,
  "currency": "EUR",
  "note": "dinner",
  "shares": [
    { "handle": "ada", "amount": 1000 },
    { "handle": "bob", "amount": 1000 },
    { "handle": "cy", "amount": 1000 }
  ],
  "requests": [
    {
      "request_id": "rq_5",
      "requester_id": "u_ada",
      "requester_handle": "ada",
      "payer_id": "u_bob",
      "payer_handle": "bob",
      "amount": 1000,
      "currency": "EUR",
      "note": "dinner",
      "status": "pending",
      "payment_id": null,
      "created_at": "2026-09-24T11:11:00+00:00"
    },
    {
      "request_id": "rq_6",
      "requester_id": "u_ada",
      "requester_handle": "ada",
      "payer_id": "u_cy",
      "payer_handle": "cy",
      "amount": 1000,
      "currency": "EUR",
      "note": "dinner",
      "status": "pending",
      "payment_id": null,
      "created_at": "2026-09-24T11:11:00+00:00"
    }
  ],
  "created_at": "2026-09-24T11:11:00+00:00"
}
```
- **Errors**:
  - Missing key -> `400 missing_idempotency_key`
  - Empty `participant_handles` or duplicate handles -> `422 validation_failed`
  - Any handle unknown -> `404 not_found`
  - Invalid amount/note -> `422 validation_failed`

---

### 4.9 Activity Feed (`GET /activity`)

```http
GET /activity?limit=50&offset=0
Authorization: Bearer <token>
```
- **Feed Contract**: A payment appears for the caller **if and only if**:
  1. Its `visibility` is `"public"`, **OR**
  2. The caller is its `from_user_id` (sender), **OR**
  3. The caller is its `to_user_id` (receiver).
- Requests never appear in `/activity`.
- **Query Params**: `limit` (default 50, 1..200), `offset` (default 0, >= 0). Unknown parameters are silently ignored.
- **Ordering**: Newest first by `created_at`.
- **Success Response**: `200 OK`
```json
{
  "payments": [ ... ],
  "has_more": false
}
```
- **Errors**: Bad limit/offset -> `422 validation_failed`.

---

### 4.10 Net Settlements (`POST /settlements`)

**Idempotent Write Path**.
```http
POST /settlements
Authorization: Bearer <token>
Idempotency-Key: set_key_123...
Content-Type: application/json

{
  "transfers": [
    { "from_handle": "ada", "to_handle": "bob", "amount": 100 },
    { "from_handle": "bob", "to_handle": "cy", "amount": 50 }
  ]
}
```
- **Permissions**: Caller `user_id` must be present in `settlement_operator_ids`.
- **Validation**:
  - No token -> `401 unauthenticated`
  - Non-operator caller -> `403 forbidden`
  - `transfers` length: 1 to 32 items. Empty or > 32 -> `422 validation_failed`
  - Any transfer where `from_handle == to_handle` -> `422 self_payment`
  - Unknown handle -> `404 not_found`
  - Net affordability check: Every affected wallet's balance after summing all incoming credits and subtracting all outgoing debits across the entire batch must remain `>= 0`. If any wallet would drop below 0 -> `409 insufficient_funds`.
- **Atomicity**: All transfers execute together or none do.
- **Success Response**: `201 Created` (Replay: `200 OK`)
```json
{
  "settlement_id": "set_1",
  "committed_at": "2026-09-24T12:00:00+00:00",
  "payments": [
    {
      "payment_id": "p_10",
      "from_user_id": "u_ada",
      "from_handle": "ada",
      "to_user_id": "u_bob",
      "to_handle": "bob",
      "amount": 100,
      "currency": "EUR",
      "note": "",
      "visibility": "public",
      "request_id": null,
      "settlement_id": "set_1",
      "created_at": "2026-09-24T12:00:00+00:00"
    },
    {
      "payment_id": "p_11",
      "from_user_id": "u_bob",
      "from_handle": "bob",
      "to_user_id": "u_cy",
      "to_handle": "cy",
      "amount": 50,
      "currency": "EUR",
      "note": "",
      "visibility": "public",
      "request_id": null,
      "settlement_id": "set_1",
      "created_at": "2026-09-24T12:00:00+00:00"
    }
  ]
}
```
- All payments in the settlement share the same `settlement_id` and have `created_at == committed_at`.
- Non-settlement payments expose `"settlement_id": null`.
