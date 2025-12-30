import pandas as pd
import time
import streamlit as st
from utils.tencent_api import TencentDocsAPI

# Column Configuration (0-based Index)
# A=0, B=1, ... M=12, O=14, P=15, Q=16, R=17
COL_ACCOUNT = 0
COL_STATUS = 1    # B: 已电联
COL_SELECTED = 2  # C: 已选中
COL_QQ = 4        # E: QQ
COL_PHONE = 12    # M: 手机
COL_DEVICE = 15   # P: 设备 (Read Only as per user correction)
COL_STAFF = 16    # Q: 建联人 (LOCK TARGET)
COL_NOTE = 17     # R: 备注

api = TencentDocsAPI()

def get_dataframe():
    """Fetches all data and converts to Pandas DataFrame."""
    raw_data = api.get_sheet_data()
    if not raw_data:
        return pd.DataFrame()
    
    # Assume first row is header
    headers = raw_data[0]
    rows = raw_data[1:]
    
    # Pad rows if they are shorter than headers
    padded_rows = []
    for r in rows:
        if len(r) < len(headers):
            r += [""] * (len(headers) - len(r))
        padded_rows.append(r[:len(headers)]) # Truncate if too long?
        
    df = pd.DataFrame(padded_rows, columns=headers)
    return df

def find_and_lock_ticket(user_name):
    """
    1. Find unfinished ticket assigned to ME.
    2. If none, find Valid, Unfinished, Unassigned ticket.
    3. Lock it (Write Name -> Wait -> Read).
    
    Returns: (row_index, row_data_dict) or (None, None)
    """
    raw_values = api.get_sheet_data()
    if not raw_values:
        st.error("无法拉取数据，请检查网络或配置")
        return None, None

    # We work with raw list indices to correspond 1:1 with API rows
    # raw_values[0] is Header -> Index 0
    # raw_values[1] is Data -> Index 1
    
    # 1. Search for Resume (My locked but unfinished tasks)
    for i in range(1, len(raw_values)):
        row = raw_values[i]
        # Ensure row has enough columns to check logic
        if len(row) <= COL_STAFF: continue 
        
        status = row[COL_STATUS] if len(row) > COL_STATUS else ""
        staff = row[COL_STAFF] if len(row) > COL_STAFF else ""
        
        if str(status) != "1" and staff == user_name:
            # Case: Found my own unfinished task
            return i, _row_to_dict(row)

    # 2. Search for New (Unassigned & Unfinished)
    # Strategy: Find first N candidates, pick one? For now, linear search.
    for i in range(1, len(raw_values)):
        row = raw_values[i]
        if len(row) <= COL_STAFF: continue # Skip malformed
        
        status = row[COL_STATUS] if len(row) > COL_STATUS else ""
        staff = row[COL_STAFF] if len(row) > COL_STAFF else ""
        
        # Logic: Status != 1 AND Staff is Empty
        if str(status) != "1" and (staff is None or str(staff).strip() == ""):
            # Found candidate at Row index i
            
            # --- LOCKING MECHANISM ---
            # 1. Write my name
            success = api.update_range(i, COL_STAFF, user_name)
            if not success:
                continue # Write failed, try next
                
            # 2. Optimistic Wait
            time.sleep(0.5) # Wait for eventual consistency or conflict
            
            # 3. Read back
            actual_staff = api.get_cell_value(i, COL_STAFF)
            if actual_staff == user_name:
                # Success!
                # Update local row data with the new staff name for display
                if len(row) > COL_STAFF:
                    row[COL_STAFF] = user_name
                return i, _row_to_dict(row)
            else:
                # Conflict or fail
                st.warning(f"Row {i+1} 被 {actual_staff} 抢占，正在寻找下一条...")
                continue
                
    return None, None

def submit_ticket(row_idx, action_type, user_name, data_payload=None):
    """
    Updates the row based on action.
    action_type: 'PASS', 'FAIL', 'NO_ANSWER'
    """
    if not data_payload: data_payload = {}
    
    qq = data_payload.get('qq', "")
    
    # Determine Status
    # B:已电联(1), C:已选中(1/0), E:QQ, Q:建联人(Me), R:备注
    
    updates = {}
    
    if action_type == 'PASS':
        status_note = "通过"
        is_selected = "1"
        updates[COL_QQ] = qq
    elif action_type == 'FAIL':
        status_note = "设备不符/拒绝"
        is_selected = "0"
    elif action_type == 'NO_ANSWER':
        status_note = "未接/挂断"
        is_selected = "0"
    else:
        return False

    # Apply Common Updates
    # Note: API calls are separate. optimize if batch available.
    # For now, separate calls for safety.
    
    # 1. Note (R)
    api.update_range(row_idx, COL_NOTE, status_note)
    # 2. Selected (C)
    api.update_range(row_idx, COL_SELECTED, is_selected)
    # 3. Staff (Q) - Re-affirm ownership
    api.update_range(row_idx, COL_STAFF, user_name)
    # 4. QQ (E) - Only if provided
    if action_type == 'PASS' and qq:
        api.update_range(row_idx, COL_QQ, qq)
    
    # 5. Processed (B) - Last update to seal it
    api.update_range(row_idx, COL_STATUS, "1")
    
    return True

def _row_to_dict(row):
    """Helper to safely map list row to dict for UI"""
    def get_safe(idx):
        return row[idx] if len(row) > idx else ""
        
    return {
        "account": get_safe(COL_ACCOUNT),
        "phone": get_safe(COL_PHONE),
        "device": get_safe(COL_DEVICE),
        "location": get_safe(14), # O col
        "qq": get_safe(COL_QQ),
        "note": get_safe(COL_NOTE)
    }
