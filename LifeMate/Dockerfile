# Operator supplies a reviewed image digest and complete offline wheelhouse.
ARG BASE_IMAGE=python:3.12-slim
FROM ${BASE_IMAGE}
ENV HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /opt/lifemate
COPY wheelhouse/ /wheelhouse/
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-index --find-links=/wheelhouse "setuptools>=68" "wheel>=0.45,<1"
RUN pip install --no-index --find-links=/wheelhouse --no-build-isolation ".[model,asr]"
COPY predict.sh ./predict.sh
RUN chmod +x ./predict.sh
ENTRYPOINT ["/opt/lifemate/predict.sh"]
