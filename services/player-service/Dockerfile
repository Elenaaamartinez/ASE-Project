FROM python:3.10-slim

RUN addgroup --system appgroup && \
    adduser --system --ingroup appuser appuser

WORKDIR /app

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY . /app
RUN chown -R appuser:appgroup /app

USER appuser

CMD ["python", "app.py"]
