# 兼容 Hugging Face Spaces / Zeabur / 本地三处部署：
# - HF Spaces 会自动注入 PORT=7860，容器需监听 $PORT
# - Zeabur 会注入 PORT，本地默认 8000
FROM python:3.12-slim

# 非 root 用户运行（HF Spaces 推荐）
RUN useradd -m -u 1000 appuser
WORKDIR /home/user/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser . .
RUN chown -R appuser:appuser /home/user/app
USER appuser

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
