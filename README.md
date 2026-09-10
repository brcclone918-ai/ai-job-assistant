# Offer 教练 · AI 求职助手

一个帮你把招聘 JD 吃透的 AI 小工具：粘贴一份 JD，立刻得到 **匹配度分析 + 简历修改建议 + 面试考察点**，还能基于这份 JD 进行 **AI 模拟面试**（出题 → 点评 → 再出题，最多 4 轮）。

> 为什么做它：求职过程中发现"读 JD、改简历、练面试"是三个重复且耗时的事，于是做了一个工具把它们串起来。我自己就是它的第一个用户。

## 功能

| 功能 | 说明 |
| --- | --- |
| JD 分析 | 粘贴 JD（可选附简历），输出总体判断、匹配度评分、硬性要求、加分项、简历修改建议、面试考察点；结果可一键复制为 Markdown |
| 简历文件上传 | 上传 PDF / TXT 简历，自动解析成文本填入，可用于分析和对比 |
| 模拟面试 | 基于 JD 出题，你作答后 AI 点评并出下一题，4 轮后给出整体评价；支持语音输入（浏览器支持时） |
| 多 JD 对比 | 同时对比 2-4 份 JD 的岗位定位、硬性要求、加分项、考察侧重、成长线索，给出投递建议 |
| 简历优化 | 粘贴/上传简历，按你给的优化方向（目标岗位、突出重点、篇幅风格等）重写简历，附改动说明与投递提醒 |
| 个人文风（自动学习） | 每个账号第一次提交简历优化时，自动学习该简历的文风并保存；此后该账号所有输出（分析/面试/对比/优化）都保持此风格，不同账号风格各异。可手动编辑/清除 |
| 账号系统 | 用户名 + 密码 + 邮箱注册/登录（SQLite 存储，密码加盐哈希）；登录错误会给出具体原因（未注册/密码错误等）；登录后文风与账号绑定，匿名期学到的文风注册时自动迁移 |

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

- `POST /api/analyze` — `{ "jd": "...", "resume": "(可选)", "uid": "账号标识" }` → 单份 JD 的结构化分析
- `POST /api/interview` — `{ "jd": "...", "messages": [...], "uid": "账号标识" }` → 面试官回复
- `POST /api/compare` — `{ "jds": [...], "resume": "(可选)", "uid": "账号标识" }` → 多 JD 对比（2-4 份）
- `POST /api/optimize_resume` — `{ "resume": "...", "direction": "...", "uid": "账号标识" }` → `{ optimized, changes, tips, style_learned, style_text }`（该账号首次提交时自动学习文风）
- `POST /api/upload_resume` — multipart 上传 `file`（PDF / TXT，≤10MB）→ `{ filename, chars, text }`
- `GET /api/style?uid=...` — 查看某账号文风（`{ enabled, style_text }`）
- `POST /api/style/save` — `{ "uid": "...", "style_text": "..." }` → 手动保存/修改文风
- `POST /api/style/clear` — `{ "uid": "..." }` → 清除该账号文风
- `POST /api/auth/register` — `{ "username": "...", "password": "...", "email": "...", "anon_uid": "(可选)" }` → 注册并登录（错误会返回具体原因）
- `POST /api/auth/login` — `{ "account": "用户名或邮箱", "password": "..." }` → 登录（未注册/密码错误会分别提示）
- `POST /api/auth/logout` — `{ "token": "..." }` → 退出登录
- `POST /api/auth/me` — `{ "token": "..." }` → 校验登录态，返回 `{ uid, username }`
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
