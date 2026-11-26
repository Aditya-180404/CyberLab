FROM python:3.12-slim

WORKDIR /opt/cyberlab-agent

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir psutil>=6.1.0

COPY cyberlab_agent.py /opt/cyberlab-agent/cyberlab_agent.py

CMD ["python3", "/opt/cyberlab-agent/cyberlab_agent.py"]
