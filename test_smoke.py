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

    print("\n全部通过 ✅")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print("测试失败:", e)
        sys.exit(1)
