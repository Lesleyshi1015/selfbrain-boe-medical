# SelfBrain BOE Medical — 完整医疗支撑系统（可复现 Demo）

> 京东方 AI 黑客松 2026 · 数据主权 AI 底座（隐私 + 记忆 + 医疗专业能力）
> 评审可复现版（clone 即跑）

## 🎯 项目定位
为京东方 50 亿健康数据打造的数据主权 AI 底座：
**脱敏（隐私）→ 记忆（长程）→ 解读（医疗专业）** 完整闭环

## 📁 结构
```
├── src/
│   ├── demo_medical.py    # S1 病历脱敏（19字段 89%敏感 + 审计）
│   └── unisound_client.py # 云知声医疗解读客户端（无key降级演示）
├── scripts/
│   └── demo_unisound.py   # 云知声解读 demo
├── data/                  # MIMIC-IV 合成样本（非真实患者）
└── health-demo/           # TimeWeave 记忆引擎（模拟版，clone即跑）
```

## 🚀 快速运行（评审复现）

### 1. 病历脱敏（S1）
```bash
python src/demo_medical.py
# 输出：脱敏流程 + 审计报告（19字段 89% 敏感）
```

### 2. 医疗解读（云知声）
```bash
python scripts/demo_unisound.py --patient P-2026-0001
# 无 UNISOUND_API_KEY → 演示模式（模拟解读）
# 有 key → 真实医疗解读（u2-med 模型）
```

### 3. 记忆引擎（TimeWeave）
```bash
cd health-demo/
python generate_synthetic_data.py  # 生成合成健康档案
python run_demo.py                 # 长程记忆/时间线/风险（模拟版）
```

## 📹 演示视频
见 `docs/final_demo.mp4`（3 分钟：脱敏→记忆→解读→数据主权）

## ⚠️ 黑盒保护说明
- 本仓库为**可复现模拟版**（纯标准库/模拟数据，clone 即跑）
- **真引擎版**（TimeWeave 五层引擎 / SelfBrain Core）为闭源商业核心
  - 演示视频展示真引擎效果
  - 商务合作时提供真引擎接入
- 云知声 API Key 不入仓库（环境变量，无 key 自动降级演示）

## ✅ 数据声明
- 所有医疗数据为**合成数据**（MIMIC-IV 模式生成，不对应真实患者）
- 定位：辅助决策系统，不替代专业医疗诊断

## 📋 满足赛事要求
- AI 智能体项目：✅（隐私/记忆/医疗多 Agent 协作）
- 可运行 Demo：✅（三个入口 clone 即跑）
- 3-5 分钟视频：✅（docs/final_demo.mp4）
- 部署说明：✅（本文件）

---

## 🔌 框架适配说明

本仓库为**可复现的医疗场景 Demo**（原程序版，clone 即跑）。

**能力与框架解耦**：底层能力（病历脱敏 / 隐私保护 / 记忆检索 / 医疗解读）为通用模块，
**可适配多种 Agent 框架**（AgentTeams / LangChain / AutoGen / 自定义编排等）——
后续接入具体框架时，仅需替换调用层（API/接口适配），核心能力不变。

> 当前版本聚焦"能力可复现"，框架适配为工程接入层（按需提供）。
