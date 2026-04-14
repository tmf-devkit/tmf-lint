FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY tmf_lint ./tmf_lint

RUN pip install --no-cache-dir .

ENTRYPOINT ["tmf-lint"]
CMD ["--help"]
