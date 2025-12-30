# Task Breakdown: Call-Center-Helper

**Status**: Phase 3 (Atomize)  
**Date**: 2025-12-31

## Task 1: Environment & API Connector (P0)
- [ ] **T1.1**: Create `requirements.txt` (streamlit, pandas, requests, openpyxl).
- [ ] **T1.2**: Create `utils/tencent_api.py` skeleton.
- [ ] **T1.3**: Implement **Auth** (AppID/Secret) and **Token Refresh** logic.
- [ ] **T1.4**: Implement `get_sheet_data()` to fetch all rows.
- [ ] **T1.5**: Implement `update_range()` for specific cells.
- [ ] **T1.6**: Create unit test script to verify API connectivity (local run).

## Task 2: Core Logic & Concurrency (P0)
- [ ] **T2.1**: Create `utils/logic.py`.
- [ ] **T2.2**: Implement `find_next_ticket(user_name)`:
    - Search for existing claim -> Search for new empty -> Return index.
- [ ] **T2.3**: Implement **Optimistic Locking** `lock_ticket(index, user)`:
    - Write Name -> (Optional: Read back to verify) -> Return Success/Fail.
- [ ] **T2.4**: Implement `submit_action(index, action_type, user)`:
    - Handle 'Perfect', 'Reject', 'No Answer'.
    - Update Columns B, C, P, Q, E.

## Task 3: UI Implementation (P1)
- [ ] **T3.1**: Create `app.py` basic layout (Wide mode).
- [ ] **T3.2**: **Sidebar Login**:
    - Dropdown for User selection.
    - Password check (optional/simple).
- [ ] **T3.3**: **Workspace Area**:
    - Show Big Phone Number.
    - Show Audio Player (Placeholder).
    - Show Script/Prompt text.
- [ ] **T3.4**: **Action Buttons**:
    - 3 Columns for Buttons (Green/Red/Yellow).
    - Wiring buttons to `logic.submit_action`.
    - Auto-load next ticket on click.

## Task 4: Admin Dashboard (P2)
- [ ] **T4.1**: Check if `user == "Admin"`.
- [ ] **T4.2**: Calculate Stats (Total Processed, % Success).
- [ ] **T4.3**: Show Per-Agent Leaderboard (DataFrame).

## Task 5: Integration & Polish (P1)
- [ ] **T5.1**: Add Error Handling (API fail notifications).
- [ ] **T5.2**: Add `st.session_state` persistence for current ticket.
- [ ] **T5.3**: Final Code Cleanup & Commenting.
- [ ] **T5.4**: Create `docs/README.md` for deployment instructions.
