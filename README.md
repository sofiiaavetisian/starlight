# Starlight ![CI](https://github.com/sofiiaavetisian/starlight/actions/workflows/ci.yml/badge.svg)

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
   The app now uses Gunicorn inside the container. It still listens on port 8000, and Docker maps it to port 8000 on your machine.
6. **Open the site** in your browser at [http://localhost:8000](http://localhost:8000).

## Troubleshooting

- 400 Bad Request: Make sure you are visiting `http://localhost:8000` (not `0.0.0.0`).
- Static files missing when `DEBUG=0`: They are collected during the Docker build. Rebuild the image (`docker build ...`) if you made changes to static assets.
- Rebuilding after code changes: Run `docker build -t starlight-app .` again, then restart the container.

## How It Works

Here’s the chain of events when you ask the app, “where is satellite X right now?”

1. **Grab the TLE** – A Two-Line Element set is basically two lines of numbers that describe the orbit. For example, a NORAD ID might have a line that starts `1 25544…`. That single line hides things like inclination (tilt of the orbit), mean motion (how many laps per day), and when the orbit was last updated. I fetch the latest TLE from CelesTrak so I’m not stuck with stale data.

2. **Feed it into SGP4** – SGP4 is the standard orbit propagator used by NASA, universities, basically everyone. I hand it the two TLE lines and a timestamp (the current UTC time). SGP4 spits out two 3D vectors in the TEME frame:
   - `r = (x, y, z)` is the satellite position in kilometres.
   - `v = (vx, vy, vz)` is the velocity in km/s.
   TEME is “True Equator Mean Equinox” – think of it as coordinates that move with the orbit, not with Earth. They’re not great for drawing on a map yet, but they’re super precise for orbit math.

3. **Rotate into Earth’s frame** – Because Earth spins underneath the orbit, I need to rotate the TEME vector so it lines up with Earth. I do that with the `_gmst_from_jd` helper. It calculates the Greenwich Mean Sidereal Time (GMST), which is just “how many degrees has the Earth spun since a known reference point.” If GMST is, say, 45°, I rotate the vector by 45° around Earth’s Z axis. After that rotation I have an ECEF vector (Earth-Centered, Earth-Fixed). Example: imagine SGP4 gave me `(6524, -686, 0)` km and GMST works out to 1 radian (~57°). After rotation the new vector might be `(5583, 3603, 0)` km. Now the X axis points toward Greenwich and the Y axis toward 90°E, so it’s tied to the ground.

4. **Convert to latitude/longitude/altitude** – I plug the ECEF vector into `pyproj` which knows how to jump from Cartesian coordinates to geodetic ones (`lat`, `lon`, `alt`). In the example above, the rotated vector might land at latitude `53.1°`, longitude `32.5°`, altitude `420 km`. That makes sense for the ISS: roughly 400–420 km up, usually somewhere between ±51.6° latitude.

5. **Send it back as JSON** – The API bundles the NORAD ID, name, latitude, longitude, altitude, speed (calculated from the velocity vector), and the timestamp. The frontend or any external tool can then plot that point on a map or draw a track.

Key takeaway: I’m not doing any fancy orbital mechanics myself. I’m leaning on the established SGP4 library to do the heavy lifting, then doing a couple of coordinate transforms so humans can read the result.

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

## Tests & Coverage

Run the Django test suite with coverage enabled (required to stay above the 70% gate):

```bash
coverage run manage.py test
coverage html
coverage xml
```

Coverage artifacts are written to `reports/` (`reports/.coverage`, `reports/coverage_html/`, `reports/coverage.xml`). The `.coveragerc` configuration enforces `fail_under = 70`, so CI or local runs will fail if overall coverage slips under the assignment threshold.

## Continuous Integration

A GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push/PR to `main`. It installs dependencies, executes `coverage run manage.py test` (so the 70% gate is enforced automatically), publishes the coverage reports in `reports/`, and then builds the Docker image via `docker build -t starlight-app .`. The workflow fails immediately if tests or coverage fail, which keeps `main` healthy.

## Continuous Deployment (Azure Container Apps)

Pushes to `main` run `.github/workflows/cd.yml`, which builds the Docker image, pushes it to Azure Container Registry (ACR), and updates an Azure Container Apps deployment that hosts both the Django container and a PostgreSQL container (provisioned once up front). Secrets are injected via GitHub Actions so nothing sensitive lands in git.

1. **One-time Azure setup**
   - Ensure you have an ACR in the provided resource group: `az acr create --name <acrName> --resource-group <rg> --sku Basic`.
   - Run the helper script to provision Container Apps + PostgreSQL:
     ```bash
     az login --service-principal --username <appId> --password <clientSecret> --tenant <tenantId>
     export RESOURCE_GROUP=<rg>
     export LOCATION=<region>
     export CONTAINERAPPS_ENVIRONMENT=starlight-env
     export LOG_ANALYTICS_WORKSPACE=starlight-logs
     export STORAGE_ACCOUNT_NAME=<unique storage name>
     export STORAGE_FILE_SHARE=starlightpg
     export POSTGRES_APP_NAME=starlight-db
     export POSTGRES_DB=starlight
     export POSTGRES_USER=starlight
     export POSTGRES_PASSWORD=<strong password>
     bash infra/containerapps/setup.sh
     ```
     The script registers required providers (if needed), creates the Container Apps environment + Log Analytics workspace, provisions Azure Files storage, and deploys the PostgreSQL container (internal ingress only). It prints the database FQDN when finished.

2. **Create GitHub secrets** (Repository → Settings → Secrets and variables → Actions).
   - Azure auth & registry:
     - `AZURE_CREDENTIALS`: Service-principal JSON (clientId, clientSecret, tenantId, subscriptionId, etc.).
     - `AZURE_CONTAINER_REGISTRY`: ACR name (e.g., `mystarlightacr`).
     - `AZURE_CONTAINER_REGISTRY_LOGIN_SERVER`: The login server (`mystarlightacr.azurecr.io`).
     - `AZURE_RESOURCE_GROUP`: Resource group name.
     - `AZURE_CONTAINERAPPS_ENVIRONMENT`: Name passed to the setup script (e.g., `starlight-env`).
     - `AZURE_CONTAINERAPPS_APP_NAME`: Desired name for the Django container app (e.g., `starlight-web`).
   - Django config:
     - `DJANGO_SECRET_KEY`: Production secret key.
     - `DJANGO_ALLOWED_HOSTS`: Comma-separated hostname(s) (use the Container App FQDN or a custom domain routed to it).
   - Database connection (values printed by the setup script or chosen by you):
     - `POSTGRES_HOST`: Internal FQDN (for example `starlight-db.internal.<env>.<region>.azurecontainerapps.io`).
     - `POSTGRES_DB`
     - `POSTGRES_USER`
     - `POSTGRES_PASSWORD`

3. **Deploy automatically**
   - Push/merge to `main`. The workflow will:
     1. Log in to Azure with the service principal.
     2. Build the Docker image and push both `:SHA` and `:latest` tags to ACR.
     3. Ensure the Container Apps CLI extension is installed.
     4. Create or update the `starlight-web` Container App so it pulls the new image, exposes port 8000 publicly, and injects all Django/PostgreSQL env vars (DB password is supplied as an Azure Container Apps secret).

If anything fails, check the workflow logs in GitHub Actions or re-run the `az` commands locally with the same service principal.
