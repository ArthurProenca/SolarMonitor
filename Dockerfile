# Use a imagem oficial do Python
FROM python:3.12-slim

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos necessários para o diretório de trabalho
COPY ./app /app

# Instala as dependências
RUN pip install --no-cache-dir -r /app/requirements.txt

# Comando para iniciar a aplicação
CMD uvicorn main:app --host 0.0.0.0 --port $PORT