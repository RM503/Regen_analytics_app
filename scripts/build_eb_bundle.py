"""Build a private Beanstalk bundle, including required local plot data and GEE key."""
from pathlib import Path
import argparse
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = ["Dockerfile", "flask_app.py", "config_loader.py",
         "gunicorn.conf.py", "credentials.json", "deploy/nginx.conf"]
DIRECTORIES = ["src", "static", "templates", "logos"]
SKIP = {"__pycache__", "test_data", ".DS_Store"}


def build(destination: Path) -> None:
    required = FILES + ["deploy/requirements.lock.txt", "src/dashboards/initial_market_data/plots_json"]
    for name in required:
        if not (ROOT / name).exists():
            raise FileNotFoundError(f"Required deployment input is missing: {name}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as bundle:
        for name in FILES:
            bundle.write(ROOT / name, name)
        bundle.write(ROOT / "deploy/requirements.lock.txt", "requirements.txt")
        for directory in DIRECTORIES:
            for path in sorted((ROOT / directory).rglob("*")):
                relative = path.relative_to(ROOT)
                metadata = any(part.endswith((".egg-info", ".dist-info")) for part in relative.parts)
                if path.is_file() and not metadata and not SKIP.intersection(relative.parts) and path.suffix != ".pyc":
                    bundle.write(path, relative)
        bundle.write(ROOT / "deploy/docker-compose.yml", "docker-compose.yml")
        bundle.write(ROOT / "deploy/prepare-host.sh", ".platform/hooks/predeploy/01-prepare-host.sh")
        bundle.write(ROOT / "deploy/verify-services.sh", ".platform/hooks/postdeploy/01-verify-services.sh")
        bundle.writestr("config.py", 'import os\nUSE_LOCAL_DB = os.getenv("USE_LOCAL_DB", "false").lower() == "true"\nLOCAL_DB_CONFIG = {}\n')
        bundle.writestr(".dockerignore", ".env\n.env.*\n.platform\n")
    destination.chmod(0o600)
    print(f"Built {destination} ({destination.stat().st_size:,} bytes)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    build(parser.parse_args().output)
