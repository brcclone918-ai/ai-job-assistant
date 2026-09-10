# Offer 教练 · AI 求职助手

一个帮你把招聘 JD 吃透的 AI 小工具：粘贴一份 JD，立刻得到 **匹配度分析 + 简历修改建议 + 面试考察点**，还能基于这份 JD 进行 **AI 模拟面试**（出题 → 点评 → 再出题，最多 4 轮）。

> 为什么做它：求职过程中发现"读 JD、改简历、练面试"是三个重复且耗时的事，于是做了一个工具把它们串起来。我自己就是它的第一个用户。

## 功能

| 功能 | 说明 |
| --- | --- |
| JD 分析 | 粘贴 JD（可选附简历），输出总体判断、匹配度评分、硬性要求、加分项、简历修改建议、面试考察点 |
| 模拟面试 | 基于 JD 出题，你作答后 AI 点评并出下一题，4 轮后给出整体评价 |

## 技术栈

- 后端：Python + FastAPI + OpenAI SDK（兼容 DeepSeek API）
- 模型：DeepSeek `deepseek-chat`
- 前端：原生 HTML / CSS / JS（单文件，无需构建）

## 快速开始（Windows）

```powershell
# 1. 进入项目目录
cd ai-job-assistant

# 2. 创建虚拟环境并安装依赖
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt

# 3. 配置密钥：复制 .env.example 为 .env，填入你的 DeepSeek API Key
#    （DeepSeek Key 在 https://platform.deepseek.com 申请）

# 4. 启动
.\.venv\Scripts\python -m uvicorn main:app --port 8000
```

打开 http://127.0.0.1:8000 即可使用。

## 目录结构

```
ai-job-assistant/
├── main.py            # FastAPI 后端（两个接口 + 提示词）
├── static/
│   └── index.html     # 前端单页（两个标签页）
├── requirements.txt   # Python 依赖
├── .env               # 密钥配置（已被 .gitignore 排除）
├── .env.example       # 密钥配置示例
└── .gitignore
```

## 接口说明

- `POST /api/analyze` — `{ "jd": "...", "resume": "(可选)" }` → 结构化分析结果
- `POST /api/interview` — `{ "jd": "...", "messages": [{"role":"user","content":"..."}] }` → 面试官回复
- `GET /api/health` — 健康检查

## 安全提醒（重要）

- `.env` 已加入 `.gitignore`，**不要把 API Key 提交到 GitHub**。
- 如果你把 Key 发到过聊天/公开渠道，建议到 DeepSeek 平台重新生成一个。
- 部署到公网时，后端务必加上访问控制，避免 Key 被他人刷用量。

## 后续可以加什么（Roadmap）

- [ ] 简历上传（PDF）自动解析
- [ ] 面试回答录音转写
- [ ] 多份 JD 对比分析
- [ ] 生成定制化简历 PDF
