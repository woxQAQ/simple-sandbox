FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    MPLBACKEND=Agg \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends libfreetype6 libpng16-16 fonts-dejavu-core; \
    pip install --no-cache-dir matplotlib==3.8.4 numpy==1.26.4; \
    useradd -m -u 65532 -s /usr/sbin/nologin sandbox; \
    mkdir -p /runner /workspace /tmp; \
    chown -R sandbox:sandbox /runner /workspace /tmp

COPY runner.py /runner/runner.py

USER sandbox
WORKDIR /workspace

ENTRYPOINT ["python", "/runner/runner.py"] 