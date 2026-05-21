FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ROOT=/app \
    WEB_DIR=/app/web \
    DATA_DIR=/app/data \
    MAX_UPLOAD_MB=0 \
    WHISPER_MODEL=small \
    BGM_PROVIDER=procedural \
    MUSICGEN_MODEL=facebook/musicgen-small \
    MUSICGEN_MAX_SECONDS=20 \
    DEFAULT_TARGET_LANG=en \
    DEFAULT_SOURCE_LANG=auto \
    SUPERTONIC_VOICE=M1 \
    SUBTITLE_STYLE=bold \
    SUBTITLE_POSITION=bottom \
    SUBTITLE_SIZE=100 \
    SUBTITLE_FONT="Noto Sans" \
    MIN_DUB_SPEED=0.85 \
    MAX_DUB_SPEED=1.75 \
    SUPERTONIC_STEPS=8 \
    SUPERTONIC_SPEED=1.05

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      ffmpeg ca-certificates curl fontconfig openssl \
      fonts-noto-core fonts-noto-cjk fonts-noto-color-emoji \
      fonts-noto-extra fonts-noto-ui-core fonts-noto-ui-extra \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

ARG ENABLE_MUSICGEN=0
COPY backend/requirements-musicgen.txt /app/backend/requirements-musicgen.txt
RUN if [ "$ENABLE_MUSICGEN" = "1" ]; then \
      pip install --no-cache-dir -r /app/backend/requirements-musicgen.txt; \
    fi

COPY backend /app/backend
RUN python /app/backend/scripts/install_argos_models.py
RUN if [ "$ENABLE_MUSICGEN" = "1" ]; then \
      python /app/backend/scripts/warmup_musicgen.py; \
    fi

COPY web /app/web
RUN mkdir -p /app/certs \
    && openssl req -x509 -newkey rsa:2048 -nodes \
      -keyout /app/certs/localhost.key \
      -out /app/certs/localhost.crt \
      -days 365 \
      -subj "/CN=localhost"

LABEL org.opencontainers.image.title="kekedubing"

EXPOSE 8801

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8801", "--ssl-certfile", "/app/certs/localhost.crt", "--ssl-keyfile", "/app/certs/localhost.key"]
