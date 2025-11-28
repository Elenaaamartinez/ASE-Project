FROM python:3.9-alpine

WORKDIR /app
COPY . .

# Installa le dipendenze (se necessario in futuro)
# RUN pip install --no-cache-dir -r requirements.txt

# Esponi la porta
EXPOSE 8080

# Avvia il server Python semplice
CMD ["python", "server.py"]
