import os
import subprocess
import time
import pytest
import httpx

SERVER_URL = "http://127.0.0.1:8001"
DB_PATH = "./e2e_test.db"


@pytest.fixture(scope="session", autouse=True)
def live_server():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{DB_PATH}"
    env["JWT_SECRET"] = "e2e-test-secret-key"

    proc = subprocess.Popen(
        ["python", "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8001"],
        env=env,
    )

    for _ in range(30):
        try:
            r = httpx.get(f"{SERVER_URL}/health", timeout=1)
            if r.status_code == 200:
                break
        except Exception:
            time.sleep(0.5)
    else:
        proc.terminate()
        raise RuntimeError("Test server failed to start on port 8001")

    yield SERVER_URL

    proc.terminate()
    proc.wait()
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
