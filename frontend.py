# frontend.py
import gradio as gr
from backend import chat_with_ai

# 创建聊天界面
demo = gr.ChatInterface(
    fn=chat_with_ai,
    title="AI助手",
    examples=["解释一下绩效管理", "帮我写一份招聘JD", "如何提升团队沟通效率"]
)

if __name__ == "__main__":
    demo.launch()