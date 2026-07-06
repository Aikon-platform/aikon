#!/usr/bin/env python3
"""
AIKON unified installer (cross-platform, stdlib only).

    python setup.py [--mode local|dev|prod] [--defaults]

local = everything in Docker, zero prompt, app running at the end
dev   = services in Docker, front deps installed on the host, then `python run.py`
prod  = everything in Docker, full prompts, app running at the end
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))
import generate_env

FRONT_APP = ROOT / "front/app"
SVELTE_DIR = FRONT_APP / "svelte"
DOCKER_DIR = ROOT / "docker"

UV_INSTALL = {
    "posix": "curl -LsSf https://astral.sh/uv/install.sh | sh",
    "nt": 'powershell -c "irm https://astral.sh/uv/install.ps1 | iex"',
}


def sh(cmd: list|str, cwd: Path = None, shell = False, capture_output = False, text = False) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=capture_output, shell=shell, text=text)


def which(name: str) -> str:
    return shutil.which(name) or sys.exit(
        f"'{name}' is required but not found.\n"
        + (
            f"Install uv with:\n  {UV_INSTALL[os.name]}"
            if name == "uv"
            else f"Install {name} then rerun setup."
        )
    )


def check_docker() -> None:
    which("docker")
    if subprocess.run(["docker", "compose", "version"], capture_output=True).returncode:
        sys.exit("docker compose v2 is required (https://docs.docker.com/compose/install/)")
    if subprocess.run(["docker", "info"], capture_output=True).returncode:
        sys.exit("docker daemon not reachable — start it (Docker Desktop, `colima start`, `orbstack`, ...) and retry")


def db_password_ok(v: dict) -> bool:
    return not subprocess.run(
        ["docker", "compose", "exec", "-T",
         "-e", f"PGPASSWORD={v['POSTGRES_PASSWORD']}", "db",
         "psql", "-U", v["POSTGRES_USER"], "-d", v["POSTGRES_DB"], "-c", "\\q"],
        cwd=DOCKER_DIR, capture_output=True,
    ).returncode


def ensure_db_credentials(v: dict) -> None:
    # Postgres bakes credentials into its volume on first init and ignores the
    # env afterwards; a regenerated password then fails to authenticate.
    if db_password_ok(v):
        return
    if v["MODE"] != "dev":
        sys.exit(
            f"✗ Postgres rejects the .env password (stale volume) and MODE={v['MODE']} "
            "forbids auto-wipe. Fix manually: docker compose down -v (DESTROYS DATA)."
        )
    print("⚠ stale Postgres volume (password mismatch) — wiping volumes (dev)")
    sh(["docker", "compose", "down", "-v"], cwd=DOCKER_DIR)
    sh(["docker", "compose", "up", "-d", "--build", "--wait"], cwd=DOCKER_DIR)


def setup_dev(v: dict) -> None:
    uv, npm = which("uv"), which("npm")
    sh([uv, "sync", "--group=dev"], cwd=FRONT_APP)
    sh([npm, "install"], cwd=SVELTE_DIR)
    sh([npm, "run", "build"], cwd=SVELTE_DIR)
    sh(["docker", "compose", "up", "-d", "--build", "--wait"], cwd=DOCKER_DIR)
    ensure_db_credentials(v)
    sh([uv, "run", "manage.py", "migrate"], cwd=FRONT_APP)
    sh([uv, "run", "manage.py", "create_superuser_check"], cwd=FRONT_APP)
    print("\n✅ dev setup complete. Start everything with:  python run.py")


def setup_docker(v: dict) -> None:
    sh(["docker", "compose", "up", "-d", "--build", "--wait"], cwd=DOCKER_DIR)
    ensure_db_credentials(v)
    url = (
        f"https://{v['PROD_URL']}"
        if v["MODE"] == "prod"
        else f"http://localhost:{v['NGINX_PORT']}"
    )
    print(f"\n✅ app starting (migrations run inside the container) → {url}")


def setup_api(mode: str, use_defaults: bool) -> None:
    api_install = ROOT / "api/install.py"
    if not api_install.exists():
        print("api/ not initialized (git submodule update --init), skipping API setup")
        return
    cmd = [
        sys.executable,
        str(api_install),
        "--mode",
        mode,
        "--root-env",
        str(ROOT / ".env"),
    ] + (["--defaults"] if use_defaults else [])
    sh(cmd, cwd=ROOT / "api")

def detect_firewall() -> None:
    """
    firewalls can silently cause docker-to-host HTTP requests to fail.
    detect if a firewall is used, and if so print an error message.
    MacOS is not concerned: firewall is disabled by default and Docker-to-Host
    queries are not blocked by its firewall (socketfilterfw)
    """
    script = f"bash {ROOT / 'scripts' / 'check_firewall.sh'}"
    msg = lambda firewall: print(
        "\n"
        f"⚠️  Detected active firewall `{firewall}`, "
        "which may cause network errors (Docker-to-Host requests blocked.) "
        "Run the following script to add Docker's network to firewall:\n"
        f">>> {script}\n"
    )
    _sh = lambda cmd: sh(cmd, cwd=ROOT, shell=True, capture_output=True, text=True)
    # 1. ubuntu/debian
    if which("ufw") and "Status: active" in _sh("sudo ufw status").stdout:
        msg("ufw")
    # 2. fedora
    elif which("firewall-cmd") and "running" in _sh("firewall-cmd --state").stdout:
        msg("firewalld")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=generate_env.MODES)
    parser.add_argument("--defaults", action="store_true", help="never prompt, use defaults")
    args = parser.parse_args()

    check_docker()
    mode = args.mode or generate_env.ask_mode()
    v = generate_env.generate(mode, args.defaults or mode == "local")

    (setup_dev if mode == "dev" else setup_docker)(v)
    setup_api(mode, args.defaults)

    detect_firewall()