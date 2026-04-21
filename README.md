# IS601 Module 13 – JWT Login/Registration + Playwright E2E Testing

FastAPI back-end with JWT authentication, front-end registration and login pages, and Playwright E2E tests — all wired into a CI/CD pipeline that deploys to Docker Hub.

## Docker Hub

**Repository:** https://hub.docker.com/r/kushyarwar/is601-module13

**Image:** `kushyarwar/is601-module13:latest`

```bash
docker pull kushyarwar/is601-module13:latest
docker run -p 8000:8000 \
  -e DATABASE_URL=<your-postgres-url> \
  -e JWT_SECRET=<your-secret> \
  kushyarwar/is601-module13:latest
```

---

## Running Locally (Docker Compose)

```bash
docker-compose up --build
```

| Service | URL |
|---------|-----|
| API + Swagger | http://localhost:8000/docs |
| Register page | http://localhost:8000/static/register.html |
| Login page | http://localhost:8000/static/login.html |
| pgAdmin | http://localhost:5050 (admin@admin.com / admin) |

---

## Running Integration Tests Locally

Tests use **SQLite** locally — no Postgres required.

```bash
pip install -r requirements.txt
pytest tests/ --ignore=tests/e2e -v --cov=app --cov-report=term-missing
```

---

## Running Playwright E2E Tests Locally

```bash
# Install Playwright browser (first time only)
playwright install chromium

# Run E2E tests (starts a local server automatically)
pytest tests/e2e/ -v
```

The E2E conftest starts a throwaway SQLite-backed server on port 8001, runs the 4 browser tests, then shuts it down.

---

## API Endpoints

### Auth / User Routes

| Method | Path | Description |
|--------|------|-------------|
| POST | `/users/register` | Register — returns JWT + user info |
| POST | `/users/login` | Login with email + password — returns JWT |
| GET | `/users/` | List all users |
| GET | `/users/{id}` | Get user by ID |
| DELETE | `/users/{id}` | Delete user (cascades calculations) |

**Register request body:**
```json
{ "email": "you@example.com", "password": "yourpassword" }
```

**Register / Login response:**
```json
{ "token": "<jwt>", "message": "...", "user": { "id": 1, "username": "...", "email": "..." } }
```

### Calculation Routes (BREAD)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/calculations/` | Browse all |
| GET | `/calculations/{id}` | Read one |
| PUT | `/calculations/{id}` | Edit (recomputes result) |
| POST | `/calculations/` | Add new |
| DELETE | `/calculations/{id}` | Delete |
| GET | `/calculations/join/all` | Calculations with username |

Supported types: `Add`, `Sub`, `Multiply`, `Divide`

---

## CI/CD Pipeline

GitHub Actions (`.github/workflows/ci.yml`):

1. **Integration tests** — spins up PostgreSQL 15, runs `pytest` against a real Postgres DB
2. **Playwright E2E tests** — runs 4 browser tests (register positive/negative, login positive/negative) against a SQLite-backed local server
3. **Docker build & push** — on successful merge to `main`, builds and pushes `kushyarwar/is601-module13:latest`
4. **Trivy scan** — vulnerability scan on the pushed image

Required GitHub Secrets: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`

---

## Screenshots

*(Add your screenshots here after a successful CI run)*

### GitHub Actions – Workflow Passing
![GitHub Actions](Screenshots/github_actions.png)

### Playwright E2E Tests Passing
![Playwright Tests](Screenshots/playwright_tests.png)

### Register Page
![Register Page](Screenshots/register_page.png)

### Login Page
![Login Page](Screenshots/login_page.png)
