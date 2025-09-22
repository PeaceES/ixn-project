FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the full project in
COPY . .

# Run the agent
CMD ["python", "main.py"]

