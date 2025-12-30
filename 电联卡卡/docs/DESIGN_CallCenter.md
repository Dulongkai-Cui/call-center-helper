# Design: Call-Center-Helper System

**Status**: Phase 2 (Architect)  
**Date**: 2025-12-31

## 1. System Architecture

The application adopts a **Service-Oriented Architecture (SOA)** within a monolithic Streamlit app.

### 1.1 Directory Structure
```
root/
├── app.py                  # Main entry point (Login + Routing)
├── .streamlit/
│   └── secrets.toml        # [Local Dev Only] API Credentials
├── assets/                 # Images, CSS
├── docs/                   # Documentation
├── utils/
│   ├── __init__.py
│   ├── tencent_api.py      # TencentDocsAPI Class (Singleton connection)
│   ├── logic.py            # Business Logic (Claim, Submit, release)
│   └── ui_components.py    # Reusable UI widgets (Cards, Status badges)
└── requirements.txt        # Dependencies
```

## 2. Key Modules Design

### 2.1 `utils/tencent_api.py` (The Connector)
Encapsulates all raw HTTP requests to Tencent Docs OpenAPI.

*   **Class**: `TencentDocsAPI`
*   **Attributes**:
    *   `access_token`: Str (Cached in session w/ expiry check)
    *   `file_id`, `sheet_id`: Str (Configured via secrets)
*   **Methods**:
    *   `_get_token()`: Authenticate/Refresh token.
    *   `get_sheet_data(range="A:Q")`: Returns raw rows.
    *   `update_range(row_idx, col_idx, values)`: Writes data.
    *   `batch_update(updates)`: Handle multiple cell updates if needed.

### 2.2 `utils/logic.py` (The Brain)
Handles the "Call Center" specific rules.

*   **Functions**:
    *   `get_my_ticket(user_name)`:
        *   Step 1: Fetch all data.
        *   Step 2: Filter for `建联人 == user_name` AND `已电联 != 1`. Return first match.
        *   Step 3: If none, find first `建联人 == ""` AND `已电联 != 1`.
        *   Step 4 (*Critical*): Call `lock_ticket(row_index, user_name)` to claim it.
    *   `lock_ticket(row_index, user_name)`:
        *   Writes `user_name` to Column P at `row_index`.
        *   Returns success/fail (optimistic locking).
    *   `submit_result(row_index, action_type, payload)`:
        *   Constructs updates based on action (Pass/Fail/NoAnswer).
        *   Writes to API.

## 3. Concurrency Strategy (Optimistic Locking)

Since we cannot hold a real database lock, we use an **Optimistic Locking** strategy with "Read-Modify-Write" verification on the UI side logic (simplified for V1):

1.  **Read**: User A and User B both read row 10 as "Empty".
2.  **Write**:
    *   User A clicks "Get Ticket" -> Logic writes "User A" to Row 10 Col P.
    *   User B clicks "Get Ticket" -> Logic writes "User B" to Row 10 Col P.
3.  **Conflict**: The last write wins physically in the sheet.
4.  **Mitigation (V1.5)**:
    *   Inside `lock_ticket`, after writing, sleep 0.2s and **READ BACK** the cell.
    *   If cell value == `user_name`, Success.
    *   If cell value != `user_name`, Fail (someone else took it). Recursively try next available row.

## 4. Token Management
*   **Storage**: `st.session_state['oauth_token']` and `st.session_state['token_expiry']`.
*   **Refresh**: Decorator `@check_token` on API methods. If `time.now > token_expiry`, auto-refresh before request.

## 5. UI/UX Design (Streamlit)
*   **Sidebar**:
    *   `Selectbox("Current User", ["Caller_01", ...])`
    *   Stats: "Today's Calls: X"
*   **Main**:
    *   **Header**: Big bold Phone Number (e.g., `138 **** 1234`).
    *   **Audio**: Stream audio from URL/File path (simulated for V1).
    *   **Action Area**: 3 Columns [Pass] [Fail] [No Answer].
    *   **History**: Expandable "Last 5 Calls".

## 6. Implementation Plan (Phase 3 Atomization preview)
1.  **Setup**: Secrets & Env.
2.  **API**: Basic Read/Write.
3.  **Logic**: The "Find & Lock" algorithm.
4.  **UI**: Wiring it up.
