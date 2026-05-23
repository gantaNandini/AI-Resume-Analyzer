FROM python:3.12-slim AS builder
WORKDIR /app
COPY services/llm_service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app
EXPOSE 8005
CMD ["uvicorn", "services.llm_service.main:app", "--host", "0.0.0.0", "--port", "8005"]
