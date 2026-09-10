# -*- coding: utf-8 -*-
"""AI 求职助手 —— FastAPI 后端

功能：
1. POST /api/analyze    粘贴 JD（可选附简历）→ 匹配度分析 + 简历修改建议 + 面试考察点
2. POST /api/interview  基于 JD 的模拟面试（出题 → 点评 → 再出题，最多 4 轮）

运行：
    .venv\\Scripts\\python -m uvicorn main:app --port 8000
打开 http://127.0.0.1:8000 即可使用。
"""

import json
import os
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from openai import OpenAI
from pydantic import BaseModel

load_dotenv()

app = FastAPI(title="AI 求职助手", description="粘贴 JD，得到匹配度分析、简历建议与模拟面试")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip()
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat").strip()

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")


# ---------- 请求模型 ----------
class AnalyzeRequest(BaseModel):
    jd: str
    resume: str = ""


class InterviewRequest(BaseModel):
    jd: str
    messages: List[dict] = []


class CompareRequest(BaseModel):
    jds: List[str]
    resume: str = ""


class OptimizeRequest(BaseModel):
    resume: str
    direction: str = ""


# ---------- 提示词 ----------
ANALYZE_SYSTEM = (
    "你是资深 HR 兼业务面试官，帮助求职者分析一份岗位 JD。\n"
    "必须只输出一个 JSON 对象，不要输出任何其他文字、注释或代码块标记。JSON 结构如下：\n"
    '{"summary":"用2-3句话概括岗位核心要求与总体判断",'
    '"match_score":0到100的整数,'
    '"must_have":["硬性要求1","硬性要求2"],'
    '"good_have":["加分项1","加分项2"],'
    '"resume_advice":["具体可操作的简历修改建议1","建议2"],'
    '"interview_focus":["面试官可能重点考察的点1","点2"]}\n'
    "要求：简历建议必须具体到可以照着改，禁止空话套话；"
    "如果用户没有提供简历，match_score 表示你对该岗位匹配难度的估计，并在 summary 中说明。"
)

INTERVIEW_SYSTEM = (
    "你是资深面试官，根据用户提供的 JD 进行模拟面试。规则：\n"
    "1. 对话刚开始（没有任何历史）时，先用一句话说明会重点考察哪些能力，然后出第一道题。\n"
    "2. 用户回答后：先点评（1-2个优点、1-2个不足），再出下一道题。\n"
    "3. 出题总数不超过4道，难度递进：基础题→项目经历→场景/开放题。\n"
    "4. 第4道题用户回答后，给出整体评价与提升建议，并明确说“面试结束”。\n"
    "5. 题目要贴近 JD 的真实考察点。语气专业、友好、简洁，使用分段，不要长篇大论。"
)

COMPARE_SYSTEM = (
    "你是资深 HR 兼业务面试官，帮助求职者横向对比多份岗位 JD。\n"
    "必须只输出一个 JSON 对象，不要输出任何其他文字、注释或代码块标记。JSON 结构如下：\n"
    '{"summary":"2-3句话的总体对比结论",'
    '"rows":['
    '{"dimension":"岗位定位","values":["JD1要点","JD2要点"]},'
    '{"dimension":"硬性要求","values":["JD1要点","JD2要点"]},'
    '{"dimension":"加分项","values":["JD1要点","JD2要点"]},'
    '{"dimension":"面试考察侧重","values":["JD1要点","JD2要点"]},'
    '{"dimension":"成长与薪资线索","values":["JD1要点","JD2要点"]}'
    '],'
    '"advice":"综合建议：哪个岗位更适合这位求职者、理由、下一步怎么准备"}\n'
    "要求：rows 里每个 values 数组的长度必须与用户提供的 JD 数量完全一致，"
    "按 JD 顺序一一对应；内容要具体，禁止空话套话。"
)

OPTIMIZE_SYSTEM = (
    "你是资深 HR 与简历优化专家，根据用户给出的优化方向，帮用户优化简历。\n"
    "必须只输出一个 JSON 对象，不要输出任何其他文字、注释或代码块标记。JSON 结构如下：\n"
    '{"optimized":"优化后的完整简历文本（保留原简历的全部真实信息与结构，按优化方向重写表述、调整顺序、突出亮点）",'
    '"changes":["改动点1：具体改了什么、为什么这么改","改动点2"],'
    '"tips":["面试官视角提醒1","提醒2"]}\n'
    "要求：\n"
    "1. 优化后的简历必须严格基于原文，不得编造不存在的经历、项目、技能或数据；\n"
    "2. 尊重用户提供的优化方向（如目标岗位、想突出的重点、篇幅、语言、模板风格等）；\n"
    "3. changes 逐条说明改动及理由，具体可操作；\n"
    "4. tips 给 2-3 条与投递或面试准备相关的实用提醒。"
)


# ---------- 工具函数 ----------
def call_deepseek(messages: List[dict], temperature: float = 0.7) -> str:
    """调用 DeepSeek，返回模型回复文本。"""
    if not DEEPSEEK_API_KEY:
        raise HTTPException(status_code=500, detail="未配置 DEEPSEEK_API_KEY，请在 .env 文件中填写")
    try:
        resp = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=2048,
        )
        return resp.choices[0].message.content or ""
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"DeepSeek 调用失败：{exc}") from exc


def parse_json_loose(text: str):
    """尽量从模型输出中解析 JSON；失败返回 None。"""
    if not text:
        return None
    cleaned = text.strip()
    # 去掉 ```json ... ``` 围栏
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    for candidate in (text.strip(), cleaned):
        try:
            return json.loads(candidate)
        except Exception:
            continue
    return None


# ---------- 路由 ----------
@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/api/health")
def health():
    return {"status": "ok", "model": DEEPSEEK_MODEL}


ALLOWED_RESUME_EXT = {".pdf", ".txt"}
MAX_RESUME_BYTES = 10 * 1024 * 1024


@app.post("/api/upload_resume")
async def upload_resume(file: UploadFile = File(...)):
    """上传简历文件（PDF / TXT），解析出纯文本返回。"""
    filename = file.filename or "resume"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_RESUME_EXT:
        raise HTTPException(status_code=400, detail="仅支持 PDF 或 TXT 格式")
    data = await file.read()
    if len(data) > MAX_RESUME_BYTES:
        raise HTTPException(status_code=400, detail="文件过大，上限 10MB")

    text = ""
    if ext == ".pdf":
        try:
            import io

            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(data))
            parts = []
            for page in reader.pages:
                parts.append(page.extract_text() or "")
            text = "\n".join(parts)
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(
                status_code=400,
                detail=f"PDF 解析失败（可能是扫描件或加密文件）：{exc}",
            ) from exc
    else:
        text = data.decode("utf-8", errors="replace")

    text = text.strip()
    if len(text) < 10:
        raise HTTPException(
            status_code=400,
            detail="未能从文件中提取到足够文字（扫描版 PDF 暂不支持，可直接粘贴文本）",
        )
    return {"filename": filename, "chars": len(text), "text": text}


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest):
    jd = (req.jd or "").strip()
    if len(jd) < 20:
        raise HTTPException(status_code=400, detail="JD 内容太短，请粘贴完整的职位描述")
    resume = (req.resume or "").strip()
    user_content = f"JD 内容：\n{jd}\n\n我的简历（如未提供则为空）：\n{resume or '（未提供）'}"
    reply = call_deepseek(
        [
            {"role": "system", "content": ANALYZE_SYSTEM},
            {"role": "user", "content": user_content},
        ],
        temperature=0.4,
    )
    data = parse_json_loose(reply)
    if data is None:
        data = {
            "summary": reply,
            "match_score": None,
            "must_have": [],
            "good_have": [],
            "resume_advice": [],
            "interview_focus": [],
        }
    return data


@app.post("/api/interview")
def interview(req: InterviewRequest):
    jd = (req.jd or "").strip()
    if len(jd) < 20:
        raise HTTPException(status_code=400, detail="JD 内容太短，请先粘贴完整的职位描述")
    history = req.messages or []
    clean_history = [
        {"role": m.get("role"), "content": (m.get("content") or "").strip()}
        for m in history
        if m.get("role") in ("user", "assistant") and (m.get("content") or "").strip()
    ]
    messages = [
        {"role": "system", "content": INTERVIEW_SYSTEM},
        {"role": "user", "content": f"目标 JD：\n{jd}"},
    ] + clean_history
    reply = call_deepseek(messages, temperature=0.7)
    return {"reply": reply}


@app.post("/api/compare")
def compare(req: CompareRequest):
    jds = [j.strip() for j in (req.jds or []) if j and len(j.strip()) >= 20]
    if len(jds) < 2:
        raise HTTPException(status_code=400, detail="请至少提供 2 份完整的 JD（每份不少于 20 个字符）")
    if len(jds) > 4:
        raise HTTPException(status_code=400, detail="一次最多对比 4 份 JD")
    resume = (req.resume or "").strip()
    jd_text = "\n\n".join(f"JD{i + 1}：\n{j}" for i, j in enumerate(jds))
    user_content = f"{jd_text}\n\n我的简历（如未提供则为空）：\n{resume or '（未提供）'}"
    reply = call_deepseek(
        [
            {"role": "system", "content": COMPARE_SYSTEM},
            {"role": "user", "content": user_content},
        ],
        temperature=0.4,
    )
    data = parse_json_loose(reply)
    if data is None:
        data = {"summary": reply, "rows": [], "advice": ""}
    return data


@app.post("/api/optimize_resume")
def optimize_resume(req: OptimizeRequest):
    resume = (req.resume or "").strip()
    if len(resume) < 20:
        raise HTTPException(status_code=400, detail="简历内容太短，请粘贴完整简历或先上传简历文件")
    direction = (req.direction or "").strip() or "（用户未填写，按通用求职优化：突出亮点、量化成果、精炼表述）"
    user_content = f"我的优化方向：\n{direction}\n\n我的原始简历：\n{resume}"
    reply = call_deepseek(
        [
            {"role": "system", "content": OPTIMIZE_SYSTEM},
            {"role": "user", "content": user_content},
        ],
        temperature=0.4,
    )
    data = parse_json_loose(reply)
    if data is None:
        data = {"optimized": reply, "changes": [], "tips": []}
    return data
