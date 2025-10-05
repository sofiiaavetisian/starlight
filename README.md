# Starlight

## Run the Project Locally (Docker)

Follow these steps to build and run the app inside a Docker container. The only local dependency you need is Docker.

1. **Clone the repository**
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
4. **Set up the database** inside the container (run each command from the project root):
   ```bash
   docker run --env-file .env starlight-app python manage.py migrate
   docker run --env-file .env starlight-app python manage.py import_catalog
   ```
   - `migrate` creates the tables; only needs to happen once per database file.
   - `import_catalog` pulls the active satellites from CelesTrak so the catalog isn’t empty. Skip it if you already populated the table.

5. **Run the container** with the web server exposed:
   ```bash
   docker run --env-file .env -p 8000:8000 starlight-app
   ```
   The app listens on port 8000 inside the container and Docker maps it to port 8000 on your machine.
6. **Open the site** in your browser at [http://localhost:8000](http://localhost:8000).

## Troubleshooting

- 400 Bad Request: Make sure you are visiting `http://localhost:8000` (not `0.0.0.0`).
- Static files missing when `DEBUG=0`: They are collected during the Docker build. Rebuild the image (`docker build ...`) if you made changes to static assets.
- Rebuilding after code changes: Run `docker build -t starlight-app .` again, then restart the container.

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
