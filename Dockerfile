FROM python:3.12-slim

WORKDIR /app

# Dependencias del sistema para PyMySQL y comunicación serial (Modbus)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias primero (mejor cache de capas)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY src/ ./src/
COPY fake_serial.py ./
COPY async_run.py ./
COPY serial_controller.py ./

# Punto de entrada
CMD ["python", "async_run.py"]