# @agent: session-260820-smart-palm | module: boe/unisound | ts: 2026-08-20T18:20:00+08:00
# -*- coding: utf-8 -*-
"""
云知声医疗AI演示脚本 - 京东方AI黑客松 2026

演示场景:
  1. 健康档案智能解读（脱敏后档案 → 云知声U2模型 → 解读报告）
  2. 医保/药品问答（医疗知识问答）

降级策略:
  若API Key不可用，自动切换至演示模式，返回模拟解读结果（标注"演示模式"）。

用法:
  python scripts/demo_unisound.py [--demo] [--patient P-2026-0001]
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── 路径配置 ──────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
SRC_DIR = PROJECT_ROOT / "src"
HEALTH_DEMO_DIR = PROJECT_ROOT / "health-demo"
DOCS_DIR = PROJECT_ROOT / "docs"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# ── 彩色输出 ──────────────────────────────────────────────────────────────────


class Colors:
    HEADER = '[95m'
    BLUE = '[94m'
    CYAN = '[96m'
    WHITE = '[97m'
    GREEN = '[92m'
    YELLOW = '[93m'
    RED = '[91m'
    BOLD = '[1m'
    END = '[0m'


def c_print(text: str, color: str = ""):
    """彩色打印。"""
    print(f"{color}{text}{Colors.END}")


def print_header(text: str):
    c_print(f"\n{'=' * 65}", Colors.HEADER + Colors.BOLD)
    c_print(f"  {text}", Colors.HEADER + Colors.BOLD)
    c_print(f"{'=' * 65}\n", Colors.HEADER + Colors.BOLD)


def print_section(text: str):
    c_print(f"\n{Colors.BLUE}{Colors.BOLD}▶ {text}{Colors.END}", Colors.BLUE)
    c_print(f"  {'─' * 55}", Colors.CYAN)


def print_success(text: str):
    c_print(f"  {Colors.GREEN}✓ {text}{Colors.END}")


def print_warning(text: str):
    c_print(f"  {Colors.YELLOW}⚠ {text}{Colors.END}")


def print_error(text: str):
    c_print(f"  {Colors.RED}✗ {text}{Colors.END}")


def print_info(text: str):
    c_print(f"  {Colors.CYAN}ℹ {text}{Colors.END}")


# ── 数据加载 ──────────────────────────────────────────────────────────────────


def load_synthetic_data(patient_id: Optional[str] = None) -> Dict[str, Any]:
    """
    加载脱敏后的健康档案数据
    
    Args:
        patient_id: 患者ID，不提供则返回全部
    
    Returns:
        包含patients列表的字典
    """
    data_file = HEALTH_DEMO_DIR / "synthetic_data_gold.json"
    
    if not data_file.exists():
        raise FileNotFoundError(f"脱敏数据文件不存在: {data_file}")
    
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if patient_id:
        patients = [p for p in data["patients"] if p["patient_id"] == patient_id]
        if not patients:
            raise ValueError(f"未找到患者: {patient_id}")
        return {"patients": patients}
    
    return data


def extract_records_for_patient(data: Dict[str, Any], patient_id: str) -> List[Dict]:
    """从数据中提取指定患者的所有记录。"""
    for patient in data.get("patients", []):
        if patient["patient_id"] == patient_id:
            return patient.get("records", [])
    return []


# ── 演示主流程 ────────────────────────────────────────────────────────────────


def demo_health_interpretation(client, patient_id: str, records: List[Dict]) -> str:
    """
    演示场景1: 健康档案智能解读
    
    展示从脱敏档案到AI解读的完整流程。
    """
    print_section(f"场景1: 健康档案智能解读 — 患者 {patient_id}")
    
    # 显示输入摘要
    c_print(f"\n  📋 输入: 脱敏健康档案 ({len(records)} 条记录)", Colors.CYAN)
    for i, rec in enumerate(records[:3], 1):
        rec_type = rec.get("record_type", "?")
        content = rec.get("content", "")[:60] + "..." if len(rec.get("content", "")) > 60 else rec.get("content", "")
        ts = rec.get("timestamp", "")
        c_print(f"    [{i}] {rec_type} | {ts} | {content}", Colors.CYAN)
    if len(records) > 3:
        c_print(f"    ... 共 {len(records)} 条", Colors.CYAN)
    
    # 调用云知声解读
    c_print(f"\n  🔄 调用云知声 U2 模型解读中...", Colors.YELLOW)
    start = time.time()
    
    result = client.interpret_health_record(
        patient_id=patient_id,
        records=records,
        focus="血压趋势分析与用药建议",
    )
    
    elapsed = time.time() - start
    
    # 显示结果
    mode_tag = " [演示模式]" if client.is_demo_mode else ""
    c_print(f"\n  ⏱ 耗时: {elapsed:.2f}s{mode_tag}", Colors.GREEN if not client.is_demo_mode else Colors.YELLOW)
    
    return result


def demo_medical_qa(client, questions: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    演示场景2: 医保/药品问答
    
    展示云知声在医保政策和药品信息方面的问答能力。
    """
    print_section("场景2: 医保/药品智能问答")
    
    results = []
    for i, qa in enumerate(questions, 1):
        q = qa["question"]
        cat = qa.get("category", "general")
        
        c_print(f"\n  ❓ Q{i}: {q}", Colors.BLUE)
        c_print(f"     类别: {cat}", Colors.CYAN)
        
        c_print(f"  🔄 查询中...", Colors.YELLOW)
        start = time.time()
        
        answer = client.answer_medical_question(q, category=cat)
        elapsed = time.time() - start
        
        c_print(f"\n  💡 A{i}:", Colors.GREEN)
        # 格式化输出（限制长度）
        lines = answer.split("\n")
        for line in lines[:15]:  # 最多显示15行
            c_print(f"     {line}", Colors.WHITE if line.strip() else "")
        if len(lines) > 15:
            c_print(f"     ... (共 {len(lines)} 行)", Colors.CYAN)
        
        mode_tag = " [演示模式]" if client.is_demo_mode else ""
        c_print(f"  ⏱ 耗时: {elapsed:.2f}s{mode_tag}", Colors.GREEN if not client.is_demo_mode else Colors.YELLOW)
        
        results.append({
            "question": q,
            "category": cat,
            "answer": answer,
            "demo_mode": client.is_demo_mode,
        })
    
    return results


def generate_report(
    patient_id: str,
    interpretation: str,
    qa_results: List[Dict[str, str]],
    output_path: Path,
) -> Path:
    """
    生成演示报告文件
    
    Returns:
        报告文件路径
    """
    report_lines = [
        "=" * 65,
        "  云知声医疗AI演示报告",
        "  京东方AI黑客松 2026 · 完整医疗支撑系统",
        "=" * 65,
        "",
        f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"患者ID: {patient_id}",
        "",
        "─" * 65,
        "  【健康档案解读报告】",
        "─" * 65,
        "",
        interpretation,
        "",
        "─" * 65,
        "  【医保/药品问答记录】",
        "─" * 65,
        "",
    ]
    
    for i, qa in enumerate(qa_results, 1):
        report_lines.extend([
            f"Q{i}: {qa['question']}",
            f"类别: {qa['category']}",
            "",
            f"A{i}:",
            qa['answer'],
            "",
            f"{'─' * 40}",
            "",
        ])
    
    report_lines.extend([
        "",
        "=" * 65,
        "  报告结束",
        "  接入方: 云知声 Unisound (山海·知医 U2)",
        "  隐私底座: SelfBrain (脱敏前置)",
        "  记忆引擎: TimeWeave (跨会话记忆)",
        "=" * 65,
    ])
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    
    return output_path


# ── 预设问答 ──────────────────────────────────────────────────────────────────

DEFAULT_QUESTIONS = [
    {
        "question": "高血压患者常用的氨氯地平片，医保能报销多少？",
        "category": "insurance",
    },
    {
        "question": "二甲双胍和阿卡波糖可以一起服用吗？有什么注意事项？",
        "category": "drug",
    },
    {
        "question": "2型糖尿病患者的随访频率应该是怎样的？",
        "category": "disease",
    },
]


# ── CLI入口 ───────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="云知声医疗AI演示脚本 - 京东方AI黑客松2026",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python demo_unisound.py                          # 默认患者演示
  python demo_unisound.py --patient P-2026-0002    # 指定患者
  python demo_unisound.py --demo                   # 强制演示模式
  python demo_unisound.py --output report.txt      # 指定输出路径
        """,
    )
    
    parser.add_argument(
        "--patient", "-p",
        default="P-2026-0001",
        help="患者ID（默认: P-2026-0001）",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="强制使用演示模式（不调用真实API）",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="云知声API Key（也可通过UNISOUND_API_KEY环境变量设置）",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="报告输出路径（默认: health-demo/unisound_report.txt）",
    )
    parser.add_argument(
        "--questions", "-q",
        nargs="+",
        default=None,
        help="自定义问题列表（空格分隔）",
    )
    
    args = parser.parse_args()
    
    # ── 初始化 ────────────────────────────────────────────────────────────
    print_header("云知声医疗AI演示 · 京东方AI黑客松2026")
    
    # 加载脱敏数据
    try:
        data = load_synthetic_data(args.patient)
        records = extract_records_for_patient(data, args.patient)[-5:]  # 取最近5条提速
        if not records:
            print_error(f"患者 {args.patient} 无记录")
            sys.exit(1)
        print_success(f"已加载患者 {args.patient} 的 {len(records)} 条脱敏记录")
    except FileNotFoundError as e:
        print_error(str(e))
        sys.exit(1)
    
    # 初始化客户端
    if args.demo:
        # 强制演示模式：不传API key
        from unisound_client import UnisoundClient
        client = UnisoundClient(api_key=None)
    else:
        from unisound_client import UnisoundClient
        client = UnisoundClient(api_key=args.api_key)
    
    mode_str = "演示模式 ⚠️" if client.is_demo_mode else "真实API模式 ✓"
    c_print(f"\n  运行模式: {mode_str}", Colors.GREEN if not client.is_demo_mode else Colors.YELLOW)
    c_print(f"  模型: {client.model}", Colors.CYAN)
    c_print(f"  BaseURL: {client.base_url}", Colors.CYAN)
    
    # ── 演示场景1: 健康档案解读 ─────────────────────────────────────────
    interpretation = demo_health_interpretation(client, args.patient, records)
    
    # 打印解读报告
    print_section("📄 解读报告")
    c_print(interpretation, Colors.WHITE)
    
    # ── 演示场景2: 医保/药品问答 ────────────────────────────────────────
    questions = DEFAULT_QUESTIONS
    if args.questions:
        questions = [{"question": q, "category": "general"} for q in args.questions]
    
    qa_results = demo_medical_qa(client, questions)
    
    # ── 生成报告 ────────────────────────────────────────────────────────
    output_path = args.output
    if not output_path:
        output_path = HEALTH_DEMO_DIR / "unisound_report.txt"
    else:
        output_path = Path(output_path)
    
    report_path = generate_report(args.patient, interpretation, qa_results, output_path)
    
    print_header("演示完成")
    print_success(f"报告已保存: {report_path}")
    print_info(f"文件大小: {report_path.stat().st_size / 1024:.1f} KB")
    
    if client.is_demo_mode:
        print_warning("\n当前为演示模式（API Key不可用）")
        print_info("配置真实API Key的方法见: docs/云知声接入说明-20260820.md")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
