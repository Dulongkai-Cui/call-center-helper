import pandas as pd
import time
import streamlit as st
import pypinyin
from utils.tencent_api import TencentDocsAPI

# --- 最终确认列号配置 (0-based) ---
# A=0, B=1, C=2, D=3 ... J=9, K=10, M=12, O=14, P=15, Q=16, R=17

COL_ACCOUNT = 0
COL_STATUS = 1    # B: 已电联 (写入目标)
COL_SELECTED = 2  # C: 已选中 (写入目标: 1=通过, 0=未通过)
COL_CHECK = 3     # D: 去重校验 (只读: 如果是1则跳过)
COL_PASS = 9      # J: 通行证
COL_NAME = 10     # K: 真实姓名
COL_PHONE = 12    # M: 手机
COL_LOC = 14      # O: 常住地
COL_DEVICE = 15   # P: 设备
COL_STAFF = 16    # Q: 建联人 (抢号占位)
COL_NOTE = 17     # R: 备注

api = TencentDocsAPI()

def get_sheet_options():
    """Returns list of sheets for the sidebar selector."""
    sheets = api.get_sheet_list()
    if not sheets:
        return []
    return [s['title'] for s in sheets]

def set_active_sheet(sheet_title):
    """Sets the active sheet ID in the API instance based on title."""
    sheets = api.get_sheet_list()
    for s in sheets:
        if s['title'] == sheet_title:
            api.sheet_id = s['id']
            st.session_state['current_sheet_id'] = s['id']
            return True
    return False

def get_dataframe():
    """Fetches all data and converts to Pandas DataFrame."""
    raw_data = api.get_sheet_data()
    if not raw_data:
        return pd.DataFrame()
    
    headers = raw_data[0]
    rows = raw_data[1:]
    
    padded_rows = []
    for r in rows:
        if len(r) < len(headers):
            r += [""] * (len(headers) - len(r))
        padded_rows.append(r[:len(headers)])
        
    df = pd.DataFrame(padded_rows, columns=headers)
    return df

def find_and_lock_ticket(user_name):
    """
    1. Filter out where Col D (Index 3) == '1'.
    2. Locked Resume: Staff == Me AND Status != 1.
    3. New Claim: D != 1 AND Status != 1 AND Staff is Empty.
    """
    raw_values = api.get_sheet_data()
    if not raw_values:
        st.error("无法拉取数据，请检查网络或配置")
        return None, None

    # 1. Search for Resume (My locked but unfinished tasks)
    for i in range(1, len(raw_values)):
        row = raw_values[i]
        get = lambda idx: row[idx] if len(row) > idx else ""
        
        status = get(COL_STATUS)
        staff = get(COL_STAFF)
        check_val = get(COL_CHECK) # D列
        
        if str(check_val) == "1": continue

        if str(status) != "1" and staff == user_name:
            return i, _row_to_dict(row)

    # 2. Search for New
    for i in range(1, len(raw_values)):
        row = raw_values[i]
        get = lambda idx: row[idx] if len(row) > idx else ""

        status = get(COL_STATUS)
        staff = get(COL_STAFF)
        check_val = get(COL_CHECK) # D列
        
        # --- 核心去重逻辑 ---
        if str(check_val) == "1":
            continue

        if str(status) != "1" and (staff is None or str(staff).strip() == ""):
            # --- 抢号 ---
            success = api.update_range(i, COL_STAFF, user_name)
            if not success: continue
                
            time.sleep(0.5) 
            
            actual_staff = api.get_cell_value(i, COL_STAFF)
            if actual_staff == user_name:
                if len(row) > COL_STAFF: row[COL_STAFF] = user_name
                return i, _row_to_dict(row)
            else:
                st.warning(f"Row {i+1} 被 {actual_staff} 抢占...")
                continue
                
    return None, None

def submit_ticket(row_idx, action_type, user_name, data_payload=None):
    if not data_payload: data_payload = {}
    
    note_input = data_payload.get('note', "")
    qq = data_payload.get('qq', "")
    
    emoji = ""
    status_text = ""
    is_selected = "0" 
    
    if action_type == 'PASS':
        emoji = "🟢"
        status_text = "通过"
        is_selected = "1"
    elif action_type == 'FAIL':
        emoji = "🔴"
        status_text = "拒绝/设备不符"
        is_selected = "0"
    elif action_type == 'NO_ANSWER':
        emoji = "🟡"
        status_text = "未接/挂断"
        is_selected = "0"
    else:
        return False

    final_note = f"{emoji} [{status_text}] {note_input}"

    # --- 开始写入 (B, C, E, Q, R) ---
    api.update_range(row_idx, COL_NOTE, final_note)      # R: 备注
    api.update_range(row_idx, COL_SELECTED, is_selected) # C: 已选中 (关键修复!)
    api.update_range(row_idx, COL_STAFF, user_name)      # Q: 建联人
    
    # E: QQ (仅当通过且有值时写入)
    COL_QQ = 4
    if action_type == 'PASS' and qq:
        api.update_range(row_idx, COL_QQ, qq)
    
    api.update_range(row_idx, COL_STATUS, "1")           # B: 已电联
    
    return True

def _row_to_dict(row):
    def get(idx):
        return row[idx] if len(row) > idx else ""
    
    name = get(COL_NAME)
    try:
        py_list = pypinyin.lazy_pinyin(name)
        name_pinyin = " ".join(py_list).title()
    except:
        name_pinyin = ""

    return {
        "account": get(COL_ACCOUNT),
        "name": name,
        "pinyin": name_pinyin,
        "pass_id": get(COL_PASS),
        "phone": get(COL_PHONE),
        "device": get(COL_DEVICE),
        "location": get(COL_LOC),
        "note": get(COL_NOTE)
    }
