FROM python:3.12-slim

WORKDIR /repo

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    bash \
    file \
    ca-certificates

CMD ["bash", "scripts/run-linux-validation.sh"]