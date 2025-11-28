FROM node:18-alpine

WORKDIR /app

# Copia i file del frontend
COPY . .

# Installa http-server globalmente
RUN npm install -g http-server

# Esponi la porta
EXPOSE 8080

# Avvia il server
CMD ["http-server", "-p", "8080", "-c-1", "--cors"]
