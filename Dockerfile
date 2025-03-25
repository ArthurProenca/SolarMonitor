# Use a imagem oficial do Python
FROM python:3.12-slim

# Instala o pacote necessário para suporte a locais
RUN apt-get update && apt-get install -y locales && \
    locale-gen pt_BR.UTF-8

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos necessários para o diretório de trabalho
COPY ./app /app

# Define a variável de ambiente LANG diretamente
ENV LANG=pt_BR.UTF-8

# Instala as dependências
RUN pip install --no-cache-dir -r /app/requirements.txt

# Comando para iniciar a aplicação
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
