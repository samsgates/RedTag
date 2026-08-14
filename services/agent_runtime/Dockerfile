FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /workspace
RUN useradd --create-home --uid 10002 agent
COPY pyproject.toml /workspace/
RUN pip install --upgrade pip && pip install .
COPY services/agent_runtime/app /workspace/app
RUN chown -R agent:agent /workspace
USER agent
EXPOSE 8080
CMD ["adk", "api_server", "--host", "0.0.0.0", "--port", "8080", "/workspace"]
