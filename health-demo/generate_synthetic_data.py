#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合成健康数据生成器（兼容 gold 脱敏契约版）
============================================
为京东方AI黑客松生成脱敏的合成健康档案数据。

📌 协作契约：
- 输出格式与 SelfBrain (gold) 脱敏 JSON 同构
- gold 脱敏版和脚本合成版均可 ingest 到 TimeWeave memory_store

⚠️ 合规声明：
- 所有数据均为合成生成，不对应任何真实患者
- 仅用于技术演示，不用于医疗诊断
- 数据定位：辅助医生/患者决策，非替代专业医疗建议
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

# ============================================================
# 患者配置
# ============================================================

PATIENTS = [
    {
        "id": "P-2026-0001",
        "age": 58,
        "gender": "男",
        "chief_complaint": "反复头晕、头痛3年，加重1个月",
        "diagnosis": "原发性高血压2级（中危）",
        "conditions": ["高血压", "高脂血症", "轻度脂肪肝"],
        "medications": ["苯磺酸氨氯地平片 5mg qd", "阿托伐他汀钙片 20mg qn"],
        "baseline_metrics": {
            "systolic_bp": (150, 170),
            "diastolic_bp": (95, 105),
            "heart_rate": (75, 90),
            "total_cholesterol": (5.8, 6.5),
            "ldl_cholesterol": (3.5, 4.2),
            "weight": (78, 82),
        }
    },
    {
        "id": "P-2026-0002",
        "age": 65,
        "gender": "女",
        "chief_complaint": "多饮、多尿、多食伴体重下降2年",
        "diagnosis": "2型糖尿病伴糖尿病周围神经病变",
        "conditions": ["2型糖尿病", "糖尿病周围神经病变", "高血压1级", "骨质疏松"],
        "medications": ["二甲双胍缓释片 0.5g bid", "格列美脲片 2mg qd", "甲钴胺片 0.5mg tid", "硝苯地平控释片 30mg qd"],
        "baseline_metrics": {
            "fasting_glucose": (8.5, 12.0),
            "hba1c": (7.5, 9.5),
            "systolic_bp": (140, 155),
            "diastolic_bp": (85, 95),
            "weight": (58, 62),
            "creatinine": (70, 95),
        }
    },
    {
        "id": "P-2026-0003",
        "age": 42,
        "gender": "男",
        "chief_complaint": "体检发现血糖升高1周",
        "diagnosis": "2型糖尿病（新诊断）",
        "conditions": ["2型糖尿病", "肥胖症", "脂肪肝"],
        "medications": ["二甲双胍片 0.5g tid", "生活方式干预"],
        "baseline_metrics": {
            "fasting_glucose": (7.8, 10.5),
            "hba1c": (7.0, 8.5),
            "weight": (88, 95),
            "bmi": (28.5, 31.0),
            "alt": (45, 80),
            "ast": (40, 65),
        }
    }
]

# ============================================================
# 时间线事件模板
# ============================================================

VISIT_TYPES = ["门诊随访", "住院", "急诊", "体检"]
SYMPTOMS = {
    "高血压": ["头晕", "头痛", "心悸", "胸闷", "视力模糊"],
    "糖尿病": ["多饮", "多尿", "多食", "乏力", "手脚麻木", "视力模糊"],
    "高脂血症": ["头晕", "乏力"],
}

LAB_TESTS = {
    "高血压": [
        ("血压测量", "mmHg", "收缩压/舒张压"),
        ("心电图", "-", "心律"),
        ("肾功能", "μmol/L", "肌酐"),
        ("尿常规", "-", "尿蛋白"),
    ],
    "糖尿病": [
        ("空腹血糖", "mmol/L", "GLU"),
        ("糖化血红蛋白", "%", "HbA1c"),
        ("肾功能", "μmol/L", "肌酐"),
        ("尿微量白蛋白", "mg/L", "mAlb"),
        ("血脂四项", "mmol/L", "TC/TG/HDL/LDL"),
    ],
}


def generate_records(patient: Dict, months: int = 12) -> List[Dict[str, Any]]:
    """
    生成符合 gold 脱敏契约的患者记录。
    
    契约格式：
    {
        "patient_id": "P-2026-****",
        "records": [{
            "record_type": "就诊/检查/用药",
            "content": "脱敏后文本",
            "sensitive_removed": ["姓名","身份证","联系方式"],
            "permission_level": "L2",
            "timestamp": "2026-08-15T10:30:00"
        }]
    }
    """
    records = []
    now = datetime(2026, 8, 20)
    start_date = now - timedelta(days=months * 30)
    
    current_bp_sys = random.randint(*patient["baseline_metrics"].get("systolic_bp", (140, 160)))
    current_bp_dia = random.randint(*patient["baseline_metrics"].get("diastolic_bp", (90, 100)))
    current_glucose = random.uniform(*patient["baseline_metrics"].get("fasting_glucose", (7, 10)))
    current_hba1c = random.uniform(*patient["baseline_metrics"].get("hba1c", (7, 9)))
    current_weight = random.randint(*patient["baseline_metrics"].get("weight", (60, 90)))
    
    # 生成规律随访事件
    visit_interval = random.randint(25, 45)
    current_date = start_date
    
    while current_date < now:
        visit_type = random.choice(VISIT_TYPES)
        if visit_type == "住院":
            visit_type = "门诊随访"
        
        # 构建记录内容
        content_parts = [
            f"患者{patient['id']}，{patient['age']}岁{patient['gender']}，",
            f"诊断：{patient['diagnosis']}。",
        ]
        
        # 症状
        symptoms = []
        for cond in patient["conditions"]:
            if cond in SYMPTOMS:
                n = random.randint(0, 2)
                symptoms.extend(random.sample(SYMPTOMS[cond], min(n, len(SYMPTOMS[cond]))))
        if symptoms:
            content_parts.append(f"主诉：{', '.join(set(symptoms))}。")
        
        # 体征
        vitals_parts = []
        if "高血压" in patient["conditions"] or "血压" in str(patient.get("baseline_metrics", {})):
            progress_factor = (now - current_date).days / (months * 30)
            target_sys = current_bp_sys - int(random.randint(5, 15) * progress_factor)
            target_dia = current_bp_dia - int(random.randint(3, 10) * progress_factor)
            bp_sys = target_sys + random.randint(-8, 8)
            bp_dia = target_dia + random.randint(-5, 5)
            vitals_parts.append(f"血压 {bp_sys}/{bp_dia} mmHg")
            current_bp_sys = target_sys
            current_bp_dia = target_dia
        
        if "糖尿病" in patient["conditions"]:
            progress_factor = (now - current_date).days / (months * 30)
            target_glucose = current_glucose - random.uniform(0.5, 2.0) * progress_factor
            target_hba1c = current_hba1c - random.uniform(0.3, 1.0) * progress_factor
            glucose = target_glucose + random.uniform(-0.5, 0.5)
            hba1c = target_hba1c + random.uniform(-0.2, 0.2)
            vitals_parts.append(f"空腹血糖 {glucose:.1f} mmol/L")
            vitals_parts.append(f"糖化血红蛋白 {hba1c:.1f}%")
            current_glucose = target_glucose
            current_hba1c = target_hba1c
        
        if "weight" in patient["baseline_metrics"]:
            vitals_parts.append(f"体重 {current_weight + random.uniform(-1, 1):.1f} kg")
        
        if vitals_parts:
            content_parts.append("体征：" + "，".join(vitals_parts) + "。")
        
        # 用药调整
        if random.random() < 0.15:
            med_change = random.choice(["加量", "减量", "换药", "新增"])
            med_name = random.choice(patient["medications"])
            content_parts.append(f"用药调整：{med_change} {med_name}。")
        
        # 医生备注
        notes = [
            "建议继续当前治疗方案，定期复查。",
            "患者依从性良好，指标有所改善。",
            "建议加强生活方式干预，控制饮食，增加运动。",
            "指标波动，建议缩短随访间隔。",
            "病情稳定，继续保持。",
        ]
        content_parts.append(random.choice(notes))
        
        content = "".join(content_parts)
        
        record = {
            "record_type": "就诊",
            "content": content,
            "sensitive_removed": ["姓名", "身份证", "联系方式", "住址", "电话号码"],
            "permission_level": "L2",
            "timestamp": current_date.strftime("%Y-%m-%dT%H:%M:%S"),
            "metadata": {
                "visit_type": visit_type,
                "symptoms": list(set(symptoms)) if symptoms else [],
                "vitals": vitals_parts,
            }
        }
        records.append(record)
        
        # 添加检验报告记录
        if random.random() < 0.4:
            lab_content_parts = [
                f"患者{patient['id']}检验报告。",
                "检验项目：",
            ]
            
            for cond in patient["conditions"]:
                if cond in LAB_TESTS:
                    for test_name, unit, desc in LAB_TESTS[cond]:
                        if "血糖" in test_name:
                            val = f"{current_glucose + random.uniform(-1, 1):.1f}"
                        elif "糖化" in test_name:
                            val = f"{current_hba1c + random.uniform(-0.3, 0.3):.1f}"
                        elif "血压" in test_name or "收缩压" in desc:
                            val = f"{current_bp_sys}/{current_bp_dia}"
                        else:
                            val = f"{random.uniform(1, 10):.1f}"
                        
                        is_abnormal = random.random() < 0.3
                        flag = "↑异常" if is_abnormal else "正常"
                        lab_content_parts.append(f"  - {test_name}: {val} {unit} [{flag}]")
            
            lab_record = {
                "record_type": "检查",
                "content": "".join(lab_content_parts),
                "sensitive_removed": ["姓名", "身份证", "联系方式"],
                "permission_level": "L2",
                "timestamp": current_date.strftime("%Y-%m-%dT%H:%M:%S"),
                "metadata": {
                    "lab_tests": True,
                }
            }
            records.append(lab_record)
        
        current_date += timedelta(days=visit_interval + random.randint(-5, 5))
    
    # 添加患者档案摘要记录
    profile_content = (
        f"患者档案：{patient['id']}\n"
        f"年龄：{patient['age']}岁，性别：{patient['gender']}\n"
        f"主诉：{patient['chief_complaint']}\n"
        f"诊断：{patient['diagnosis']}\n"
        f"基础疾病：{', '.join(patient['conditions'])}\n"
        f"当前用药：{', '.join(patient['medications'])}\n"
        f"过敏史：无已知药物过敏\n"
        f"--- 合成演示数据 | 京东方AI黑客松 2026 ---"
    )
    
    profile_record = {
        "record_type": "就诊",
        "content": profile_content,
        "sensitive_removed": ["姓名", "身份证", "联系方式", "住址"],
        "permission_level": "L1",
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%S"),
        "metadata": {
            "profile": True,
        }
    }
    records.append(profile_record)
    
    # 按时间排序
    records.sort(key=lambda x: x["timestamp"])
    return records


def generate_gold_compatible_data() -> Dict[str, Any]:
    """
    生成符合 gold 脱敏契约的合成数据。
    
    输出格式：
    {
        "patients": [{
            "patient_id": "P-2026-****",
            "records": [...]
        }],
        "metadata": {...}
    }
    """
    all_data = {
        "patients": [],
        "metadata": {
            "source": "synthetic_demo",
            "demo_source": "京东方AI黑客松2026",
            "generated_at": datetime(2026, 8, 20).strftime("%Y-%m-%dT%H:%M:%S"),
            "total_patients": len(PATIENTS),
            "compliance": {
                "synthetic_data": True,
                "desensitized": True,
                "for_demo_only": True,
                "not_for_diagnosis": True,
            }
        }
    }
    
    total_records = 0
    
    for p_config in PATIENTS:
        records = generate_records(p_config, months=12)
        total_records += len(records)
        
        patient_data = {
            "patient_id": p_config["id"],
            "records": records,
            "profile": {
                "age": p_config["age"],
                "gender": p_config["gender"],
                "diagnosis": p_config["diagnosis"],
                "conditions": p_config["conditions"],
                "current_medications": p_config["medications"],
            }
        }
        all_data["patients"].append(patient_data)
    
    all_data["metadata"]["total_records"] = total_records
    
    return all_data


def generate_memory_store_format(all_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    将 gold 契约数据转换为 memory_store 调用格式。
    
    转换规则：
    - content = records[].content（脱敏后文本）
    - metadata = {"tags": ["health", patient_id], "source": "gold-desensitized", ...}
    - timestamp = records[].timestamp（转为 epoch ms）
    """
    memories = []
    
    for patient in all_data["patients"]:
        patient_id = patient["patient_id"]
        
        for record in patient["records"]:
            # 解析时间戳
            ts_str = record["timestamp"]
            try:
                dt = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%S")
                timestamp_ms = int(dt.timestamp() * 1000)
            except ValueError:
                timestamp_ms = int(datetime.now().timestamp() * 1000)
            
            # 构建 tags
            tags = [
                "health",
                f"health/{patient_id}",
                f"health/record_type/{record['record_type']}",
                f"health/permission/{record['permission_level']}",
            ]
            
            # 构建 metadata（兼容 gold 契约）
            metadata = {
                "patient_id": patient_id,
                "record_type": record["record_type"],
                "source": "gold-desensitized",
                "permission_level": record["permission_level"],
                "sensitive_removed": record.get("sensitive_removed", []),
                "synthetic": True,
                "demo_source": "京东方AI黑客松2026",
            }
            
            # 合并 record 中的 metadata
            if "metadata" in record:
                metadata.update(record["metadata"])
            
            # 构建 title
            title = f"{patient_id} - {record['record_type']} - {ts_str[:10]}"
            
            memory = {
                "content": record["content"],
                "timestamp": timestamp_ms,
                "title": title,
                "tags": tags,
                "metadata": metadata,
            }
            memories.append(memory)
    
    return memories


if __name__ == "__main__":
    print("=" * 60)
    print("  合成健康数据生成器（兼容 gold 脱敏契约）")
    print("  京东方AI黑客松 2026")
    print("=" * 60)
    
    # 生成 gold 契约格式数据
    gold_data = generate_gold_compatible_data()
    
    print(f"\n生成患者档案: {len(gold_data['patients'])} 个")
    for p in gold_data["patients"]:
        print(f"  - {p['patient_id']}: {p['profile']['age']}岁 {p['profile']['gender']}, {p['profile']['diagnosis']}")
    
    print(f"\n生成记录总数: {gold_data['metadata']['total_records']} 条")
    
    # 保存 gold 契约格式
    gold_path = Path(__file__).parent / "synthetic_data_gold.json"
    with open(gold_path, "w", encoding="utf-8") as f:
        json.dump(gold_data, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] Gold 契约格式: {gold_path}")
    
    # 生成 memory_store 格式
    memories = generate_memory_store_format(gold_data)
    
    memory_data = {
        "patients": gold_data["patients"],
        "memories": memories,
        "metadata": gold_data["metadata"],
    }
    
    memory_path = Path(__file__).parent / "synthetic_data.json"
    with open(memory_path, "w", encoding="utf-8") as f:
        json.dump(memory_data, f, ensure_ascii=False, indent=2)
    print(f"[OK] Memory Store 格式: {memory_path}")
    
    print("\n" + "=" * 60)
    print("  合规声明")
    print("=" * 60)
    print("  [!] 所有数据均为合成生成，不对应任何真实患者")
    print("  [!] 仅用于技术演示，不用于医疗诊断")
    print("  [!] 定位：辅助医生/患者决策，非替代专业医疗建议")
    print("  [!] 格式兼容：gold 脱敏版和脚本合成版均可 ingest")
    print("=" * 60)
