import streamlit as st
import time
from utils import logic

# --- Page Config ---
st.set_page_config(page_title="Call Center V2", page_icon="📞", layout="wide")

st.markdown("""
<style>
    .big-font { font-size: 32px !important; font-weight: bold; color: #1E88E5; }
    .pinyin-font { font-size: 20px; color: #888; font-style: italic; }
    .label-font { font-size: 16px; color: #555; font-weight: bold; }
    .check-btn { border: 1px solid #ccc; padding: 2px 8px; border-radius: 4px; cursor: pointer; color: green; }
    .stButton button { width: 100%; height: 50px; font-size: 18px; }
    .verified { color: #2e7d32; font-weight: bold; border-bottom: 2px solid #2e7d32; }
</style>
""", unsafe_allow_html=True)

# --- Session Init ---
if 'user_name' not in st.session_state: st.session_state['user_name'] = ""
if 'current_ticket' not in st.session_state: st.session_state['current_ticket'] = None
if 'sheet_name' not in st.session_state: st.session_state['sheet_name'] = ""
# Local UI state for checks
if 'check_pass' not in st.session_state: st.session_state['check_pass'] = False
if 'check_loc' not in st.session_state: st.session_state['check_loc'] = False

# --- Sidebar ---
with st.sidebar:
    st.title("📞外测招募急速助手")
    
    # 1. User Select
    users = ["Caller_01", "Caller_02", "Caller_03", "Caller_04", "Admin"]
    selected_user = st.selectbox("当前员工 / User", [""] + users)
    
    if selected_user:
        st.session_state['user_name'] = selected_user
    else:
        st.warning("请选择员工")
        st.stop()
        
    st.divider()
    
    # 2. Sheet Select (New V2)
    sheet_options = logic.get_sheet_options()
    if sheet_options:
        selected_sheet = st.selectbox("选择任务表 / Sheet", sheet_options)
        if selected_sheet != st.session_state['sheet_name']:
            st.session_state['sheet_name'] = selected_sheet
            logic.set_active_sheet(selected_sheet)
            st.session_state['current_ticket'] = None # Reset ticket on sheet change
            st.rerun()
    else:
        st.error("无法加载 Sheet 列表")
    
    st.divider()
    st.caption("Emoji: 🟢通过 🔴拒绝 🟡未接")

# --- Logic ---
def load_new_ticket():
    # Reset UI checks
    st.session_state['check_pass'] = False
    st.session_state['check_loc'] = False
    
    with st.spinner("正在获取下一条..."):
        idx, data = logic.find_and_lock_ticket(st.session_state['user_name'])
        if idx:
            st.session_state['current_ticket'] = {"index": idx, "data": data}
            st.rerun()
        else:
            st.session_state['current_ticket'] = None
            st.error("当前表无可用任务！(或全部被 D 列过滤)")

if st.session_state['current_ticket'] is None:
    st.info(f"当前任务表: {st.session_state.get('sheet_name', 'Open to Select')}")
    if st.button("🚀 开始 / Start", type="primary"):
        load_new_ticket()
else:
    ticket = st.session_state['current_ticket']
    data = ticket['data']
    idx = ticket['index']
    
    # --- Top Info Row ---
    c1, c2, c3 = st.columns([1.5, 1, 1])
    
    with c1: # Name & Pinyin
        st.markdown("<p class='label-font'>真实姓名 (Name)</p>", unsafe_allow_html=True)
        st.markdown(f"<span><span class='big-font'>{data.get('name')}</span> <span class='pinyin-font'>({data.get('pinyin')})</span></span>", unsafe_allow_html=True)
        
    with c2: # Phone
        st.markdown("<p class='label-font'>手机号 (Phone)</p>", unsafe_allow_html=True)
        st.markdown(f"<div class='big-font'>{data.get('phone')}</div>", unsafe_allow_html=True)

    with c3: # Device
        st.markdown("<p class='label-font'>设备 (Device)</p>", unsafe_allow_html=True)
        st.info(data.get('device', 'N/A'))
        
    st.divider()
    
    # --- Verify Row (Pass & Location) ---
    v1, v2 = st.columns(2)
    
    with v1:
        st.caption("通行证 (ID Pass)")
        pass_val = data.get('pass_id', 'N/A')
        # Check Button
        if st.button(f"验证: {pass_val}", key="btn_check_pass", help="点击确认一致"):
            st.session_state['check_pass'] = True
        
        if st.session_state['check_pass']:
            st.markdown(f"<div class='verified'>✅ {pass_val} (已核对)</div>", unsafe_allow_html=True)
            
    with v2:
        st.caption("常住地 (Location)")
        loc_val = data.get('location', 'N/A')
        if st.button(f"验证: {loc_val}", key="btn_check_loc"):
            st.session_state['check_loc'] = True
            
        if st.session_state['check_loc']:
            st.markdown(f"<div class='verified'>✅ {loc_val} (已核对)</div>", unsafe_allow_html=True)

    st.divider()

    # --- Actions ---
    n_col, _ = st.columns([3, 1])
    with n_col:
        note_text = st.text_input("📝 备注 (R列) - 可选", placeholder="在此输入特殊情况...")

    b1, b2, b3 = st.columns(3)
    
    def do_submit(action):
        payload = {"note": note_text}
        ok = logic.submit_ticket(idx, action, st.session_state['user_name'], payload)
        if ok:
            st.toast("✅ 提交成功")
            load_new_ticket()
        else:
            st.error("提交失败")

    with b1:
        if st.button("🟢 完美通过"):
            do_submit('PASS')
    with b2:
        if st.button("🔴 拒绝/不符"):
            do_submit('FAIL')
    with b3:
        if st.button("🟡 未接/挂断"):
            do_submit('NO_ANSWER')

# Admin
if st.session_state['user_name'] == "Admin":
    st.divider()
    if st.button("Debug: Show Raw Data"):
        st.dataframe(logic.get_dataframe())


