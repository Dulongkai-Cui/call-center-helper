import requests
import time
import streamlit as st

class TencentDocsAPI:
    """
    Singleton-like wrapper for Tencent Docs Smart Sheet OpenAPI.
    Handles Authentication and Token Refresh.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TencentDocsAPI, cls).__new__(cls)
            cls._instance.init_api()
        return cls._instance

    def init_api(self):
        # Load secrets
        try:
            self.app_id = st.secrets["tencent"]["appid"]
            self.app_secret = st.secrets["tencent"]["secret"]
            self.file_id = st.secrets["tencent"]["file_id"]
            self.sheet_id = st.secrets["tencent"]["sheet_id"]
        except Exception as e:
            st.error(f"Missing specific secrets. Please configure secrets.toml: {e}")
            self.app_id = None

    def _get_token(self):
        """
        Returns a valid access token. Refreshes if expired or missing.
        """
        # Check session state for existing valid token
        if 'oauth_token' in st.session_state and 'token_expiry' in st.session_state:
            if time.time() < st.session_state['token_expiry'] - 60: # Buffer 60s
                return st.session_state['oauth_token']
        
        # Request new token
        url = "https://docs.qq.com/oauth/v2/token"
        params = {
            "client_id": self.app_id,
            "client_secret": self.app_secret,
            "grant_type": "client_credentials"
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            if "access_token" in data:
                st.session_state['oauth_token'] = data['access_token']
                # Default expiry is usually 7200s, assume safe 3600s or use returned 'expires_in'
                expires_in = data.get('expires_in', 7200)
                st.session_state['token_expiry'] = time.time() + expires_in
                return data['access_token']
            else:
                st.error(f"Failed to get token: {data}")
                return None
        except Exception as e:
            st.error(f"Network error during token fetch: {e}")
            return None

    def get_headers(self):
        token = self._get_token()
        if not token:
            raise ValueError("Authentication Failed")
        return {
            "Access-Token": token,
            "Client-Id": self.app_id,
            "Content-Type": "application/json"
        }

    def get_sheet_data(self):
        """
        Fetch all rows from the configured sheet.
        Returns: Dict (Raw JSON response of rows) or None
        """
        url = f"https://docs.qq.com/openapi/drive/v2/files/{self.file_id}/sheets/{self.sheet_id}/values/A:R" # Fetch A to R
        # Note: Adjust range 'A:R' based on max columns needed.
        
        try:
            res = requests.get(url, headers=self.get_headers(), timeout=15)
            if res.status_code == 200:
                data = res.json()
                # Validate response structure
                if 'data' in data and 'values' in data['data']:
                    return data['data']['values'] # List of Lists
            return []
        except Exception as e:
            st.error(f"API Read Error: {e}")
            return []

    def update_range(self, row_idx, col_idx, value):
        """
        Update a single cell.
        row_idx: 0-based index for API (0 is Header usually, but check API specifics)
        Actually Tencent Docs OpenAPI uses Range string for simple updates usually, 
        or a batch update endpoint. 
        We will use the Values Update endpoint: PATCH /files/{file_id}/sheets/{sheet_id}/values/{range}
        
        Range format: "A1", or specific cell like "Q5".
        """
        # Convert indexes to A1 notation. 
        # A=0, B=1... Q=16, R=17
        col_letter = chr(ord('A') + col_idx) # Works for A-Z (0-25). Sufficient for this project (max R=17).
        # Row in API usually 1-based for A1 notation? Yes. 
        # But if our internal row_idx matches the list index from get_sheet_data(A:Z), 
        # and List[0] is Header, then actual Sheet Row 1 is Header.
        # internal_idx 0 (Header) -> Sheet Row 1
        # internal_idx 1 (Data) -> Sheet Row 2
        
        sheet_row_num = row_idx + 1 
        range_str = f"{col_letter}{sheet_row_num}"
        
        url = f"https://docs.qq.com/openapi/drive/v2/files/{self.file_id}/sheets/{self.sheet_id}/values/{range_str}"
        
        body = {
            "values": [[value]] # 2D array for single cell
        }
        
        try:
            res = requests.patch(url, headers=self.get_headers(), json=body, timeout=10)
            if res.status_code != 200:
                 st.warning(f"Update failed for {range_str}: {res.text}")
                 return False
            return True
        except Exception as e:
            st.error(f"API Write Error: {e}")
            return False

    def get_cell_value(self, row_idx, col_idx):
        """
        Specific read for verification using range.
        """
        col_letter = chr(ord('A') + col_idx)
        sheet_row_num = row_idx + 1 
        range_str = f"{col_letter}{sheet_row_num}"
        
        url = f"https://docs.qq.com/openapi/drive/v2/files/{self.file_id}/sheets/{self.sheet_id}/values/{range_str}"
        
        try:
            res = requests.get(url, headers=self.get_headers(), timeout=10)
            if res.status_code == 200:
                data = res.json()
                if 'data' in data and 'values' in data['data']:
                    rows = data['data']['values']
                    if rows and len(rows) > 0 and len(rows[0]) > 0:
                        return rows[0][0]
            return None
        except Exception:
            return None

    def get_sheet_list(self):
        """
        Fetches the list of all sheets in the file.
        Returns: List of dicts [{'id': 'BB08J2', 'title': '总表'}, ...]
        """
        url = f"https://docs.qq.com/openapi/drive/v2/files/{self.file_id}/sheets"
        try:
            res = requests.get(url, headers=self.get_headers(), timeout=10)
            if res.status_code == 200:
                data = res.json()
                if 'data' in data and 'sheets' in data['data']:
                    return data['data']['sheets']
            return []
        except Exception as e:
            st.error(f"Failed to fetch sheets: {e}")
            return []

