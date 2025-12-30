# Alignment: Call-Center-Helper System

**Status**: Phase 1 (Align)  
**Date**: 2025-12-31

## 1. Project Goal
Build a collaborative "Telephone Recruitment Clock-in System" using **Python Streamlit** (Frontend) and **Tencent Docs Smart Sheet** (Backend). The system allows multiple employees to claim phone numbers, record call results, and tracks performance, while adhering to strict security and concurrency handling rules.

## 2. Tech Stack & Constraints
- **Frontend**: Streamlit (SessionState for state management).
- **Backend**: Tencent Docs OpenAPI (Smart Sheet).
- **Auth**: `st.secrets` for AppID/Secret/Token (No hardcoding).
- **Concurrency**: Must handle race conditions using "Occupancy" logic (Locking mechanism).
- **Deployment**: Streamlit Community Cloud (Public Repo).

## 3. Data Model (Sheet1)
The table structure is fixed. Column mapping and permissions:

| Column | Name | Permission | Description |
| :--- | :--- | :--- | :--- |
| **A** | account | Read-Only | Unique ID / Account Name. |
| **B** | 已电联 | **Write** | Flag: `1` = Processed. |
| **C** | 已选中 | **Write** | Flag: `1` = Perfect pass, `0` = Others. |
| **D** | 是否已电联... | **Read-Only** | VLOOKUP Formula. **DO NOT OVERWRITE**. |
| **E** | QQ | **Write** | Updated if user provides a new QQ. |
| **M** | 手机号 | Read-Only | Phone number to call. |
| **O** | 设备 | Read-Only | Device info for verification. |
| **P** | 建联人 | **Write** | Name of the employee handling this row. |
| **Q** | 备注 | **Write** | Status text (e.g., "Pass", "Hangup", "Refused"). |

**Critical Rule**: When updating rows, only write to Columns B, C, E, P, Q. Do not touch others.

## 4. User Flows

### 4.1 Login & Sidebar
- **Input**: Select Employee Name (e.g., "Caller_01") from a predefined list.
- **Admin**: "Admin" user sees the dashboard.

### 4.2 "Get Ticket" (Claiming a Number)
**Logic**:
1.  **Resume**: Search for row where `建联人 (P)` == CurrentUser AND `已电联 (B)` != 1.
2.  **New Claim**: Search for row where `建联人 (P)` is Empty AND `已电联 (B)` != 1.
3.  **Concurrency Lock**:
    - Identify target row index.
    - **Write**: Set `建联人 (P)` = CurrentUser.
    - **Verify**: Re-read row to ensure it wasn't claimed by another user in the interim. (Optional but recommended).
    - **Display**: Show data if lock successful.

### 4.3 Workspace UI
- **Display**: Large Name & Phone Number.
- **Audio File**: `account_Name.mp3` with Copy button.
- **Script**: Prompts for Device Check, Time, NDA, QQ.

### 4.4 One-Click Submit (Actions)
No manual refresh needed. Action triggers write then auto-loads next ticket.

| Action | Color | Updates |
| :--- | :--- | :--- |
| **Perfect** | 🟢 Green | `QQ`=Input, `已电联`=1, `已选中`=1, `备注`="通过", `建联人`=Me |
| **Reject/Device** | 🔴 Red | `已电联`=1, `已选中`=0, `备注`="设备不符/拒绝", `建联人`=Me |
| **No Answer** | 🔴 Yellow | `已电联`=1, `已选中`=0, `备注`="未接/挂断", `建联人`=Me |

### 4.5 Admin Dashboard
- Progress bar (Total `已电联` / Total Rows).
- Leaderboard (Count of `已选中`=1 per `建联人`).

## 5. Potential Risks & Questions
1.  **API Rate Limits**: Tencent Docs API has rate limits. Need robust error handling and retries.
2.  **Token Expiry**: Access Token expires. Need implicit refresh mechanism (check expiry -> refresh -> retry).
3.  **Concurrency**: If two people see the same "Empty" P column row at the same time, the first one to write wins.
    - **Strategy**: When checking for a new row, we should perhaps use a random offset or check `P` again before committing? Or simply accept "Last Write Wins" for the `建联人` column, but that might confuse the first user.
    - **Proposed Solution**: Write `建联人` = Me. If write success, that's the claim. If User A and B both write, the final value in the cell determines owner. The UI should double-check "Is `建联人` == Me?" after writing before showing the ticket to the user.

## 6. Next Steps (Phase 2: Architect)
- Design `utils/tencent_api.py` class structure.
- Design `utils/logic.py` flow.
