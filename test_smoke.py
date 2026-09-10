# -*- coding: utf-8 -*-
"""本地冒烟测试：验证 DeepSeek key 与两个业务接口。"""
import json
import sys
import urllib.request

BASE = "http://127.0.0.1:8000"

SAMPLE_JD = (
    "AI 应用开发工程师（全职，北京）\n"
    "岗位职责：\n"
    "1. 基于大模型 API 开发 AI 应用产品，负责 Prompt 工程与效果调优；\n"
    "2. 参与前后端全栈开发，独立完成功能从设计到上线；\n"
    "3. 对接业务需求，快速迭代 MVP。\n"
    "任职要求：\n"
    "1. 熟悉 Python 或 TypeScript；\n"
    "2. 有大模型 API 调用经验，了解 RAG、Agent 等常见架构；\n"
    "3. 有上线过小工具/网站/小程序的经验优先。"
)

SAMPLE_JD2 = (
    "大模型应用工程师（全职，上海）\n"
    "岗位职责：\n"
    "1. 负责 Agent 与 RAG 系统的落地开发与效果评估；\n"
    "2. 与产品协作，把大模型能力转化为可用功能；\n"
    "3. 关注模型选型、成本与延迟优化。\n"
    "任职要求：\n"
    "1. Python 扎实，熟悉 LangChain/LlamaIndex 之一；\n"
    "2. 有向量数据库使用经验（Milvus/Chroma/pgvector 等）；\n"
    "3. 熟悉 Prompt 工程与评测方法，能独立做效果调优。"
)


def post(path, body):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=10) as resp:
        return resp.read().decode("utf-8")


def get_json(path):
    import json

    with urllib.request.urlopen(BASE + path, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    print("== 1. 首页可达 ==")
    html = get("/")
    print("index.html 返回字节数:", len(html))

    print("\n== 2. 健康检查 ==")
    print(get("/api/health"))

    print("\n== 3. /api/analyze（真实调用 DeepSeek）==")
    data = post("/api/analyze", {"jd": SAMPLE_JD, "resume": ""})
    print("summary:", (data.get("summary") or "")[:60].replace("\n", " "))
    print("match_score:", data.get("match_score"))
    print("must_have:", data.get("must_have"))
    print("resume_advice 条数:", len(data.get("resume_advice") or []))
    print("interview_focus 条数:", len(data.get("interview_focus") or []))

    print("\n== 4. /api/interview（出第一题）==")
    d1 = post("/api/interview", {"jd": SAMPLE_JD, "messages": []})
    print("AI 首轮回复:", (d1.get("reply") or "")[:80].replace("\n", " "))

    print("\n== 5. /api/interview（回答后继续）==")
    d2 = post("/api/interview", {
        "jd": SAMPLE_JD,
        "messages": [
            {"role": "assistant", "content": d1.get("reply", "")},
            {"role": "user", "content": "我熟悉 Python，调过大模型 API，做过一个小程序上线。"},
        ],
    })
    print("AI 点评+下一题:", (d2.get("reply") or "")[:100].replace("\n", " "))

    print("\n== 6. /api/compare（双 JD 对比）==")
    c = post("/api/compare", {"jds": [SAMPLE_JD, SAMPLE_JD2], "resume": ""})
    print("summary:", (c.get("summary") or "")[:60].replace("\n", " "))
    print("rows 数量:", len(c.get("rows") or []))
    if c.get("rows"):
        r0 = c["rows"][0]
        print("第一行维度:", r0.get("dimension"), "| 值数量:", len(r0.get("values") or []))
    print("advice:", (c.get("advice") or "")[:60].replace("\n", " "))

    print("\n== 7. /api/optimize_resume（简历优化）==")
    o = post("/api/optimize_resume", {
        "resume": "白洳丞\n求职意向：AI 应用开发工程师\n技能：Python、FastAPI、大模型 API 调用、微信小程序上线经验\n项目：开发过 AI 求职助手，支持 JD 分析与模拟面试，已部署上线。",
        "direction": "目标岗位是 AI 应用开发工程师，突出上线作品与量化成果，控制在 1 页",
    })
    print("optimized 长度:", len(o.get("optimized") or ""))
    print("optimized 开头:", (o.get("optimized") or "")[:60].replace("\n", " "))
    print("changes 条数:", len(o.get("changes") or []))
    print("tips 条数:", len(o.get("tips") or []))

    print("\n== 8. 文风学习 → 注入 → 清除 ==")
    post("/api/style/clear", {})
    s0 = get_json("/api/style")
    print("初始 enabled:", s0.get("enabled"))
    learn = post("/api/style/learn", {"sample": "咱就说，找工作这事别慌。JD 看不懂？拆开看。先看硬性要求，再看加分项，一条条对，不整虚的。语气要接地气、带点俏皮，多用短句。"})
    st = learn.get("style_text") or ""
    print("学习到文风指令长度:", len(st))
    s1 = get_json("/api/style")
    print("保存后 enabled:", s1.get("enabled"))
    d3 = post("/api/analyze", {"jd": SAMPLE_JD, "resume": ""})
    print("文风下 analyze summary:", (d3.get("summary") or "")[:70].replace("\n", " "))
    post("/api/style/clear", {})
    s2 = get_json("/api/style")
    print("清除后 enabled:", s2.get("enabled"))

    print("\n全部通过 ✅")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print("测试失败:", e)
        sys.exit(1)
