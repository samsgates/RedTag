FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
RUN useradd --create-home --uid 10001 redtag
COPY pyproject.toml /app/
RUN pip install --upgrade pip && pip install .
COPY services/api /app/services/api
COPY services/api/app /app/app
COPY scripts /app/scripts
COPY demo /app/demo
RUN chown -R redtag:redtag /app
USER redtag
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
