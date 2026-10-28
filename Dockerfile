FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
COPY requirements.txt ./
COPY LICENSE docs/18_Attribution_and_Data_Citation.md ./
RUN python -m pip install --no-cache-dir -r requirements.txt \
    && useradd --uid 10001 --create-home research
COPY neurolab ./neurolab
COPY schemas ./schemas
# Operator-only budget review and bounded provider smoke tools.
COPY scripts/configure_model_budget.py scripts/smoke_meta_provider.py ./scripts/
COPY data ./data
USER research
EXPOSE 10000
CMD ["sh", "-c", "exec uvicorn neurolab.deployment_api:app --host 0.0.0.0 --port \"${PORT:-10000}\" --no-proxy-headers"]
