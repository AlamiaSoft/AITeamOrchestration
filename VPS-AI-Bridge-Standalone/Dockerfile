FROM python:3.11-slim

WORKDIR /app

# We now only install base dependencies here since the code comes from a mounted volume
RUN pip install --no-cache-dir fastapi uvicorn requests pydantic

EXPOSE 5000

# Command is overridden in docker-compose.yml to run from the mounted repo volume
CMD ["tail", "-f", "/dev/null"]
