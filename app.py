import streamlit as st
import openai
import os
import requests
import json
import datetime
import socket
from dotenv import load_dotenv

def get_local_ip():
    """获取本机局域网IP地址"""
    try:
        # 创建一个临时socket连接来获取IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "无法获取IP"

# 加载环境变量
load_dotenv()

# 页面配置
st.set_page_config(
    page_title="AI学习周计划生成器",
    page_icon="📚",
    layout="wide"
)

# 页面标题和介绍
st.title("📚 AI学习周计划生成器")
st.markdown("""**基于Wisdom AI的简化版学习规划助手**

输入你的学习目标、主题和可用时间，获取个性化的一周学习计划。同时支持AI对话功能，解答学习相关问题。
""")

# 创建侧边栏
with st.sidebar:
    st.header("设置")
    
    # 显示访问信息
    st.subheader("🖥️ 访问信息")
    local_ip = get_local_ip()
    st.info(f"本机IP: `{local_ip}`")
    st.info(f"访问地址: `http://{local_ip}:8501`")
    st.caption("将此地址分享给校园网内的同学")
    st.markdown("---")
    
    # 模型提供商选择
    provider = st.selectbox(
        "选择模型提供商",
        ["DeepSeek (免费)", "OpenAI"]
    )
    
    # 根据提供商选择显示相应的API密钥输入
    if provider == "DeepSeek (免费)":
        api_key = st.text_input("DeepSeek API密钥", type="password",
                              placeholder="请输入你的DeepSeek API密钥...",
                              key="deepseek_api_key")
        # DeepSeek免费模型选择
        model = st.selectbox(
            "选择DeepSeek模型",
            ["deepseek-chat", "deepseek-coder"],
            key="deepseek_model"
        )
    else:
        # OpenAI API密钥输入
        api_key = st.text_input("OpenAI API密钥", type="password",
                              placeholder="请输入你的OpenAI API密钥...",
                              key="openai_api_key")
        # OpenAI模型选择
        model = st.selectbox(
            "选择OpenAI模型",
            ["gpt-3.5-turbo", "gpt-4"],
            key="openai_model"
        )
    
    st.markdown("---")
    st.info("💡 提示：为了获得最佳效果，请尽可能详细地描述你的学习需求")
    
    # 初始化会话状态
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # 初始化学习计划状态
    if "plan_placeholder" not in st.session_state:
        st.session_state["plan_placeholder"] = st.empty()
    if "learning_plan_md" not in st.session_state:
        st.session_state["learning_plan_md"] = ""
    
    # 重置对话按钮
    if st.button("重置对话", use_container_width=True):
        st.session_state.messages = []

# 创建标签页
tab1, tab2 = st.tabs(["📋 学习计划生成", "💬 AI对话助手"])

with tab1:
    # 主内容区域
    col1, col2 = st.columns([3, 1])

    with col1:
        # 用户输入表单
        with st.form("learning_plan_form"):
            st.subheader("你的学习需求")
            
            # 从URL读取prompt参数作为默认值
            raw = st.query_params.get("prompt", "")
            default_prompt = raw[0] if isinstance(raw, list) else raw
            
            learning_topic = st.text_input(
                "学习主题", 
                placeholder="例如：Python数据分析、机器学习基础、前端开发等"
            )
            
            learning_goal = st.text_area(
                "学习目标（可从网址自动带入）", 
                value=default_prompt,
                placeholder="你希望通过学习达到什么效果？有什么特定的知识点或技能需要掌握？",
                height=100
            )
            
            daily_hours = st.slider(
                "每天可用学习时间（小时）", 
                0.5, 8.0, 2.0, 0.5
            )
            
            learning_level = st.selectbox(
                "学习水平",
                ["初学者", "中级", "高级", "专家"]
            )
            
            special_needs = st.text_area(
                "特殊需求（可选）",
                placeholder="例如：喜欢视频学习、需要练习题、有特定资源偏好等",
                height=80
            )
            
            # 提交按钮
            submit_button = st.form_submit_button(
                "生成学习计划",
                use_container_width=True,
                type="primary"
            )

    with col2:
        # 示例计划预览
        st.subheader("示例计划")
        st.info("填写左侧表单并点击生成按钮，这里将显示你的个性化学习计划")
        
        with st.expander("示例计划结构"):
            st.markdown("""
            - **周一**：基础知识学习
            - **周二**：核心概念掌握
            - **周三**：实践练习
            - **周四**：进阶内容学习
            - **周五**：项目实践
            - **周末**：复习与总结
            """)

with tab2:
    # AI对话助手功能
    st.subheader("💬 AI学习助手对话")
    st.markdown("向AI助手提问关于学习计划、知识点或其他学习相关问题")
    
    # 显示对话历史
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # 用户输入
    if prompt := st.chat_input("请输入你的问题..."):
        # 检查API密钥
        if not api_key:
            st.error("请在侧边栏中输入API密钥")
        else:
            # 添加用户消息到对话历史
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # 显示用户消息
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # 显示AI正在输入
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                
                # 创建一个fallback回复函数
            def create_fallback_response(user_message):
                fallback_responses = [
                    "您好！关于学习计划的问题，我建议您关注基础知识的学习，制定合理的时间规划，并结合实践练习来巩固所学内容。",
                    "为了更好地帮助您，请提供更具体的学习主题和目标，我可以为您生成一个详细的学习计划。",
                    "在学习过程中，坚持每天的学习习惯非常重要。建议您将大目标分解为小任务，逐步完成。",
                    "学习是一个循序渐进的过程。请确保您理解了基础概念后再进入更复杂的内容。",
                    "实践是掌握技能的最佳方式。尝试将所学知识应用到实际项目中，这将大大提高您的学习效果。"
                ]
                # 根据用户问题长度选择不同的回复
                index = min(len(user_message) // 10, len(fallback_responses) - 1)
                return fallback_responses[index]
            
            # 调用AI生成回复
            try:
                if provider == "DeepSeek (免费)":
                    # 使用DeepSeek API
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {api_key}"
                    }
                    
                    api_base = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
                    url = f"{api_base}/chat/completions"
                    
                    # 构建消息历史
                    messages = [
                        {"role": "system", "content": "你是一位专业的学习助手，擅长解答各种学习问题，提供学习建议和指导。"}
                    ]
                    messages.extend(st.session_state.messages)
                    
                    data = {
                        "model": model,
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 2000
                    }
                    
                    try:
                        response = requests.post(url, headers=headers, data=json.dumps(data))
                        response.raise_for_status()
                        result = response.json()
                        full_response = result["choices"][0]["message"]["content"]
                    except requests.exceptions.HTTPError as e:
                        if "422" in str(e) or "Payment Required" in str(e):
                            # 当DeepSeek API返回支付错误时，使用本地fallback
                            st.warning("⚠️ DeepSeek API调用失败（支付错误），使用本地回复助手")
                            full_response = create_fallback_response(prompt)
                            full_response += "\n\n**注意**: 这是一个基础回复。要获取更准确的答案，请确保您的API密钥有效。"
                        else:
                            raise e
                    
                else:
                    # 使用OpenAI API
                    openai.api_key = api_key
                    if os.getenv("OPENAI_API_BASE"):
                        openai.api_base = os.getenv("OPENAI_API_BASE")
                    
                    # 构建消息历史
                    messages = [
                        {"role": "system", "content": "你是一位专业的学习助手，擅长解答各种学习问题，提供学习建议和指导。"}
                    ]
                    messages.extend(st.session_state.messages)
                    
                    response = openai.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=0.7,
                        max_tokens=2000
                    )
                    full_response = response.choices[0].message.content
                
                # 显示回复
                message_placeholder.markdown(full_response)
                
                # 添加AI回复到对话历史
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
            except Exception as e:
                # 所有其他错误都使用本地fallback
                error_msg = f"❌ 生成回复时出错: {str(e)}"
                st.warning(f"⚠️ API调用失败: {error_msg}，使用本地回复助手")
                full_response = create_fallback_response(prompt)
                full_response += "\n\n**注意**: 这是一个基础回复。要获取更准确的答案，请检查您的API设置。"
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})

# 计划生成函数
# 导出Markdown文件功能
def export_markdown_button(md_text: str, goal: str):
    filename = f"学习计划_{goal}_{datetime.datetime.now().strftime('%Y%m%d')}.md"
    st.download_button(
        label="📥 下载学习计划（Markdown）",
        data=md_text.encode("utf-8"),
        file_name=filename,
        mime="text/markdown",
        use_container_width=True
    )

# 创建一个本地fallback函数，当API调用失败时提供基础学习计划
def create_fallback_learning_plan(topic, goal, daily_hours, level, special_needs):
    """创建本地基础学习计划作为fallback，确保中文Markdown格式"""
    plan = f"""
# 总览
基于你的需求，这里提供了关于{topic}的基础学习计划。完整版本需要有效的API调用。

## 第1周
### 周一
- **上午**: {topic}基础知识入门 ({daily_hours/2}小时)
- **下午**: 核心概念理解与简单练习 ({daily_hours/2}小时)
- **关键概念**: 基础知识框架、核心术语
- **推荐资源**: [官方文档](https://example.com)、入门教程

### 周二
- **上午**: 核心功能学习与实践 ({daily_hours/2}小时)
- **下午**: 案例分析与应用 ({daily_hours/2}小时)
- **关键概念**: 主要功能模块、使用方法
- **推荐资源**: [在线课程](https://example.com)、示例代码

### 周三
- **上午**: 进阶内容学习 ({daily_hours/2}小时)
- **下午**: 实践练习与问题解决 ({daily_hours/2}小时)
- **关键概念**: 高级特性、常见问题
- **推荐资源**: [进阶教程](https://example.com)、技术博客

### 周四
- **上午**: 深入理解底层原理 ({daily_hours/2}小时)
- **下午**: 综合应用案例 ({daily_hours/2}小时)
- **关键概念**: 工作原理、优化方法
- **推荐资源**: 技术文章、[源码分析](https://example.com)

### 周五
- **上午**: 项目开发实践 ({daily_hours/2}小时)
- **下午**: 项目完善与调试 ({daily_hours/2}小时)
- **关键概念**: 实际应用、问题排查
- **推荐资源**: 项目示例、[调试指南](https://example.com)

### 周末
- **全天**: 复习、总结与扩展学习

## 学习资源
- 官方文档
- 在线课程平台
- 技术社区和论坛
- 推荐书籍

## 评估与调整
- 每周结束时评估学习进度
- 根据掌握程度调整下周计划
- 重点加强薄弱环节

**注意**: 这是一个简化版本的学习计划。要获取更个性化、更详细的计划，请确保:
1. 你的DeepSeek API密钥有效
2. 检查API密钥是否有足够的权限
3. 或尝试使用OpenAI API选项
"""
    return plan

def generate_learning_plan(provider, api_key, model, topic, goal, daily_hours, level, special_needs):
    """使用AI模型生成学习计划，包含fallback机制"""
    try:
        # 构建提示词
        prompt = f"""你是一个专业的学习规划顾问。请根据以下信息为用户创建一个详细的一周学习计划。

学习主题: {topic}
学习目标: {goal}
每天可用时间: {daily_hours}小时
学习水平: {level}
特殊需求: {special_needs}

请按照以下格式生成计划，确保计划具体、可执行且平衡:

## 整体学习目标
[简要总结一周学习目标]

## 每日详细计划
### 周一
- **上午**: [具体学习内容和建议时长]
- **下午**: [具体学习内容和建议时长]
- **关键概念**: [列出当日需要掌握的关键概念]
- **推荐资源**: [推荐的学习资源]

### 周二
[类似周一的格式]

### 周三
[类似周一的格式]

### 周四
[类似周一的格式]

### 周五
[类似周一的格式]

### 周末
[安排周末的复习、实践或项目时间]

## 学习建议
[提供2-3条针对该学习主题的具体建议]

## 完成标准
[列出可以判断学习成功的具体标准]
"""
        
        if provider == "DeepSeek (免费)":
            # 使用requests调用DeepSeek API
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            # 获取API基础URL，默认为官方地址
            api_base = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
            url = f"{api_base}/chat/completions"
            
            data = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "你是一名资深学习规划师。请只用中文输出，并严格使用Markdown格式（# 总览，## 第1周...，## 学习资源，## 评估与调整；使用有序/无序列表；资源用Markdown链接）。不要输出HTML。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            try:
                response = requests.post(url, headers=headers, data=json.dumps(data))
                response.raise_for_status()  # 检查HTTP错误
                result = response.json()
                return result["choices"][0]["message"]["content"]
            except requests.exceptions.HTTPError as e:
                if "422" in str(e) or "Payment Required" in str(e):
                    # 当DeepSeek API返回支付错误时，使用本地fallback
                    st.warning("⚠️ DeepSeek API调用失败（支付错误），使用本地学习计划生成器")
                    return create_fallback_learning_plan(topic, goal, daily_hours, level, special_needs)
                else:
                    raise e
            
        else:
            # 使用OpenAI API
            openai.api_key = api_key
            
            # 设置API基础URL（如果有）
            if os.getenv("OPENAI_API_BASE"):
                openai.api_base = os.getenv("OPENAI_API_BASE")
            
            response = openai.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "你是一名资深学习规划师。请只用中文输出，并严格使用Markdown格式（# 总览，## 第1周...，## 学习资源，## 评估与调整；使用有序/无序列表；资源用Markdown链接）。不要输出HTML。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
    except Exception as e:
        # 所有其他错误都使用本地fallback
        error_msg = f"❌ 生成计划时出错: {str(e)}"
        st.warning(f"⚠️ API调用失败: {error_msg}，使用本地学习计划生成器")
        return create_fallback_learning_plan(topic, goal, daily_hours, level, special_needs)

# 处理表单提交
if submit_button:
    # 验证输入
    if not learning_topic or not learning_goal:
        st.error("请填写学习主题和学习目标")
    elif not api_key:
        st.error("请输入OpenAI API密钥")
    else:
        # 显示加载状态
        with st.spinner("正在生成Markdown学习计划..."):
            # 生成学习计划
            learning_plan = generate_learning_plan(
                provider=provider,
                api_key=api_key,
                model=model,
                topic=learning_topic,
                goal=learning_goal,
                daily_hours=daily_hours,
                level=learning_level,
                special_needs=special_needs
            )
            
            # 判空与错误处理
            if not learning_plan or learning_plan.strip() == "" or learning_plan.startswith("❌"):
                st.error("生成学习计划失败，请重试")
            else:
                # 保存计划到session_state并显示
                st.session_state["learning_plan_md"] = learning_plan
                st.session_state["plan_placeholder"].markdown(learning_plan, unsafe_allow_html=False)
                
                # 添加导出功能
                export_markdown_button(st.session_state["learning_plan_md"], learning_goal)

# 不再需要单独定义plan_placeholder变量，使用session_state中的版本

# 计划显示区域（在tab1中）
with tab1:
    st.markdown("---")
    st.subheader("📋 你的学习计划")
    
    # 初始状态或没有计划时显示提示
    if not st.session_state["learning_plan_md"]:
        st.session_state["plan_placeholder"].info("你的个性化学习计划将在这里显示...")
    # 显示已保存的计划
    else:
        st.session_state["plan_placeholder"].markdown(st.session_state["learning_plan_md"])
        
        # 添加导出功能
        if st.session_state["learning_plan_md"]:
            export_markdown_button(st.session_state["learning_plan_md"], learning_goal)

# 页脚
st.markdown("---")
st.caption("© 2025 AI学习计划生成器 - 基于Wisdom AI的简化版本")