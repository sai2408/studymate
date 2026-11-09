# ---- StudyMate backend image ----
# 1. Start from an official, small Python image
FROM python:3.12-slim

# 2. Don't write .pyc files; print logs immediately
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 3. All following commands run inside /app
WORKDIR /app

# 4. Copy ONLY requirements first -> Docker caches this layer,
#    so packages are not reinstalled every time the code changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Now copy the source code
COPY . .

# 6. Document the port and start the server
#    (0.0.0.0 = accept connections from outside the container;
#     ${PORT:-8000} lets cloud platforms choose the port)
EXPOSE 8000
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]