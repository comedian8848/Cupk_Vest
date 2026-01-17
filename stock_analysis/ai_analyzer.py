import json
import logging
from typing import Dict, Any, Optional
try:
    from .ai_client import UnifiedAIClient
except ImportError:
    from ai_client import UnifiedAIClient

logger = logging.getLogger(__name__)

class AIAnalyzer:
    def __init__(self, ai_config: Optional[Dict[str, Any]] = None):
        self.client = UnifiedAIClient(ai_config=ai_config)

    def generate_report(self, stock_data: Dict[str, Any], industry_avg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        基于股票数据生成 AI 分析报告
        """
        prompt = self._build_prompt(stock_data, industry_avg)
        system_prompt = self._build_system_prompt()
        
        try:
            response_text = self.client.analyze(prompt, system_prompt=system_prompt)
            # Try to extract JSON from the response if it contains markdown code blocks
            json_text = self._extract_json(response_text)
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.debug(f"Raw response: {response_text}")
            return {
                "error": "Failed to parse AI response",
                "raw_response": response_text
            }
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return {"error": str(e)}

    def _extract_json(self, text: str) -> str:
        """从文本中提取 JSON"""
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

    def _build_system_prompt(self) -> str:
        return """你是拥有20年经验的资深金融分析师，精通基本面分析、估值建模、财报解读。

分析框架:
1. 读取财务数据（营收、利润、现金流、ROE等）
2. 对比行业平均水平
3. 分析增长趋势和质量
4. 评估估值合理性
5. 给出明确的投资建议

输出要求:
- 必须输出合法的 JSON 格式
- 投资建议需包含评级、目标价、止损价、建议仓位
- 预测需包含乐观/中性/悲观三个区间
"""

    def _build_prompt(self, data: Dict[str, Any], industry_avg: Optional[Dict[str, Any]]) -> str:
        # Extract key metrics safely
        meta = data.get('meta', {})
        fundamentals = data.get('fundamentals', {})
        valuation = data.get('valuation', {})
        
        industry_avg_json = json.dumps(industry_avg, ensure_ascii=False) if industry_avg else "暂无行业平均数据"

        return f"""
作为资深金融分析师，请分析以下股票数据：

## 股票基本信息
- 代码: {meta.get('code', 'Unknown')}
- 名称: {meta.get('stock_name', 'Unknown')}
- 行业: {meta.get('industry', 'Unknown')}

## 核心财务指标
- 营收: {fundamentals.get('revenue_yi', 0)}亿元
- 净利润: {fundamentals.get('net_profit_yi', 0)}亿元
- ROE: {fundamentals.get('roe_pct', 0)}%
- 毛利率: {fundamentals.get('gross_margin_pct', 0)}%
- 净利率: {fundamentals.get('net_margin_pct', 0)}%
- 负债率: {fundamentals.get('debt_ratio_pct', 0)}%

## 估值数据
- 当前价格: ¥{valuation.get('price', 0)}
- PE(TTM): {valuation.get('pe_ttm', 0)}
- PB: {valuation.get('pb', 0)}
- DCF估值: ¥{valuation.get('dcf_per_share', 0)}
- DCF安全边际: {valuation.get('dcf_margin_of_safety', 0)}%

## 行业平均（对比基准）
{industry_avg_json}

请以JSON格式输出深度分析报告，结构如下：
{{
  "interpretation": {{
    "summary": "...",
    "highlights": ["..."],
    "risks": ["..."]
  }},
  "investment_advice": {{
    "rating": "买入/持有/卖出",
    "rating_score": 0-10,
    "target_price": 0.0,
    "stop_loss": 0.0,
    "position": "...",
    "reasoning": "..."
  }},
  "forecast": {{
    "next_quarter_revenue": {{ "low": 0, "mid": 0, "high": 0, "unit": "亿元" }},
    "one_year_price": {{ "low": 0, "mid": 0, "high": 0, "confidence": "..." }},
    "key_drivers": ["..."]
  }}
}}
"""
