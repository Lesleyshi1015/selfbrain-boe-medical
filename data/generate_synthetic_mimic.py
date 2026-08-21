#!/usr/bin/env python3
"""
生成模拟 MIMIC-IV 结构的合成医疗数据样本
用于 SelfBrain 医疗隐私保护 POC 演示

注意：此数据为完全合成的模拟数据，非真实患者信息
数据结构参考 MIMIC-IV v3.1 schema (physionet.org/content/mimiciv/3.1/)
"""

import csv
import json
import random
import os
from datetime import datetime, timedelta

# 设置随机种子以确保可重复性
random.seed(42)

# 输出目录
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ========== 配置 ==========
NUM_PATIENTS = 50
NUM_ADMISSIONS = 80
NUM_LABEVENTS = 300
NUM_DIAGNOSES = 150

# 日期范围（模拟 MIMIC 的日期偏移：2100-2200）
BASE_YEAR_START = 2150
BASE_YEAR_END = 2160

# ========== 辅助数据 ==========
GENDERS = ['M', 'F']
ADMISSION_TYPES = ['ELECTIVE', 'URGENT', 'EMERGENCY']
ADMISSION_LOCATIONS = ['EMERGENCY ROOM', 'PHYSICIAN REFERRAL', 'CLINIC REFERRAL', 'TRANSFER FROM HOSPITAL']
DISCHARGE_LOCATIONS = ['HOME', 'SKILLED NURSING FACILITY', 'HOME HEALTH CARE', 'REHAB', 'AGAINST ADVICE']
INSURANCE_TYPES = ['Medicare', 'Medicaid', 'Private', 'Self-pay', 'Other']
LANGUAGES = ['English', 'Spanish', 'Chinese', 'French', 'Other']
MARITAL_STATUS = ['MARRIED', 'SINGLE', 'DIVORCED', 'WIDOWED']
RACES = ['WHITE', 'BLACK', 'ASIAN', 'HISPANIC', 'OTHER']

# ICD-10 诊断代码（常见疾病）
ICD_CODES = [
    ('I10', 10),   # 原发性高血压
    ('E11.9', 10), # 2型糖尿病
    ('J18.9', 10), # 肺炎
    ('K21.0', 10), # 胃食管反流
    ('M54.5', 10), # 下背痛
    ('F41.1', 10), # 广泛性焦虑障碍
    ('I25.10', 10),# 动脉粥样硬化性心脏病
    ('N18.3', 10), # 慢性肾脏病3期
    ('J45.909', 10),# 哮喘
    ('E78.5', 10), # 高脂血症
    ('I48.91', 10),# 心房颤动
    ('Z95.1', 10), # 主动脉冠状动脉旁路移植术状态
    ('I12.9', 10), # 高血压性慢性肾脏病
    ('E11.65', 10),# 2型糖尿病伴高血糖
    ('J96.00', 10),# 急性呼吸衰竭
]

# 实验室检查项目（itemid, 名称, 单位, 正常范围）
LAB_ITEMS = [
    (50868, 'Albumin', 'g/dL', 3.5, 5.0),
    (50862, 'Anion Gap', 'mEq/L', 8, 16),
    (50882, 'Bicarbonate', 'mEq/L', 22, 29),
    (50885, 'Bilirubin Total', 'mg/dL', 0.1, 1.2),
    (50861, 'BUN', 'mg/dL', 7, 20),
    (50912, 'Creatinine', 'mg/dL', 0.6, 1.2),
    (50806, 'Glucose', 'mg/dL', 70, 100),
    (50822, 'Hematocrit', '%', 37, 47),
    (50824, 'Hemoglobin', 'g/dL', 12, 16),
    (50831, 'Platelet', 'K/uL', 150, 400),
    (50971, 'Potassium', 'mEq/L', 3.5, 5.0),
    (50983, 'Sodium', 'mEq/L', 136, 145),
    (51006, 'WBC', 'K/uL', 4.5, 11.0),
    (50809, 'Chloride', 'mEq/L', 98, 106),
    (50878, 'ALT', 'U/L', 7, 56),
    (50879, 'AST', 'U/L', 10, 40),
    (50889, 'Cholesterol', 'mg/dL', 0, 200),
    (50931, 'INR', '', 0.8, 1.1),
    (50810, 'Calcium', 'mg/dL', 8.5, 10.5),
    (50960, 'Magnesium', 'mg/dL', 1.7, 2.2),
]

# 敏感字段（用于 POC 脱敏演示）
SENSITIVE_FIELDS = {
    'patients': ['subject_id'],  # 患者标识符
    'admissions': ['hadm_id', 'admission_type'],  # 住院标识
    'labevents': ['specimen_id', 'value', 'comments'],  # 检验结果
    'diagnoses_icd': ['icd_code'],  # 诊断信息
}


def random_date(start_year, end_year):
    """生成随机日期"""
    year = random.randint(start_year, end_year)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    return datetime(year, month, day, hour, minute)


def generate_patients(n):
    """生成患者表"""
    patients = []
    for i in range(n):
        subject_id = 1000000 + i
        anchor_year = random.randint(BASE_YEAR_START, BASE_YEAR_END)
        anchor_age = random.randint(18, 91)
        # 如果年龄>89，设为91（MIMIC规范）
        if anchor_age > 89:
            anchor_age = 91
        
        # 计算 anchor_year_group
        if anchor_year <= 2152:
            year_group = "2008 - 2010"
        elif anchor_year <= 2155:
            year_group = "2011 - 2013"
        elif anchor_year <= 2158:
            year_group = "2014 - 2016"
        else:
            year_group = "2017 - 2019"
        
        # 随机死亡日期（约10%的患者）
        dod = None
        if random.random() < 0.1:
            dod = random_date(anchor_year + 1, anchor_year + 5)
        
        patients.append({
            'subject_id': subject_id,
            'gender': random.choice(GENDERS),
            'anchor_age': anchor_age,
            'anchor_year': anchor_year,
            'anchor_year_group': year_group,
            'dod': dod.strftime('%Y-%m-%d %H:%M:%S') if dod else None
        })
    return patients


def generate_admissions(patients, n):
    """生成入院记录表"""
    admissions = []
    subject_ids = [p['subject_id'] for p in patients]
    
    for i in range(n):
        subject_id = random.choice(subject_ids)
        hadm_id = 2000000 + i
        admittime = random_date(BASE_YEAR_START, BASE_YEAR_END)
        
        # 住院时长 1-30 天
        los_days = random.randint(1, 30)
        dischtime = admittime + timedelta(days=los_days)
        
        # 约5%住院死亡
        hospital_expire = 1 if random.random() < 0.05 else 0
        deathtime = dischtime if hospital_expire else None
        
        admissions.append({
            'subject_id': subject_id,
            'hadm_id': hadm_id,
            'admittime': admittime.strftime('%Y-%m-%d %H:%M:%S'),
            'dischtime': dischtime.strftime('%Y-%m-%d %H:%M:%S'),
            'deathtime': deathtime.strftime('%Y-%m-%d %H:%M:%S') if deathtime else None,
            'admission_type': random.choice(ADMISSION_TYPES),
            'admit_provider_id': f'P{random.randint(1,999):03d}{random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}{random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")}',
            'admission_location': random.choice(ADMISSION_LOCATIONS),
            'discharge_location': random.choice(DISCHARGE_LOCATIONS) if not hospital_expire else 'DIED',
            'insurance': random.choice(INSURANCE_TYPES),
            'language': random.choice(LANGUAGES),
            'marital_status': random.choice(MARITAL_STATUS),
            'race': random.choice(RACES),
            'edregtime': (admittime - timedelta(hours=random.randint(1, 8))).strftime('%Y-%m-%d %H:%M:%S'),
            'edouttime': admittime.strftime('%Y-%m-%d %H:%M:%S'),
            'hospital_expire_flag': hospital_expire
        })
    return admissions


def generate_labevents(patients, admissions, n):
    """生成实验室检查表"""
    labevents = []
    hadm_ids = [a['hadm_id'] for a in admissions]
    subject_hadm_map = {}
    for a in admissions:
        if a['subject_id'] not in subject_hadm_map:
            subject_hadm_map[a['subject_id']] = []
        subject_hadm_map[a['subject_id']].append(a)
    
    for i in range(n):
        subject_id = random.choice([p['subject_id'] for p in patients])
        itemid, lab_name, unit, low, high = random.choice(LAB_ITEMS)
        
        # 关联到一次住院
        hadm_id = None
        charttime = random_date(BASE_YEAR_START, BASE_YEAR_END)
        if subject_id in subject_hadm_map:
            adm = random.choice(subject_hadm_map[subject_id])
            hadm_id = adm['hadm_id']
            # charttime 在住院期间
            adm_time = datetime.strptime(adm['admittime'], '%Y-%m-%d %H:%M:%S')
            disch_time = datetime.strptime(adm['dischtime'], '%Y-%m-%d %H:%M:%S')
            charttime = adm_time + timedelta(hours=random.randint(0, int((disch_time - adm_time).total_seconds() / 3600)))
        
        # 生成值（部分异常）
        is_abnormal = random.random() < 0.3
        if is_abnormal:
            valuenum = random.uniform(low - 2, high + 2)
        else:
            valuenum = random.uniform(low, high)
        
        valuenum = round(valuenum, 2)
        flag = 'abnormal' if is_abnormal else 'normal'
        
        labevents.append({
            'labevent_id': 3000000 + i,
            'subject_id': subject_id,
            'hadm_id': hadm_id,
            'specimen_id': 4000000 + i,
            'itemid': itemid,
            'order_provider_id': f'P{random.randint(1,999):03d}{random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}{random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")}',
            'charttime': charttime.strftime('%Y-%m-%d %H:%M:%S'),
            'storetime': (charttime + timedelta(hours=random.randint(1, 4))).strftime('%Y-%m-%d %H:%M:%S'),
            'value': str(valuenum),
            'valuenum': valuenum,
            'valueuom': unit,
            'ref_range_lower': low,
            'ref_range_upper': high,
            'flag': flag,
            'priority': random.choice(['routine', 'stat']),
            'comments': None
        })
    return labevents


def generate_diagnoses(patients, admissions, n):
    """生成诊断表"""
    diagnoses = []
    # 构建 subject_id -> hadm_id 映射
    subject_hadm_map = {}
    for a in admissions:
        if a['subject_id'] not in subject_hadm_map:
            subject_hadm_map[a['subject_id']] = []
        subject_hadm_map[a['subject_id']].append(a['hadm_id'])
    
    idx = 0
    for _ in range(n):
        subject_id = random.choice([p['subject_id'] for p in patients])
        if subject_id not in subject_hadm_map or not subject_hadm_map[subject_id]:
            continue
        
        hadm_id = random.choice(subject_hadm_map[subject_id])
        icd_code, icd_version = random.choice(ICD_CODES)
        
        diagnoses.append({
            'subject_id': subject_id,
            'hadm_id': hadm_id,
            'seq_num': random.randint(1, 10),
            'icd_code': icd_code,
            'icd_version': icd_version
        })
        idx += 1
    
    return diagnoses


def write_csv(filename, data, fieldnames):
    """写入 CSV 文件，带文件头指纹"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        # 文件头指纹
        f.write(f"# @agent: session-260816-cool-orchid | module: medical/data | ts: 2026-08-16T13:10+08:00\n")
        f.write(f"# SOURCE: Synthetic MIMIC-IV structured data (for SelfBrain POC)\n")
        f.write(f"# DISCLAIMER: This is simulated data, NOT real patient information\n")
        f.write(f"# SCHEMA REFERENCE: MIMIC-IV v3.1 (physionet.org/content/mimiciv/3.1/)\n")
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)
    print(f"  Written: {filepath} ({len(data)} rows)")


def main():
    print("=" * 60)
    print("SelfBrain Medical POC - Synthetic MIMIC-IV Data Generator")
    print("=" * 60)
    
    print("\n[1/4] Generating patients table...")
    patients = generate_patients(NUM_PATIENTS)
    write_csv('patients.csv', patients, [
        'subject_id', 'gender', 'anchor_age', 'anchor_year', 'anchor_year_group', 'dod'
    ])
    
    print("\n[2/4] Generating admissions table...")
    admissions = generate_admissions(patients, NUM_ADMISSIONS)
    write_csv('admissions.csv', admissions, [
        'subject_id', 'hadm_id', 'admittime', 'dischtime', 'deathtime',
        'admission_type', 'admit_provider_id', 'admission_location',
        'discharge_location', 'insurance', 'language', 'marital_status',
        'race', 'edregtime', 'edouttime', 'hospital_expire_flag'
    ])
    
    print("\n[3/4] Generating labevents table...")
    labevents = generate_labevents(patients, admissions, NUM_LABEVENTS)
    write_csv('labevents.csv', labevents, [
        'labevent_id', 'subject_id', 'hadm_id', 'specimen_id', 'itemid',
        'order_provider_id', 'charttime', 'storetime', 'value', 'valuenum',
        'valueuom', 'ref_range_lower', 'ref_range_upper', 'flag', 'priority', 'comments'
    ])
    
    print("\n[4/4] Generating diagnoses_icd table...")
    diagnoses = generate_diagnoses(patients, admissions, NUM_DIAGNOSES)
    write_csv('diagnoses_icd.csv', diagnoses, [
        'subject_id', 'hadm_id', 'seq_num', 'icd_code', 'icd_version'
    ])
    
    # 生成汇总 JSON
    summary = {
        "metadata": {
            "agent": "session-260816-cool-orchid",
            "module": "medical/data",
            "timestamp": "2026-08-16T13:10+08:00",
            "source": "Synthetic MIMIC-IV structured data",
            "disclaimer": "This is simulated data, NOT real patient information",
            "schema_reference": "MIMIC-IV v3.1 (physionet.org/content/mimiciv/3.1/)"
        },
        "statistics": {
            "patients": NUM_PATIENTS,
            "admissions": NUM_ADMISSIONS,
            "labevents": NUM_LABEVENTS,
            "diagnoses": len(diagnoses)
        },
        "tables": {
            "patients": {
                "file": "patients.csv",
                "rows": NUM_PATIENTS,
                "sensitive_fields": ["subject_id"],
                "description": "Patient demographics (deidentified)"
            },
            "admissions": {
                "file": "admissions.csv",
                "rows": NUM_ADMISSIONS,
                "sensitive_fields": ["hadm_id", "admission_type", "insurance", "race"],
                "description": "Hospital admission records"
            },
            "labevents": {
                "file": "labevents.csv",
                "rows": NUM_LABEVENTS,
                "sensitive_fields": ["specimen_id", "value", "comments"],
                "description": "Laboratory measurements"
            },
            "diagnoses_icd": {
                "file": "diagnoses_icd.csv",
                "rows": len(diagnoses),
                "sensitive_fields": ["icd_code"],
                "description": "Diagnosis codes (ICD-10)"
            }
        },
        "poc_use_cases": [
            "敏感字段脱敏演示（subject_id, hadm_id 等标识符）",
            "检验结果加密分片存储演示",
            "外部模型分析时数据隐私保护演示",
            "审计日志完整性验证"
        ]
    }
    
    summary_path = os.path.join(OUTPUT_DIR, 'synthetic_data_summary.json')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\n  Written: {summary_path}")
    
    print("\n" + "=" * 60)
    print("Data generation complete!")
    print(f"Output directory: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == '__main__':
    main()
