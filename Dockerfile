FROM python:3.11-slim

WORKDIR /app

# Install dependencies (Components V2 requires discord.py 2.6+)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && pip show discord.py

# Copy source files
COPY . .

# Create data directory for SQLite persistent database
RUN mkdir -p data

CMD ["python", "bot.py"]
