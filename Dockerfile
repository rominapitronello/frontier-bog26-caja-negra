# el gemelo en un contenedor: un proceso, sin dependencias (python estándar). railway lo construye desde el repo.
# variables: GEMELO_TOKEN (el token del equipo, como secreto del servicio) y PORT (la pone railway).
FROM python:3.12-slim
WORKDIR /app
COPY gemelo/ gemelo/
ENV PYTHONUNBUFFERED=1
CMD ["python3", "gemelo/servidor.py"]
