"""
DeepSeek学习助手 - 智能模型选择版
部署到 Railway
运行: python app.py
"""
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import time

app = Flask(__name__)
CORS(app)

# 配置 - Railway可以设置环境变量
API_KEY = os.environ.get("API_KEY", "sk-fetdccvrxjtkihpvzhovtageofnbpvmvpsnxmtprfprgowfg")
API_URL = "https://api.siliconflow.cn/v1/chat/completions"

def select_intelligent_config(user_message):
    """
    智能选择模型配置 - 基于测试结果优化
    """
    msg = user_message.lower()
    length = len(msg)

    # 1. 代码问题 → 用代码专用模型（质量优先）
    code_keywords = ["代码", "编程", "函数", "def ", "import ", "class ", "算法", "数据结构"]
    if any(keyword in msg for keyword in code_keywords):
        print("🎯 检测到代码问题，使用代码专用模型")
        return {
            "model": "Qwen/Qwen2.5-Coder-7B-Instruct",
            "temperature": 0.1,      # 低随机性，代码需要精确
            "max_tokens": 2000,      # 代码可能较长
            "timeout": 20,
            "description": "代码专用模式"
        }

    # 2. 复杂解释问题 → 用大模型保证质量
    complex_keywords = ["解释", "详细", "原理", "机制", "为什么", "如何工作", "分析"]
    is_complex = (length > 100) or any(keyword in msg for keyword in complex_keywords)

    if is_complex:
        print("🎯 检测到复杂问题，使用大模型")
        return {
            "model": "Qwen/Qwen2.5-32B-Instruct",  # 32B又快又好
            "temperature": 0.7,
            "max_tokens": 2000,
            "timeout": 25,
            "description": "复杂问题模式"
        }

    # 3. 中等问题 → 用平衡模型
    elif length > 30:
        print("🎯 中等长度问题，使用平衡模型")
        return {
            "model": "Qwen/Qwen2.5-14B-Instruct",  # 14B平衡优秀
            "temperature": 0.5,
            "max_tokens": 1500,
            "timeout": 15,
            "description": "标准模式"
        }

    # 4. 简单问题 → 用最快模型
    else:
        print("🎯 简单问题，使用最快模型")
        return {
            "model": "Qwen/Qwen2-7B-Instruct",  # 老版本但最快
            "temperature": 0.3,
            "max_tokens": 800,
            "timeout": 10,
            "description": "快速模式"
        }

@app.route('/api/chat', methods=['POST'])
def chat():
    """聊天接口 - 智能模型选择版"""
    data = request.json

    if not data:
        return jsonify({"success": False, "response": "请提供JSON数据"}), 400

    user_message = data.get('message', '').strip()

    if not user_message:
        return jsonify({"success": False, "response": "消息不能为空"}), 400

    print(f"📱 收到消息: {user_message} ({len(user_message)}字符)")

    # 智能选择配置
    config = select_intelligent_config(user_message)
    print(f"⚙️  选择配置: {config['description']}")
    print(f"🤖 使用模型: {config['model']}")
    print(f"⏱️  超时设置: {config['timeout']}秒")

    # 构建请求
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    messages = [
        {
            "role": "system",
            "content": "你是一个专业的学习助手'DeepSeek学习助手'。请用简洁准确的中文回答。复杂问题请分点说明，代码问题请提供可运行的示例。"
        },
        {"role": "user", "content": user_message}
    ]

    payload = {
        "model": config["model"],
        "messages": messages,
        "temperature": config["temperature"],
        "max_tokens": config["max_tokens"],
        "top_p": 0.9,
        "stream": False
    }

    try:
        # 调用API
        start_time = time.time()
        response = requests.post(API_URL, headers=headers, json=payload,
                               timeout=config["timeout"])
        elapsed = time.time() - start_time

        print(f"⏱️  API响应时间: {elapsed:.2f}秒")

        if response.status_code == 200:
            result = response.json()
            ai_response = result["choices"][0]["message"]["content"]

            print(f"✅ 成功! 响应长度: {len(ai_response)}字符")

            return jsonify({
                "success": True,
                "response": ai_response,
                "model_used": config["model"],
                "response_time": f"{elapsed:.2f}s",
                "mode": config["description"],
                "timestamp": int(time.time())
            })

        else:
            error_detail = response.text[:200]
            print(f"❌ API错误 {response.status_code}: {error_detail}")

            # 优雅降级：如果大模型失败，尝试小模型
            if response.status_code == 400 and config["model"] != "Qwen/Qwen2-7B-Instruct":
                print("🔄 尝试降级到快速模型...")
                # 这里可以添加降级逻辑

            return jsonify({
                "success": False,
                "response": f"请求失败 (错误 {response.status_code})",
                "model_used": config["model"],
                "timestamp": int(time.time())
            }), 500

    except requests.exceptions.Timeout:
        print(f"❌ 请求超时 ({config['timeout']}秒)")
        return jsonify({
            "success": False,
            "response": f"问题 '{user_message[:30]}...' 响应超时。\n\n建议：\n• 简化问题描述\n• 拆分复杂问题\n• 稍后重试",
            "model_used": config["model"],
            "timeout_set": config["timeout"],
            "timestamp": int(time.time())
        }), 504

    except Exception as e:
        print(f"❌ 服务器错误: {str(e)[:100]}")
        return jsonify({
            "success": False,
            "response": "服务器内部错误，请稍后重试",
            "timestamp": int(time.time())
        }), 500

@app.route('/api/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        "status": "running",
        "service": "DeepSeek学习助手",
        "available_models": [
            "Qwen/Qwen2-7B-Instruct (快速)",
            "Qwen/Qwen2.5-14B-Instruct (标准)",
            "Qwen/Qwen2.5-32B-Instruct (强大)",
            "Qwen/Qwen2.5-Coder-7B-Instruct (代码)"
        ],
        "timestamp": int(time.time())
    })

@app.route('/api/models', methods=['GET'])
def list_models():
    """查看可用模型"""
    return jsonify({
        "success": True,
        "models": {
            "fast": {"model": "Qwen/Qwen2-7B-Instruct", "desc": "最快响应，简单问题"},
            "standard": {"model": "Qwen/Qwen2.5-14B-Instruct", "desc": "平衡性能，中等问题"},
            "powerful": {"model": "Qwen/Qwen2.5-32B-Instruct", "desc": "高质量回答，复杂问题"},
            "coder": {"model": "Qwen/Qwen2.5-Coder-7B-Instruct", "desc": "代码专用，编程问题"}
        }
    })

@app.route('/')
def home():
    """首页"""
    return """
    <h1>🚀 DeepSeek学习助手后端</h1>
    <p>已部署到 Railway</p>
    <ul>
        <li><a href="/api/health">健康检查</a></li>
        <li><a href="/api/models">查看模型</a></li>
    </ul>
    <p>API地址: /api/chat (POST)</p>
    """


if __name__ == '__main__':
    # 关键修改：将默认端口从 5000 改为 8080
    port = int(os.environ.get("PORT", 8080))  # 这里改了！
    print("=" * 60)
    print("🚀 DeepSeek学习助手服务器 - Zeabur部署版")
    print("=" * 60)
    print(f"🌐 服务端口: {port}")
    print("=" * 60)
    app.run(host='0.0.0.0', port=port, debug=False)
