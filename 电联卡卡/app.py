import streamlit as st
import time
from utils import logic

# --- Page Config ---
st.set_page_config(page_title="Call Center Helper", page_icon="📞", layout="wide")

# --- Custom CSS ---
st.markdown("""
<style>
    .big-font { font-size: 36px !important; font-weight: bold; color: #1E88E5; }
    .label-font { font-size: 18px; color: #555; }
    .stButton button { width: 100%; height: 60px; font-size: 20px; font-weight: bold; }
    /* Pass Button Green */
    div[data-testid="stHorizontalBlock"] button[kind="primary"] { background-color: #4CAF50; border-color: #4CAF50; }
</style>
""", unsafe_allow_html=True)

# --- Session State Init ---
if 'user_name' not in st.session_state:
    st.session_state['user_name'] = ""
if 'current_ticket' not in st.session_state:
    st.session_state['current_ticket'] = None # Stores {'index': 123, 'data': {...}}

# --- Sidebar: Login ---
with st.sidebar:
    st.title("📞 电话招募系统")
    
    # User Selection
    users = ["Caller_01", "Caller_02", "Caller_03", "Caller_04", "Admin"]
    selected_user = st.selectbox("当前员工 / User", [""] + users, index=0)
    
    if selected_user:
        st.session_state['user_name'] = selected_user
        st.success(f"Hi, {selected_user}")
    else:
        st.warning("请选择姓名以开始")
        st.stop()
        
    st.divider()
    st.info("💡 提示: \n1. 系统会自动抢号Locked \n2. 提交后自动下一条 \n3. 禁止多开同一账号")

# --- Main Logic ---

def load_new_ticket():
    with st.spinner(f"{st.session_state['user_name']} 正在自动领号中..."):
        idx, data = logic.find_and_lock_ticket(st.session_state['user_name'])
        if idx:
            st.session_state['current_ticket'] = {"index": idx, "data": data}
            st.rerun()
        else:
            st.session_state['current_ticket'] = None
            st.error("暂无可用数据，或全部已完成！")

# If no ticket loaded, try load one
if st.session_state['current_ticket'] is None:
    if st.button("🚀 开始领号 / Start Work", type="primary"):
        load_new_ticket()
else:
    # --- Workflow UI ---
    ticket = st.session_state['current_ticket']
    data = ticket['data']
    ticket_idx = ticket['index']
    
    # Header Info
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        st.markdown(f"<div class='label-font'>目标号码 / Phone</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='big-font'>{data.get('phone', 'N/A')}</div>", unsafe_allow_html=True)
    with c2:
        st.metric("ID / Account", data.get('account', 'N/A'))
    with c3:
        st.metric("常住地", data.get('location', 'Unknown'))
        
    st.divider()
    
    # Script & Info
    info_col, script_col = st.columns([1, 2])
    
    with info_col:
        st.subheader("📋 信息核对")
        st.info(f"**设备信息 (Col P)**: {data.get('device', 'N/A')}")
        st.text("请确认对方是否成年，设备是否符合要求。")
        
        # Audio Placeholder
        st.audio(f"https://example.com/audio/{data.get('account')}.mp3", format="audio/mp3")
        st.caption("录音文件名: " + f"{data.get('account')}.mp3")

    with script_col:
        st.subheader("🗣️ 话术流程")
        st.markdown("""
        1. **确认身份**: "请问是尾号XXXX的机主吗？"
        2. **核对设备**: "您现在使用的手机型号是 `{}` 吗？是否只有这一台？"
        3. **确认时间**: "接下来2天是否有空参与测试？"
        4. **索要QQ**: "请提供一下QQ号方便拉群。"
        """.format(data.get('device', '...')))
        
        # Input for Pass scenario
        new_qq = st.text_input("📝 录入新 QQ (仅通过时填写)", key="input_qq")

    st.divider()
    
    # Action Buttons
    st.subheader("处理结果 / Action")
    
    b1, b2, b3 = st.columns(3)
    
    with b1:
        if st.button("🟢 完美通过 / Pass", type="primary"):
            if not new_qq:
                st.toast("⚠️ 请务必填写 QQ 号！")
            else:
                success = logic.submit_ticket(ticket_idx, 'PASS', st.session_state['user_name'], {'qq': new_qq})
                if success:
                    st.toast("✅ 提交成功！")
                    load_new_ticket()
                else:
                    st.error("提交失败，请重试")

    with b2:
        if st.button("🔴 拒绝/设备不符 / Reject"):
            success = logic.submit_ticket(ticket_idx, 'FAIL', st.session_state['user_name'])
            if success:
                st.toast("提交成功")
                load_new_ticket()
    
    with b3:
        if st.button("🟡 无人接/挂断 / No Answer"):
             success = logic.submit_ticket(ticket_idx, 'NO_ANSWER', st.session_state['user_name'])
             if success:
                st.toast("已标记未接")
                load_new_ticket()

# Admin Section
if st.session_state['user_name'] == "Admin":
    st.divider()
    st.subheader("Admin Dashboard")
    if st.button("Refresh Stats"):
        df = logic.get_dataframe()
        if not df.empty:
            st.dataframe(df)
            counts = df.iloc[:, logic.COL_STAFF].value_counts() # Count by staff
            st.bar_chart(counts)
