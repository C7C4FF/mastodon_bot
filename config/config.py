from pathlib import Path
import os


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_env_file(file_path=None):
    env_path = Path(file_path) if file_path else PROJECT_ROOT / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")

        if key.startswith("export "):
            key = key.removeprefix("export ").strip()

        os.environ.setdefault(key, value)


load_env_file()


CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL")
credential_json = os.getenv("CREDENTIAL_JSON") or os.getenv("CRENDENTIAL_JSON")
CREDENTIAL_JSON = str(PROJECT_ROOT / credential_json) if credential_json and not Path(credential_json).is_absolute() else credential_json
GOOGLE_SHEET_URL = os.getenv("GOOGLE_SHEET_URL")
