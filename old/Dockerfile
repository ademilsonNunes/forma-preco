# Imagem base com Python 3.12
FROM python:3.12-slim

# Variável de ambiente para não pedir interação
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório da aplicação
WORKDIR /app

# Copiar dependências
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copiar todos os arquivos da aplicação
COPY . .

# Expor a porta padrão do Streamlit
EXPOSE 8502

# Comando para rodar o app principal
CMD ["streamlit", "run", "app.py", "--server.port=8502", "--server.address=0.0.0.0"]
