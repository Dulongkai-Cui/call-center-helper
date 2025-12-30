# 📞 Call-Center-Helper (电话招募打卡系统)

A collaborative Streamlit application designed for efficient telephone recruitment and result tracking. It uses **Tencent Docs Smart Sheet** as a backend database, supporting multi-user concurrency with an optimistic locking mechanism.

## 🌟 Features

*   **Multi-User Support**: Dedicated logic for different callers (Caller_01, etc.).
*   **Automatic Ticket Locking**: "First-come, first-served" claim system with Optimistic Locking to prevent collisions.
*   **One-Click Workflow**: Streamlined "Pass/Fail/No Answer" actions that auto-load the next ticket.
*   **Admin Dashboard**: Simple stats overview for supervisors.
*   **Secure**: Uses `st.secrets` for API credentials.

## 🛠️ Project Structure

```
root/
├── app.py                  # Main Application Entry
├── requirements.txt        # Python Dependencies
├── utils/
│   ├── tencent_api.py      # API Connection & Token Management
│   └── logic.py            # Business Logic (Locking, Searching, Updating)
└── docs/                   # Documentation (Design, Alignment, Tasks)
```

## 🚀 Setup & Installation

### 1. Local Development

1.  **Clone the Repo**:
    ```bash
    git clone https://github.com/your-repo/call-center-helper.git
    cd call-center-helper
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Secrets**:
    Create a file `.streamlit/secrets.toml` in the root directory:
    ```toml
    [tencent]
    appid = "YOUR_APP_ID"
    secret = "YOUR_APP_SECRET"
    file_id = "YOUR_SMART_SHEET_FILE_ID"
    sheet_id = "YOUR_SHEET_ID"  # Usually a short string like 'BB08J2'
    ```

4.  **Run the App**:
    ```bash
    streamlit run app.py
    ```

### 2. Deployment on Streamlit Cloud

1.  Push your code to a public GitHub repository.
2.  Login to [share.streamlit.io](https://share.streamlit.io/).
3.  Click **New App** and select your repository.
4.  **CRITICAL**: Before deploying, click **Advanced Settings** -> **Secrets**.
5.  Paste the content of your `secrets.toml` into the secrets area:
    ```toml
    [tencent]
    appid = "..."
    secret = "..."
    file_id = "..."
    sheet_id = "..."
    ```
6.  Click **Deploy**.

## 📖 Usage Guide

1.  **Login**: Select your username from the sidebar (e.g., `Caller_01`).
2.  **Start**: Click "Start Work" to grab a ticket.
3.  **Call**:
    *   Dial the displayed **Phone Number**.
    *   Follow the **Script** on the right.
    *   Check **Device Info**.
4.  **Submit**:
    *   **Pass**: Input QQ -> Click Green Button.
    *   **Fail/Refuse**: Click Red Button.
    *   **No Answer**: Click Yellow Button.
    *   *System automatically loads the next number.*

## ⚠️ Important Notes

*   **Do NOT edit the Google/Tencent Sheet manually** in the `Col P (Device)` or `Col D (Formula)` columns while the bot is running.
*   **Concurrency**: The system attempts to prevent two people from grabbing the same number, but in rare network lag cases, double-claims can happen. The system is designed so "Last Write Wins" for the `Col Q (Staff)`, and the UI double-checks this before showing the ticket to you.

---
*Built with ❤️ by Antigravity*
