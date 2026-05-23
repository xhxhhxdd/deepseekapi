# backend.py
from openai import OpenAI
import os

# 从环境变量读取 API Key，这是一种安全实践
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

def chat_with_ai(message, history):
    """
    这是与AI交互的核心函数。它接收用户输入和对话历史，调用API，并逐步返回响应。

    Args:
        message (str): 用户当前发送的消息。
        history (list): Gradio ChatInterface 标准的对话历史格式。
                        是一个由 (user_msg, bot_msg) 元组组成的列表。

    Yields:
        str: 逐步生成完整的 AI 回复。
    """
    # 1. 将对话历史转换为 API 所需的 messages 格式
    messages = [{"role": "system", "content": "你是一个专业、可靠的AI助手。"}]
    for human, assistant in history:
        messages.append({"role": "user", "content": human})
        messages.append({"role": "assistant", "content": assistant})
    messages.append({"role": "user", "content": message})

    # 2. 调用 DeepSeek API，设置 stream=True 以接收流式响应
    stream = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        stream=True
    )

    # 3. 遍历响应流，逐步拼接并返回完整内容
    partial_response = ""
    for chunk in stream:
        if chunk.choices[0].delta.content:
            partial_response += chunk.choices[0].delta.content
            yield partial_response