import os
import anthropic
import httpx
from typing import Optional, Dict, Any
import time
try:
    from .config import AI_CONFIG
except ImportError:
    # Fallback for direct execution
    AI_CONFIG = {
        'API_KEY': os.getenv('ANTHROPIC_API_KEY', ''),
        'BASE_URL': os.getenv('ANTHROPIC_BASE_URL', 'https://api.minimaxi.com/anthropic'),
        'MODEL': os.getenv('ANTHROPIC_MODEL', 'MiniMax-M2.1'),
        'TIMEOUT': int(os.getenv('API_TIMEOUT_MS', '60000')),
        'PROXY': {
            'http': os.getenv('HTTP_PROXY'),
            'https': os.getenv('HTTPS_PROXY')
        } if os.getenv('HTTP_PROXY') else None
    }

class UnifiedAIClient:
    """
    统一的 AI 客户端，支持多种 API 提供商
    参考 Claude Code 配置方式，通过环境变量控制
    """

    def __init__(self, ai_config: Optional[Dict[str, Any]] = None):
        config = dict(AI_CONFIG)
        if ai_config:
            for key in ['API_KEY', 'BASE_URL', 'MODEL', 'TIMEOUT', 'PROXY']:
                if key in ai_config and ai_config[key] not in (None, ''):
                    config[key] = ai_config[key]

        auth_token = None
        if ai_config and ai_config.get('AUTH_TOKEN'):
            auth_token = ai_config.get('AUTH_TOKEN')
        elif os.getenv('ANTHROPIC_AUTH_TOKEN'):
            auth_token = os.getenv('ANTHROPIC_AUTH_TOKEN')

        self.api_key = config['API_KEY']
        self.base_url = config['BASE_URL']
        self.model = config['MODEL']
        self.timeout = float(config['TIMEOUT']) / 1000.0  # Convert ms to seconds
        self.proxies = config['PROXY']
        self.retry_count = int(os.getenv('AI_RETRY_COUNT', '2'))
        self.retry_backoff = float(os.getenv('AI_RETRY_BACKOFF', '0.8'))

        if not self.api_key and not auth_token:
            raise ValueError("AI API 未配置：请设置 ANTHROPIC_API_KEY 或 ANTHROPIC_AUTH_TOKEN")

        # Normalize proxy input
        if isinstance(self.proxies, str):
            self.proxies = {'http': self.proxies, 'https': self.proxies}

        # Configure httpx client with proxy if available
        http_client = None
        if self.proxies:
            http_client = httpx.Client(proxies=self.proxies)

        self.client = anthropic.Anthropic(
            api_key=self.api_key or None,
            auth_token=auth_token,
            base_url=self.base_url,
            timeout=self.timeout,
            http_client=http_client
        )

    def analyze(self, prompt: str, system_prompt: str = "", max_tokens: int = 4096) -> str:
        """调用 AI 分析"""
        messages = [{"role": "user", "content": prompt}]
        
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": messages
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt

        last_error = None
        for attempt in range(self.retry_count + 1):
            try:
                response = self.client.messages.create(**kwargs)
                return self._extract_text(response)
            except Exception as e:
                last_error = e
                print(f"AI API Call Error (attempt {attempt + 1}): {e}")
                if attempt < self.retry_count:
                    time.sleep(self.retry_backoff * (2 ** attempt))

        raise last_error

    def _extract_text(self, response) -> str:
        """从 Anthropic 响应中提取文本内容"""
        parts = []
        for block in getattr(response, 'content', []) or []:
            block_type = getattr(block, 'type', None)
            if block_type == 'text':
                parts.append(getattr(block, 'text', ''))
        return "".join(parts).strip()
