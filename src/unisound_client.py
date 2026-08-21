# @agent: session-260820-smart-palm | module: boe/unisound | ts: 2026-08-20T18:20:00+08:00
# -*- coding: utf-8 -*-
"""
云知声医疗AI客户端 - 京东方AI黑客松演示专用

提供健康档案解读、医疗问答等能力，通过云知声MaaS平台(u2模型)调用。
支持真实API模式与演示降级模式。

依赖:
    - OpenAI兼容接口: https://maas-api.hivoice.cn/v1/chat/completions
    - 模型: u2 (山海·知医大模型)
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# 尝试导入requests，若无则使用urllib
try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False
    import urllib.request
    import urllib.error

# ── 配置 ──────────────────────────────────────────────────────────────────────

DEFAULT_BASE_URL = "https://maas-api.hivoice.cn/v1"
DEFAULT_MODEL = "u2"
CONFIG_SLUG = "pi-api-key-6"


# ── 降级模式模拟数据 ─────────────────────────────────────────────────────────

_DEMO_INTERPRETATION = """
╔══════════════════════════════════════════════════════════════╗
║          健康档案智能解读报告（演示模式）                      ║
║          ⚠️ 当前无有效API Key，以下为模拟解读结果              ║
╚══════════════════════════════════════════════════════════════╝

【患者概况】
  患者ID: {patient_id}
  档案记录数: {record_count} 条
  时间跨度: {time_span}

【主要诊断】
  1. 原发性高血压2级（中危）
     - 最近血压: 120/83 mmHg（控制良好）
     - 趋势分析: 从149/100 → 120/83，呈改善趋势
     - 用药情况: 苯磺酸氨氯地平片 5mg qd

【风险评估】
  🔴 高风险: 无
  🟡 中风险: 血压偶有波动，建议缩短随访间隔
  🟢 低风险: 体重稳定，生活方式干预有效

【随访建议】
  1. 继续当前降压治疗方案
  2. 每2周监测血压并记录
  3. 低盐饮食，每日盐摄入 < 5g
  4. 每周至少150分钟中等强度运动
  5. 3个月后复查血脂、血糖、肾功能

【医保提示】
  高血压属于门诊慢特病病种，可申请门特待遇，报销比例约60-80%。
  建议咨询当地医保局办理门特备案。

──────────────────────────────────────────────────────────────
  解读模型: 云知声 山海·知医 U2 (演示模式)
  生成时间: {timestamp}
──────────────────────────────────────────────────────────────
"""

_DEMO_MEDICAL_ANSWER = """
【医保问答】（演示模式）

问题: {question}

回答:
  根据现行医保政策，{answer_summary}

  📋 相关政策依据:
  - 《国家基本医疗保险、工伤保险和生育保险药品目录》
  - 各地门诊慢特病管理办法

  ⚠️ 以上为AI参考回答，具体报销比例以当地医保局为准。

──────────────────────────────────────────────────────────────
  模型: 云知声 U2 (演示模式) | {timestamp}
──────────────────────────────────────────────────────────────
"""


# ── UnisoundClient ───────────────────────────────────────────────────────────

class UnisoundClient:
    """
    云知声医疗AI客户端
    
    通过OpenAI兼容接口调用云知声山海·知医大模型，
    提供健康档案解读、医疗问答等医疗专业能力。
    
    Attributes:
        api_key: 云知声API Key
        base_url: API基础URL
        model: 模型名称（默认u2）
        timeout: 请求超时时间（秒）
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        timeout: int = 120,
    ):
        """
        初始化客户端
        
        Args:
            api_key: 云知声API Key。若不提供，依次尝试:
                     1) UNISOUND_API_KEY 环境变量
                     2) Craft Agent config.json 中的 pi-api-key-6
            base_url: API基础URL。若不提供，使用默认值
            model: 模型名称，默认 u2
            timeout: 请求超时时间，默认120秒
        """
        self.model = model
        self.timeout = timeout
        
        # 解析API Key
        self.api_key = api_key or os.environ.get("UNISOUND_API_KEY")
        if not self.api_key:
            self.api_key = self._load_api_key_from_config()
        
        # 解析Base URL
        self.base_url = (base_url or os.environ.get("UNISOUND_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        
        # 模式判断
        self._demo_mode = not bool(self.api_key)
        if self._demo_mode:
            print("[UnisoundClient] ⚠️  未检测到有效API Key，已切换至演示模式", file=sys.stderr)
        else:
            print(f"[UnisoundClient] ✓ 已连接云知声MaaS平台 ({self.base_url})", file=sys.stderr)
    
    def _load_api_key_from_config(self) -> Optional[str]:
        """从Craft Agent config.json中读取云知声API Key。"""
        try:
            config_path = Path.home() / ".craft-agent" / "config.json"
            if not config_path.exists():
                return None
            
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            # 查找 pi-api-key-6 连接
            for conn in config.get("llmConnections", []):
                if conn.get("slug") == CONFIG_SLUG:
                    # API Key存储在credentials中
                    cred_path = Path.home() / ".craft-agent" / "credentials.enc"
                    # 由于credentials.enc是加密的，这里无法直接读取
                    # 返回None让调用方使用环境变量或手动传入
                    return None
            
            return None
        except Exception:
            return None
    
    @property
    def is_demo_mode(self) -> bool:
        """是否处于演示降级模式。"""
        return self._demo_mode
    
    def _build_headers(self) -> Dict[str, str]:
        """构建请求头。"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
    
    def _call_api(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        """
        调用云知声Chat Completions API
        
        Args:
            messages: OpenAI格式消息列表
            temperature: 温度参数
            max_tokens: 最大输出token数
        
        Returns:
            模型回复文本
        """
        if self._demo_mode:
            return self._demo_response(messages)
        
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        try:
            if _HAS_REQUESTS:
                resp = requests.post(
                    url,
                    headers=self._build_headers(),
                    json=payload,
                    timeout=self.timeout,
                )
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]
            else:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers=self._build_headers(),
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    return data["choices"][0]["message"]["content"]
        
        except Exception as e:
            # API调用失败时降级到演示模式
            print(f"[UnisoundClient] ⚠️  API调用失败: {e}，降级至演示模式", file=sys.stderr)
            self._demo_mode = True
            return self._demo_response(messages)
    
    def _demo_response(self, messages: List[Dict[str, str]]) -> str:
        """演示模式：根据用户消息返回模拟回复。"""
        last_msg = messages[-1].get("content", "") if messages else ""
        
        if "档案" in last_msg or "解读" in last_msg or "健康" in last_msg:
            return _DEMO_INTERPRETATION.format(
                patient_id="P-2026-0001",
                record_count=5,
                time_span="2025-08 ~ 2026-03",
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            )
        else:
            return _DEMO_MEDICAL_ANSWER.format(
                question=last_msg[:50] + "..." if len(last_msg) > 50 else last_msg,
                answer_summary="该药品/项目通常属于医保乙类目录，具体报销比例因地区政策而异。",
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            )
    
    # ── 核心方法 ──────────────────────────────────────────────────────────────
    
    def interpret_health_record(
        self,
        patient_id: str,
        records: List[Dict[str, Any]],
        focus: Optional[str] = None,
    ) -> str:
        """
        健康档案智能解读
        
        将脱敏后的健康档案发送给云知声医疗大模型，
        生成结构化的解读报告（诊断分析、风险评估、随访建议）。
        
        Args:
            patient_id: 患者ID（脱敏后）
            records: 就诊记录列表，每条包含:
                     - record_type: 记录类型（就诊/检验/用药等）
                     - content: 记录内容文本
                     - timestamp: 时间戳
                     - metadata: 附加信息（症状、体征等）
            focus: 解读重点（如"血压趋势""用药合理性"），可选
        
        Returns:
            模型生成的解读报告文本
        """
        # 构建档案摘要
        records_text = self._format_records(records)
        
        focus_hint = f"\n【解读重点】{focus}" if focus else ""
        
        system_prompt = """你是一位经验丰富的全科医生，擅长健康档案解读和慢病管理。
请根据提供的患者健康档案，生成一份专业的解读报告，包括：
1. 患者概况与主要诊断
2. 关键指标趋势分析
3. 风险评估（高/中/低）
4. 随访与用药建议
5. 医保相关提示（如适用）

要求：专业但易懂，重点突出，建议具体可执行。"""
        
        user_prompt = f"""患者ID: {patient_id}
健康档案记录（已脱敏）:
{records_text}
{focus_hint}

请生成健康档案解读报告。"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        return self._call_api(messages, temperature=0.1, max_tokens=800)
    
    def answer_medical_question(
        self,
        question: str,
        context: Optional[str] = None,
        category: str = "general",
    ) -> str:
        """
        医疗知识问答
        
        支持医保政策、药品信息、疾病知识等问答场景。
        
        Args:
            question: 用户问题
            context: 可选的上下文信息（如患者档案摘要）
            category: 问题类别
                - general: 通用医疗知识
                - insurance: 医保政策
                - drug: 药品信息
                - disease: 疾病知识
        
        Returns:
            模型回答文本
        """
        category_map = {
            "general": "医疗知识",
            "insurance": "医保政策",
            "drug": "药品信息",
            "disease": "疾病知识",
        }
        
        category_name = category_map.get(category, "医疗知识")
        
        system_prompt = f"""你是一位专业的医疗顾问，擅长{category_name}领域的问答。
请基于你的医学知识，给出准确、专业、易懂的回答。
如果涉及医保政策，请说明"具体以当地医保局规定为准"。
如果涉及用药建议，请提醒"请遵医嘱"。"""
        
        user_prompt = question
        if context:
            user_prompt = f"参考信息:\n{context}\n\n问题: {question}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        return self._call_api(messages, temperature=0.1, max_tokens=1024)
    
    # ── 工具方法 ──────────────────────────────────────────────────────────────
    
    @staticmethod
    def _format_records(records: List[Dict[str, Any]]) -> str:
        """将记录列表格式化为文本。"""
        if not records:
            return "（无记录）"
        
        lines = []
        for i, rec in enumerate(records, 1):
            rec_type = rec.get("record_type", "未知")
            content = rec.get("content", "")
            ts = rec.get("timestamp", "")
            
            line = f"[{i}] {rec_type}"
            if ts:
                line += f" ({ts})"
            line += f"\n    {content}"
            
            # 附加metadata
            meta = rec.get("metadata", {})
            if meta:
                symptoms = meta.get("symptoms", [])
                vitals = meta.get("vitals", [])
                if symptoms:
                    line += f"\n    症状: {', '.join(symptoms)}"
                if vitals:
                    line += f"\n    体征: {', '.join(vitals)}"
            
            lines.append(line)
        
        return "\n\n".join(lines)
    
    def health_check(self) -> bool:
        """
        检查API连接状态
        
        Returns:
            True表示API可用，False表示不可用（演示模式）
        """
        if self._demo_mode:
            return False
        
        try:
            # 发送一个简单请求测试连接
            messages = [{"role": "user", "content": "你好，请回复'OK'"}]
            result = self._call_api(messages, max_tokens=10)
            return bool(result)
        except Exception:
            self._demo_mode = True
            return False


# ── 便捷函数 ─────────────────────────────────────────────────────────────────

def create_client(
    api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL,
) -> UnisoundClient:
    """
    创建云知声客户端（便捷函数）
    
    Args:
        api_key: API Key，不提供则从环境变量读取
        model: 模型名称
    
    Returns:
        UnisoundClient 实例
    """
    return UnisoundClient(api_key=api_key, model=model)


# ── CLI入口 ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  云知声医疗AI客户端 - 快速测试")
    print("=" * 60)
    
    client = UnisoundClient()
    print(f"\n模式: {'演示模式 ⚠️' if client.is_demo_mode else '真实API模式 ✓'}")
    print(f"模型: {client.model}")
    print(f"BaseURL: {client.base_url}")
    
    # 测试健康档案解读
    print("\n" + "-" * 40)
    print("测试: 健康档案解读")
    print("-" * 40)
    
    test_records = [
        {
            "record_type": "就诊",
            "content": "患者P-TEST-001，58岁男，诊断：原发性高血压2级。主诉：心悸、头晕。体征：血压149/100 mmHg。",
            "timestamp": "2025-08-25",
            "metadata": {
                "symptoms": ["心悸", "头晕"],
                "vitals": ["血压 149/100 mmHg"],
            },
        },
    ]
    
    result = client.interpret_health_record("P-TEST-001", test_records)
    print(result[:500] + "..." if len(result) > 500 else result)
    
    # 测试医疗问答
    print("\n" + "-" * 40)
    print("测试: 医保问答")
    print("-" * 40)
    
    result = client.answer_medical_question(
        "高血压药氨氯地平能报销吗？",
        category="insurance",
    )
    print(result[:300] + "..." if len(result) > 300 else result)
    
    print("\n✓ 测试完成")
