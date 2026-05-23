import streamlit as st
from openai import OpenAI
import uuid
import json
import os

# ---------- 页面配置 ----------
st.set_page_config(page_title="AI助手", layout="wide")

# ---------- 加载 API Key ----------
client = OpenAI(
    api_key=st.secrets["DEEPSEEK_KEY"],
    base_url="https://api.deepseek.com"
)

# ---------- 提示词模板 ----------
PROMPT_TEMPLATES = {
    "通用助手": "你是一个友善、有用的助手，回答简洁清晰。",
    "HR顾问": "你是一个专业的人力资源顾问，擅长招聘、培训、绩效管理和劳动法规，回答专业且实用。",
    "学习导师": "你是一个耐心的学习导师，用通俗易懂的方式解释概念，善于举例和引导思考。",
    "文案润色": "你是一个文案润色专家，帮助优化文字表达，使其更流畅、专业、有说服力。",
}

# ---------- 文件路径 ----------
DATA_FILE = "conversations.json"

# ---------- 保存对话到文件 ----------
def save_conversations():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.conversations, f, ensure_ascii=False, indent=2)

# ---------- 从文件加载对话 ----------
def load_conversations():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

# ---------- 全局状态初始化 ----------
if "conversations" not in st.session_state:
    saved = load_conversations()
    if saved:
        st.session_state.conversations = saved
        st.session_state.current_conv_id = list(saved.keys())[0]
    else:
        first_id = str(uuid.uuid4())
        st.session_state.conversations = {
            first_id: {
                "title": "新对话",
                "template": "通用助手",
                "messages": [{"role": "system", "content": PROMPT_TEMPLATES["通用助手"]}]
            }
        }
        st.session_state.current_conv_id = first_id
        save_conversations()

if "model_mode" not in st.session_state:
    st.session_state.model_mode = "高速响应"

current_conv = st.session_state.conversations[st.session_state.current_conv_id]

# ---------- 侧边栏 ----------
with st.sidebar:
    # 响应模式（下拉框）
    st.selectbox(
        "响应模式",
        options=["高速响应", "深度推理"],
        index=0 if st.session_state.model_mode == "高速响应" else 1,
        key="model_mode"
    )

    # 助手角色（下拉框）
    new_template = st.selectbox(
        "助手角色",
        options=list(PROMPT_TEMPLATES.keys()),
        index=list(PROMPT_TEMPLATES.keys()).index(current_conv.get("template", "通用助手"))
    )
    if new_template != current_conv.get("template", "通用助手"):
        current_conv["template"] = new_template
        current_conv["messages"][0] = {"role": "system", "content": PROMPT_TEMPLATES[new_template]}
        save_conversations()
        st.rerun()

    st.divider()

    # 新建对话
    if st.button("新建对话", use_container_width=True):
        new_id = str(uuid.uuid4())
        st.session_state.conversations[new_id] = {
            "title": "新对话",
            "template": "通用助手",
            "messages": [{"role": "system", "content": PROMPT_TEMPLATES["通用助手"]}]
        }
        st.session_state.current_conv_id = new_id
        save_conversations()
        st.rerun()

    st.divider()

    # 对话列表
    for cid in list(st.session_state.conversations.keys()):
        conv = st.session_state.conversations[cid]
        if conv["title"] == "新对话" and len(conv["messages"]) > 1:
            for m in conv["messages"]:
                if m["role"] == "user":
                    conv["title"] = m["content"][:20]
                    break
        c1, c2 = st.columns([4, 1])
        with c1:
            label = f"> {conv['title']}" if cid == st.session_state.current_conv_id else conv["title"]
            if st.button(label, key=f"sw_{cid}", use_container_width=True):
                st.session_state.current_conv_id = cid
                st.rerun()
        with c2:
            if st.button("X", key=f"del_{cid}"):
                del st.session_state.conversations[cid]
                if st.session_state.current_conv_id == cid:
                    if st.session_state.conversations:
                        st.session_state.current_conv_id = next(iter(st.session_state.conversations))
                save_conversations()
                st.rerun()

# ---------- 主区域 ----------
for i, msg in enumerate(current_conv["messages"]):
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg["role"] == "assistant" and msg["content"]:
                c1, c2, _ = st.columns([1, 1, 4])
                with c1:
                    if st.button("复制", key=f"copy_{i}"):
                        st.toast("已复制到剪贴板")
                        st.session_state.clipboard = msg["content"]
                with c2:
                    if st.button("重新生成", key=f"regen_{i}"):
                        current_conv["messages"] = current_conv["messages"][:i]
                        save_conversations()
                        st.rerun()

if prompt := st.chat_input("输入你的问题..."):
    current_conv["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    if st.session_state.model_mode == "深度推理":
        model = "deepseek-reasoner"
    else:
        model = "deepseek-chat"

    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model=model,
            messages=current_conv["messages"],
            stream=True
        )
        response = st.write_stream(stream)

    current_conv["messages"].append({"role": "assistant", "content": response})

    if current_conv["title"] == "新对话":
        current_conv["title"] = prompt[:20]

    save_conversations()
    st.rerun()