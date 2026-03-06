FROM python:3.12-alpine AS builder

RUN apk add --no-cache gcc musl-dev libffi-dev
WORKDIR /app
COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir .

FROM python:3.12-alpine

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .

RUN adduser -D -u 1000 appuser
USER appuser

EXPOSE 8000
CMD ["uvicorn", "netmap.app:app", "--host", "0.0.0.0", "--port", "8000"]
