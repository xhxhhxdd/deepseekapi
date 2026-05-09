import streamlit as st
from openai import OpenAI
import uuid

st.set_page_config(page_title="AI助手", page_icon="🤖", layout="wide")

# 用 Streamlit Secrets 管理 Key
client = OpenAI(
api_key=st.secrets["DEEPSEEK_KEY"],
    base_url="https://api.deepseek.com"
)

# 初始化对话管理
if "conversations" not in st.session_state:
    first_id = str(uuid.uuid4())
    st.session_state.conversations = {
        first_id: {"title": "新对话", "messages": [{"role": "system", "content": "你是一个友善的助手。"}]}
    }
    st.session_state.current_conv_id = first_id

# 侧边栏
with st.sidebar:
    st.title("对话管理")
    if st.button("＋ 新建对话", use_container_width=True):
        new_id = str(uuid.uuid4())
        st.session_state.conversations[new_id] = {
            "title": "新对话",
            "messages": [{"role": "system", "content": "你是一个友善的助手。"}]
        }
        st.session_state.current_conv_id = new_id
        st.rerun()
    st.divider()
    for cid in list(st.session_state.conversations.keys()):
        conv = st.session_state.conversations[cid]
        if conv["title"] == "新对话" and len(conv["messages"]) > 1:
            for m in conv["messages"]:
                if m["role"] == "user":
                    conv["title"] = m["content"][:20]
                    break
        c1, c2 = st.columns([4, 1])
        with c1:
            if st.button(f"📄 {conv['title']}", key=f"sw_{cid}", use_container_width=True):
                st.session_state.current_conv_id = cid
                st.rerun()
        with c2:
            if st.button("🗑", key=f"del_{cid}"):
                del st.session_state.conversations[cid]
                if st.session_state.current_conv_id == cid:
                    st.session_state.current_conv_id = next(iter(st.session_state.conversations)) if st.session_state.conversations else None
                st.rerun()

# 主聊天区
conv = st.session_state.conversations[st.session_state.current_conv_id]
st.title("🤖 AI 助手")
for msg in conv["messages"]:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

if prompt := st.chat_input("说点什么..."):
    conv["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model="deepseek-chat",
            messages=conv["messages"],
            stream=True
        )
        response = st.write_stream(stream)
    conv["messages"].append({"role": "assistant", "content": response})
    if conv["title"] == "新对话":
        conv["title"] = prompt[:20]
    st.rerun()