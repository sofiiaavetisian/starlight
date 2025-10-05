# Starlight

## Run the Project Locally (Docker)

Follow these steps to build and run the app inside a Docker container. The only local dependency you need is Docker (Docker Desktop on macOS/Windows or Docker Engine on Linux).

1. **Clone the repository** (or open the project folder if you already have it).
2. **Create your environment file** by copying the template and editing the values you need:
   ```bash
   cp .env.example .env
   ```
   - Keep `DEBUG=0` so the app behaves like a production deployment.
   - Replace `SECRET_KEY` with any non-empty string if you want your own value.
   - Leave `DJANGO_ALLOWED_HOSTS` as `localhost,127.0.0.1,0.0.0.0` unless you plan to expose the container elsewhere.
3. **Build the Docker image** from the project root:
   ```bash
   docker build -t starlight-app .
   ```
   This installs Python dependencies, collects static files, and prepares the app inside an image.
4. **Run the container** using your environment variables:
   ```bash
   docker run --env-file .env -p 8000:8000 starlight-app
   ```
   - The app runs on port 8000 inside the container but is mapped to port 8000 on your machine.
   - If you have not applied migrations before, run them once with:
     ```bash
     docker run --env-file .env starlight-app python manage.py migrate
     ```
5. **Open the site** in your browser at [http://localhost:8000](http://localhost:8000).

## Troubleshooting

- 400 Bad Request: Make sure you are visiting `http://localhost:8000` (not `0.0.0.0`).
- Static files missing when `DEBUG=0`: They are collected during the Docker build. Rebuild the image (`docker build ...`) if you made changes to static assets.
- Rebuilding after code changes: Run `docker build -t starlight-app .` again, then restart the container.

## Static Files Issue (Report Note)

When I first tested the Docker container with `DEBUG=0`, none of the CSS or JavaScript showed up and Django kept returning 400 errors. It turned out that Django refuses requests that use the host `0.0.0.0` when debug mode is off, and it also stops serving static files automatically. The fix was to tell whoever runs the app to use `http://localhost:8000` instead of `0.0.0.0`, and to add WhiteNoise so the collected static files are served even with debug disabled. After rebuilding the image with `collectstatic`, everything loaded normally.

## Project Commands (without Docker)

If you want to run the project directly on your machine, you will need Python 3.11.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

You can still reuse the `.env` file by loading the values manually or with a tool like `django-environ` (not included).
