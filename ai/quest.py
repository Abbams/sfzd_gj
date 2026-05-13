import requests
import json
from typing import Optional, Dict, Any
from  models.problem import Problem
base_model="qwen3-coder:30b"
base_model_url="http://localhost:11434"

class OllamaClient:
    """
    本地 Ollama 模型调用客户端（一次问答，无历史）
    """

    def __init__(
        self,
        model: str = base_model,
        system_prompt: Optional[str] = """你是一个算法出题助手，工作是帮我补全优化题目，只以 JSON 格式回答，格式如下{  "id": "",
  "title": "",
  "description": "",
  "input_description": "",
  "output_description": "",
  "sample_input": "",
  "sample_output": "",
  "solution_code": "#include<bits/stdc++.h>\nusing namespace std;\nint main()\n{\n    return 0;\n}",
  "generator_path": "datamaker.py",
  "language": "c++",
  "data_files": []
}""",
        base_url: str = base_model_url,
        **kwargs
    ):
        """
        初始化 Ollama 客户端

        :param model: 模型名称（需已通过 `ollama pull` 下载）
        :param system_prompt: 系统提示词，用于设定模型行为或输出格式
        :param base_url: Ollama 服务地址，默认为本地 11434 端口
        :param kwargs: 其他 API 参数，如 temperature, top_p, max_tokens 等
        """
        self.model = model
        self.system_prompt = system_prompt
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/api/chat"
        self.kwargs = kwargs

    def query(self, user_prompt: str, **override_params) -> str:
        """
        发送一次问答请求，返回模型回答

        :param user_prompt: 用户输入的问题
        :param override_params: 临时覆盖初始化时的 API 参数（如 temperature）
        :return: 模型返回的文本
        """
        messages = []

        # 添加系统提示（如果存在）
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})

        # 添加用户消息
        messages.append({"role": "user", "content": user_prompt})

        # 合并参数
        params = {
            "model": self.model,
            "messages": messages,
            "stream": False,          # 非流式，一次返回完整结果
            **self.kwargs,
            **override_params
        }

        try:
            response = requests.post(self.api_url, json=params, timeout=60)
            response.raise_for_status()
            data = response.json()
            # 返回助手的回复内容
            return data.get("message", {}).get("content", "")
        except requests.exceptions.RequestException as e:
            return f"[网络错误] {e}"
        except json.JSONDecodeError:
            return "[解析错误] 返回内容不是有效的 JSON"
        except Exception as e:
            return f"[未知错误] {e}"

def ai_rewrite(problem: Problem):
    client = OllamaClient()
    response_text = client.query(problem.description)

    # 1. 清洗返回文本，提取 JSON 部分（去除可能的 markdown 代码块）
    cleaned = response_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    # 2. 解析 JSON 并更新指定字段
    try:
        data = json.loads(cleaned)
        if "description" in data:
            problem.description = data["description"]
        if "input_description" in data:
            problem.input_description = data["input_description"]
        if "output_description" in data:
            problem.output_description = data["output_description"]
        if "solution_code" in data:
            problem.solution_code = data["solution_code"]
        print("✅ 题目描述、输入说明、输出说明已更新")
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败: {e}")
        print("原始返回内容:", response_text)
