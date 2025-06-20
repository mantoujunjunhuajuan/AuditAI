# AuditAI Refactor & MVP Plan

版本: 1.0 | 日期: 2025-06-19 | 负责人: 张梦迪

---

## 1. 项目愿景 (Vision)
利用 Google Gemini 与多 Agent 协作，将保险理赔初审从 **数小时 → 数分钟**，并提升欺诈识别准确率。

## 2. 需求摘要
| 编号 | 模块 | 目标 |
|------|------|------|
| F-1 | 多文档上传 (PDF/PNG/JPG) → GCS | 安全、批量、私有存储 |
| F-2 | 5-Agent 流水线 | DocIntel → InfoExtract → RuleCheck → RiskAnalysis → ReportGen |
| F-3 | 报告可视化 | 案件摘要 + 风险评分 + 风险点 + 建议 |
| NF-1 | 60 s 端到端 | 3–5 份 PDF 内 |
| NF-2 | 数据安全 | 传输/存储加密，非公开存储桶 |

---

## 3. 重构后目录结构
```
AuditAI/
│
├── app/         # Streamlit UI
│   ├── main.py
│   ├── components/
│   └── pages/
│
├── agents/      # 五大 Agent
│   ├── base_agent.py
│   ├── doc_intel.py
│   ├── info_extract.py
│   ├── rule_check.py
│   ├── risk_analysis.py
│   └── report_gen.py
│
├── services/
│   ├── gemini_client.py
│   └── storage_service.py
│ 
├── utils/
│   ├── pdf_parser.py
│   ├── chunk.py
│   └── logging_config.py
│
├── pipeline.py  # Orchestrator
├── tests/       # Pytest
├── deploy/      # Docker & Cloud Run
└── docs/
```

---

## 4. 关键技术决策
1. **PDF → Text 默认路径**
   - `pdfminer.six` 本地解析，避免大文件 SSL 失败。
   - 生成纯文本 (<1 MB) 后按 6 k tokens 切段调用 Gemini。
2. **Vision 模式可选**
   - 勾选后上传 PDF 给 `Gemini Vision`，限制 <10 MB；>10 MB 提示压缩。
3. **GeminiClient**
   - 统一封装 `generate_content`，指数退避重试 3×。
4. **StorageService 抽象**
   - `GCSStorageService` 与 `LocalStorageService`，接口一致，便于测试。
5. **Agents**
   - 每个 Agent ≤100 行，实现单一职责。
   - 通过 `BaseAgent` 统一日志/异常。
6. **安全**
   - `.env` 管理密钥，CI 强制检查`printenv | grep KEY`为空。

---

## 5. 里程碑与工时
| 阶段 | 任务 | 产出 | 预计 | Owner |
|------|------|------|------|-------|
| M1 | 环境 & 上传 | StorageService + UI 上传 | 0.5 d | 🧑‍💻 |
| M2 | PDF Parser | pdf_parser + 单测 | 0.5 d | 🧑‍💻 |
| M3 | Agents & Pipeline | 5 Agents + pipeline | 1 d | 🧑‍💻 |
| M4 | Gemini Client | 重试&日志封装 | 0.5 d | 🧑‍💻 |
| M5 | UI 报告 | ReportViewer 组件 | 0.5 d | 🧑‍💻 |
| M6 | 测试 & CI | pytest-cov ≥80 % + GA | 0.5 d | 🧑‍💻 |
| M7 | Docker & Run | 部署脚本 | 0.5 d | 🧑‍💻 |

> 总计 **4 d** 可交付 MVP。

---

## 6. DevOps
- **CI**：GitHub Actions → lint(ruff) + type-check(pyright) + test + docker build。
- **CD**：`cloud_run.sh` 一键部署，环境变量通过 Secret Manager 注入。
- **日志**：标准输出 → Cloud Logging，JSON 格式，traceId 贯穿。

---

## 7. 下一步行动
1. `git checkout -b refactor/architecture` 创建新分支。
2. 生成上述目录 + 空文件 (`touch`).
3. 实现 `storage_service.py` & `pdf_parser.py` + 测试。
4. 完成 5 个 Agent（模版 + prompt）。
5. 拼接 Orchestrator → UI 展示。
6. 写 Dockerfile；`gcloud run deploy` 验证。

---

> **确认**：如无异议，将按本计划逐步提交代码，并在每完成一个阶段后演示功能。 