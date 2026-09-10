# -*- coding: utf-8 -*-
"""简历上传接口测试：生成中文测试 PDF / TXT，分别上传并校验解析结果。"""
import os
import sys
import uuid

RESUME_TEXT = (
    "白洳丞\n"
    "求职意向：AI 应用开发工程师\n"
    "技能：Python、FastAPI、大模型 API 调用、Prompt 工程、微信小程序上线经验\n"
    "项目：开发过 AI 求职助手，支持 JD 分析与模拟面试，已部署上线；开发过一个小程序并完成上线。\n"
    "经历：在可 AI 实验室参与 AI 应用相关工作，熟悉 Agent 与 RAG 的常见架构。\n"
)


def make_test_pdf(path):
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    font_path = None
    for candidate in [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf", r"C:\Windows\Fonts\simsun.ttc"]:
        if os.path.exists(candidate):
            font_path = candidate
            break
    if not font_path:
        raise RuntimeError("未找到可用的中文字体")
    pdf.add_font("CJK", "", font_path)
    pdf.set_font("CJK", "", 12)
    for line in RESUME_TEXT.splitlines():
        pdf.cell(0, 8, line, new_x="LMARGIN", new_y="NEXT")
    pdf.output(path)


def upload(url, path, filename):
    with open(path, "rb") as f:
        content = f.read()
    boundary = uuid.uuid4().hex
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode("utf-8") + content + f"\r\n--{boundary}--\r\n".encode("utf-8")

    import urllib.request

    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8")


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    workdir = os.path.dirname(os.path.abspath(__file__))
    txt_path = os.path.join(workdir, "_test_resume.txt")
    pdf_path = os.path.join(workdir, "_test_resume.pdf")

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(RESUME_TEXT)
    make_test_pdf(pdf_path)

    print("== TXT 上传 ==")
    r1 = upload(base + "/api/upload_resume", txt_path, "简历.txt")
    print(r1[:200])

    print("\n== PDF 上传 ==")
    r2 = upload(base + "/api/upload_resume", pdf_path, "简历.pdf")
    print(r2[:200])

    import json

    d2 = json.loads(r2)
    assert d2.get("chars", 0) > 10, "PDF 解析文本过短"
    print("\nPDF 解析成功，提取字数:", d2.get("chars"))
    print("提取内容预览:", d2.get("text", "")[:60].replace("\n", " "))

    os.remove(txt_path)
    os.remove(pdf_path)
    print("\n上传接口测试通过 ✅")


if __name__ == "__main__":
    main()
