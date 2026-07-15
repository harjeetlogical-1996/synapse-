# Synapse Research Agent — minimal Python image.
# Render sometimes picks Docker mode; this makes that path work too.
FROM python:3.12-slim

WORKDIR /app
COPY . .

# stdlib only, but keep the step for consistency
RUN pip install --no-cache-dir -r requirements.txt || true

# Render provides PORT; bind to all interfaces so the platform can route.
ENV HOST=0.0.0.0
EXPOSE 8000

CMD ["python", "server.py"]
