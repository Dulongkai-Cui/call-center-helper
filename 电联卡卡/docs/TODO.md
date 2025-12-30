# Future Improvements (TODO)

## 🚨 Critical / High Priority

- [ ] **API Rate Limit Handling**:
    - Current: Basic 5-second `requests` timeout.
    - Future: Implement `tenacity` retry decorator with exponential backoff for 429 warnings.
- [ ] **Concurrent Write Conflict**:
    - Current: Simple "Sleep & Read Correctness Check".
    - Future: If conflict detected, automatically retry `find_ticket` instead of just warning the user.

## ✨ Features

- [ ] **WebSocket Notifications**:
    - Real-time "Global Broadcast" when a major milestone is reached (e.g., 100th Pass).
- [ ] **Stats History**:
    - Add a `History` tab showing the user's last 10 actions for quick undo/review.
- [ ] **Soft Delete / Undo**:
    - Allow users to "Undo" a mis-click (reverting status to 0).

## 🔧 Engineering

- [ ] **Unit Tests**: Add `pytest` for `logic.py` using a mocked API response.
- [ ] **Type Hints**: Add full PEP 484 type hints to `tencent_api.py`.
- [ ] **Logging**: Replace `st.error`/`print` with a proper `logging` module to track API latency.
