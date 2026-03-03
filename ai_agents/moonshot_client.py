import os
from typing import List, Optional
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

class MoonshotClient:
    """
    Moonshot (Kimi) API client wrapper using the OpenAI-compatible SDK.
    """
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.moonshot.cn/v1"):
        self.api_key = api_key or os.getenv("MOONSHOT_API_KEY")
        if not self.api_key:
            raise ValueError("MOONSHOT_API_KEY not found in environment or passed to constructor.")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=base_url,
        )

    def chat_completion(self, messages: List[dict], model: str = "moonshot-v1-8k", temperature: float = 0.3):
        """
        Send a chat completion request to Moonshot.
        """
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error calling Moonshot API: {str(e)}"

if __name__ == "__main__":
    # Quick test
    client = MoonshotClient()
    response = client.chat_completion([
        {"role": "system", "content": "你是 Kimi，由 Moonshot AI 提供的对话机器人。"},
        {"role": "user", "content": "你好，请简单介绍一下你自己。"}
    ])
    print(response)
