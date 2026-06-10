FROM python:3.14-slim AS test

WORKDIR /app
ENV PYTHONPATH=/app
COPY . .

RUN pip install --no-cache-dir -r requirements-dev.txt
RUN python -m pytest && touch /tmp/tests-passed

FROM python:3.14-slim AS final-stage

WORKDIR /app
COPY . .
COPY --from=test /tmp/tests-passed /tmp/tests-passed

RUN rm /tmp/tests-passed
RUN pip install --no-cache-dir -r requirements.txt

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
