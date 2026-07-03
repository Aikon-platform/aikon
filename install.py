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
import socket
import subprocess
import sys
import time
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


def sh(cmd: list, cwd: Path = None) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


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


def wait_port(port: str, service: str, timeout: int = 90) -> None:
    print(f"waiting for {service} on localhost:{port}...")
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", int(port))) == 0:
                return
        time.sleep(1)
    sys.exit(f"{service} did not come up on port {port} within {timeout}s")


def setup_dev(v: dict) -> None:
    uv, npm = which("uv"), which("npm")
    sh([uv, "sync", "--group=dev"], cwd=FRONT_APP)
    sh([npm, "install"], cwd=SVELTE_DIR)
    sh([npm, "run", "build"], cwd=SVELTE_DIR)
    sh(["docker", "compose", "up", "-d", "--build"], cwd=DOCKER_DIR)
    wait_port(v["DB_PORT"], "postgres")
    sh([uv, "run", "manage.py", "migrate"], cwd=FRONT_APP)
    sh([uv, "run", "manage.py", "create_superuser_check"], cwd=FRONT_APP)
    print("\n✅ dev setup complete. Start everything with:  python run.py")


def setup_docker(v: dict) -> None:
    sh(["docker", "compose", "up", "-d", "--build"], cwd=DOCKER_DIR)
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
