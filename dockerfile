# Dockerfile
FROM python:3.11

WORKDIR /app

# Copiar el archivo requirements.txt al directorio de trabajo
COPY requirements.txt .

# Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código fuente al directorio de trabajo
COPY . .

# Iniciar el servidor usando waitress
CMD ["waitress-serve", "--port=5000", "app:app"]