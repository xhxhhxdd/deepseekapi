import streamlit as st
from openai import OpenAI
import uuid
import json
import os
import tempfile

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

# ---------- 数据文件 ----------
DATA_FILE = "conversations.json"

def save_conversations():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.conversations, f, ensure_ascii=False, indent=2)

def load_conversations():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def read_uploaded_file(uploaded_file):
    if uploaded_file is None:
        return None
    file_type = uploaded_file.name.split(".")[-1].lower()
    try:
        if file_type == "txt":
            return uploaded_file.getvalue().decode("utf-8")
        elif file_type == "pdf":
            from PyPDF2 import PdfReader
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            reader = PdfReader(tmp_path)
            text = "".join([page.extract_text() or "" for page in reader.pages])
            os.unlink(tmp_path)
            return text.strip()
        elif file_type in ["doc", "docx"]:
            from docx import Document
            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            doc = Document(tmp_path)
            text = "\n".join([p.text for p in doc.paragraphs])
            os.unlink(tmp_path)
            return text.strip()
        else:
            return None
    except Exception as e:
        return f"[文件读取失败: {str(e)}]"

# ---------- 初始化 ----------
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

if "current_page" not in st.session_state:
    st.session_state.current_page = "聊天"

current_conv = st.session_state.conversations[st.session_state.current_conv_id]

# ---------- 侧边栏 ----------
with st.sidebar:
    st.selectbox("功能", ["聊天", "JD生成器", "简历匹配", "面试题生成", "培训大纲"], key="current_page")
    st.divider()

    if st.session_state.current_page == "聊天":
        col1, col2 = st.columns(2)
        with col1:
            st.selectbox("模式", ["高速响应", "深度推理"], key="model_mode")
        with col2:
            new_template = st.selectbox("角色", list(PROMPT_TEMPLATES.keys()),
                                        index=list(PROMPT_TEMPLATES.keys()).index(current_conv.get("template", "通用助手")))
            if new_template != current_conv.get("template", "通用助手"):
                current_conv["template"] = new_template
                current_conv["messages"][0] = {"role": "system", "content": PROMPT_TEMPLATES[new_template]}
                save_conversations()
                st.rerun()

        st.divider()
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
        conv_ids = list(st.session_state.conversations.keys())
        for cid in conv_ids:
            conv = st.session_state.conversations[cid]
            if conv["title"] == "新对话" and len(conv["messages"]) > 1:
                for m in conv["messages"]:
                    if m["role"] == "user":
                        conv["title"] = m["content"][:20]
                        break
            is_current = (cid == st.session_state.current_conv_id)
            bg = "#e6f0ff" if is_current else "transparent"
            st.markdown(f'<div style="background:{bg};padding:0.3rem 0.5rem;border-radius:4px;margin-bottom:2px;">', unsafe_allow_html=True)
            if st.button(conv["title"], key=f"sel_{cid}", use_container_width=True):
                st.session_state.current_conv_id = cid
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# ---------- 主区域 ----------
if st.session_state.current_page == "聊天":
    # 显示聊天记录
    for msg in current_conv["messages"]:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

    # 固定底部输入区：使用 st.chat_input 自动固定，并在其上方加文件上传小框
    # 由于 st.chat_input 本身就是固定在底部的，我们在它上面再加一个极窄的上传区域
    col_upload, _ = st.columns([1, 20])
    with col_upload:
        uploaded_file = st.file_uploader("", type=["pdf", "doc", "docx", "txt"], label_visibility="collapsed", key="file_upload")

    prompt = st.chat_input("输入你的问题...")

    # 处理发送（chat_input 回车或点击发送）
    if prompt or uploaded_file:
        file_content = None
        # 处理上传文件（如果有）
        if uploaded_file is not None:
            file_content = read_uploaded_file(uploaded_file)
            if file_content and not file_content.startswith("["):
                file_msg = f"上传了文件: {uploaded_file.name}\n\n内容:\n{file_content[:8000]}"
            else:
                file_msg = file_content if file_content else "[文件无法识别]"
            current_conv["messages"].append({"role": "user", "content": file_msg})
            with st.chat_message("user"):
                st.write(file_msg)

        if prompt and prompt.strip():
            current_conv["messages"].append({"role": "user", "content": prompt.strip()})
            with st.chat_message("user"):
                st.write(prompt.strip())

        # 有内容才调API
        if (prompt and prompt.strip()) or uploaded_file is not None:
            with st.chat_message("assistant"):
                model = "deepseek-reasoner" if st.session_state.model_mode == "深度推理" else "deepseek-chat"
                stream = client.chat.completions.create(
                    model=model,
                    messages=current_conv["messages"],
                    stream=True
                )
                response = st.write_stream(stream)
            current_conv["messages"].append({"role": "assistant", "content": response})

            if current_conv["title"] == "新对话" and prompt and prompt.strip():
                current_conv["title"] = prompt.strip()[:20]

            save_conversations()
            # 清空文件上传状态（不好清，rerun 会重置组件，但文件上传组件会保留，可尝试用 key 重置）
            st.session_state.file_upload = None
            st.rerun()

# ---------- HR工具页面 ----------
elif st.session_state.current_page == "JD生成器":
    st.header("JD生成器")
    job_title = st.text_input("岗位名称", placeholder="例如：高级招聘专员")
    department = st.text_input("部门", placeholder="例如：人力资源部")
    requirements = st.text_area("关键要求（每行一个）", placeholder="例如：\n3年以上招聘经验\n熟悉各类招聘渠道")
    if st.button("生成JD", use_container_width=True):
        prompt = f"请根据以下信息撰写一份专业的招聘JD：\n岗位：{job_title}\n部门：{department}\n要求：{requirements}\n格式包括：岗位职责、任职要求、加分项。"
        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )
            result = st.write_stream(stream)
        st.session_state["jd_result"] = result
    if "jd_result" in st.session_state:
        st.text_area("生成的JD", st.session_state["jd_result"], height=300)

elif st.session_state.current_page == "简历匹配":
    st.header("简历与JD匹配度分析")
    jd_text = st.text_area("职位描述 (JD)", height=150)
    resume_text = st.text_area("候选人简历", height=150)
    if st.button("分析匹配度", use_container_width=True):
        prompt = f"请分析以下简历与职位描述的匹配度，给出1-10分的评分，并列出匹配点和不足：\n\n职位描述:\n{jd_text}\n\n简历:\n{resume_text}"
        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )
            result = st.write_stream(stream)
        st.session_state["match_result"] = result
    if "match_result" in st.session_state:
        st.text_area("分析结果", st.session_state["match_result"], height=300)

elif st.session_state.current_page == "面试题生成":
    st.header("面试题生成器")
    position = st.text_input("目标岗位", placeholder="例如：产品经理")
    interview_type = st.selectbox("面试类型", ["行为面试", "情景模拟", "专业问题", "压力面试"])
    if st.button("生成问题", use_container_width=True):
        prompt = f"为{position}岗位生成5道{interview_type}类面试题，并附上简要的评估要点。"
        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )
            result = st.write_stream(stream)
        st.session_state["question_result"] = result
    if "question_result" in st.session_state:
        st.text_area("生成的面试题", st.session_state["question_result"], height=300)

elif st.session_state.current_page == "培训大纲":
    st.header("培训大纲生成")
    topic = st.text_input("培训主题", placeholder="例如：新员工入职培训")
    duration = st.text_input("时长", placeholder="例如：1天")
    audience = st.text_input("培训对象", placeholder="例如：新入职员工")
    if st.button("生成大纲", use_container_width=True):
        prompt = f"请为《{topic}》设计一份培训大纲，时长{duration}，对象{audience}。包括：培训目标、模块划分、每个模块的内容要点。"
        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )
            result = st.write_stream(stream)
        st.session_state["outline_result"] = result
    if "outline_result" in st.session_state:
        st.text_area("培训大纲", st.session_state["outline_result"], height=300)