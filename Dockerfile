FROM python:3.11-slim

# Avoid .pyc files and get unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Create an isolated virtualenv inside the image so global pip stays clean
RUN python -m venv /opt/venv

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

# Collect static files once during the build so runtime containers only serve them
RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Run a production-ready WSGI server
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "satellite_tracker.wsgi:application"]
