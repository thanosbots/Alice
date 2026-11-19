FROM python:3.11-slim-bookworm AS builder
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

FROM python:3.11-slim-bookworm
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 ALICE_MANAGED_DEPLOYMENT=1 SESSION_DIR=/data
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt && pip check && rm -rf /wheels
COPY main.py config.py VERSION ./
COPY core/ core/
COPY database/ database/
COPY helpers/ helpers/
COPY plugins/ plugins/
COPY assets/ assets/
RUN mkdir -p /data downloads cache alice_cache
CMD ["python", "main.py"]
