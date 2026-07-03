#!/usr/bin/env python3
"""
Start / stop AIKON.

    python run.py [up|down|logs]

up   (default)  docker services up; in dev mode also runs the front on the
                host (runserver, celery, vite --watch, livereload) until Ctrl+C.
                Ctrl+C only stops the host processes; services keep running.
down            stops everything (docker compose down + api if delegated)
logs            follows the docker services logs
"""

import os
import shutil
import signal
import subprocess
import sys
import json
import socket
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRONT = ROOT / "front"
DOCKER_DIR = ROOT / "docker"
WIN = os.name == "nt"

# host processes started in dev mode: (name, command, cwd).
# celery is called through the venv bin directly (`uv run celery` fails, cf. front/run.sh);
# the worker's -B was dropped since beat runs as its own process (was doubled in run.sh).
VENV_BIN = FRONT / "app/.venv" / ("Scripts" if WIN else "bin")
DEV_PROCS = [
    (
        "django",
        ["uv", "run", "manage.py", "runserver", "localhost:{FRONT_PORT}"],
        FRONT / "app",
    ),
    (
        "celery-worker",
        [
            str(VENV_BIN / "celery"),
            "-A",
            "app.config.celery",
            "worker",
            "-c",
            "1",
            "-P",
            "threads",
            "--loglevel=INFO",
        ],
        FRONT,
    ),
    (
        "celery-beat",
        [
            str(VENV_BIN / "celery"),
            "-A",
            "app.config.celery",
            "beat",
            "--schedule",
            str(FRONT / "celery/celerybeat-schedule"),
            "--loglevel=INFO",
        ],
        FRONT,
    ),
    ("vite", ["npm", "run", "build", "--", "--watch"], FRONT / "app/svelte"),
]


def read_env() -> dict:
    env_file = ROOT / ".env"
    if not env_file.exists():
        sys.exit("no .env found: run `python setup.py` first")
    return dict(
        line.split("=", 1)
        for line in env_file.read_text().splitlines()
        if "=" in line and not line.startswith("#")
    )


def compose(*args) -> None:
    subprocess.run(["docker", "compose", *args], cwd=DOCKER_DIR, check=True)


def spawn(name: str, cmd: list, cwd: Path) -> subprocess.Popen:
    cmd = [c.format(**ENV) for c in cmd]
    cmd[0] = shutil.which(cmd[0]) or sys.exit(
        f"'{cmd[0]}' not found, run `python setup.py` first"
    )
    kwargs = (
        {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
        if WIN
        else {"start_new_session": True}
    )
    print(f"starting {name}: {' '.join(cmd)}")
    return subprocess.Popen(cmd, cwd=cwd, **kwargs)


def stop(name: str, proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    try:
        if WIN:
            proc.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            os.killpg(proc.pid, signal.SIGTERM)
        proc.wait(timeout=10)
    except (subprocess.TimeoutExpired, ProcessLookupError):
        proc.kill()
    print(f"stopped {name}")


def run_dev() -> None:
    procs = {name: spawn(name, cmd, cwd) for name, cmd, cwd in DEV_PROCS}
    print(
        f"\n→ http://localhost:{ENV['FRONT_PORT']}  (Ctrl+C stops the host "
        "processes; `python run.py down` also stops the docker services)\n"
    )
    try:
        while True:
            for name, p in procs.items():
                if p.poll() not in (None, 0):
                    print(f"\n'{name}' exited with code {p.returncode}, shutting down")
                    raise KeyboardInterrupt
            time.sleep(2)
    except KeyboardInterrupt:
        print()
        for name, p in procs.items():
            stop(name, p)


def run_api(action: str) -> None:
    api_run = ROOT / "api/run.py"
    if not api_run.exists():
        return
    if ENV.get("MODE") == "dev":
        print("api: start it separately with `python api/run.py` (host mode)")
    else:
        subprocess.run([sys.executable, str(api_run), action], cwd=ROOT / "api")


def doctor() -> None:
    ok = True

    def check(label: str, passed: bool, hint: str = "") -> None:
        nonlocal ok
        ok &= passed
        print(f"  {'✓' if passed else '✗'} {label}" + (f" — {hint}" if not passed and hint else ""))

    print("docker")
    check("daemon reachable", docker_ok(), "start Docker Desktop: open -a Docker")
    if not ok:
        sys.exit(1)

    print("containers")
    out = subprocess.run(
        ["docker", "compose", "ps", "--format", "json"],
        cwd=DOCKER_DIR, capture_output=True, text=True,
    ).stdout
    containers = [json.loads(l) for l in out.splitlines() if l.strip()]
    if not containers:
        check("services running", False, "run `python run.py` first")
    for c in containers:
        state = c.get("State", "")
        check(
            f"{c['Service']}: {state}",
            state == "running",
            f"docker compose logs {c['Service']} --tail 30",
        )

    print("ports")
    host_ports = {
        "django (host)": "FRONT_PORT",
        "aiiinotate": "AIIINOTATE_PORT",
        "mirador": "MIRADOR_PORT",
        "cantaloupe": "CANTALOUPE_PORT",
        "postgres": "DB_PORT",
        "redis": "REDIS_PORT",
        "mongo": "MONGODB_PORT",
    }
    if ENV["MODE"] != "dev":
        host_ports = {"nginx": "NGINX_PORT"}
    for name, key in host_ports.items():
        check(f"{name} on :{ENV[key]}", port_open(ENV[key]))

    sys.exit(0 if ok else 1)


def docker_ok() -> bool:
    return not subprocess.run(["docker", "info"], capture_output=True).returncode


def port_open(port: str) -> bool:
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", int(port))) == 0


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "up"
    ENV = read_env()
    if not docker_ok():
        sys.exit("docker daemon not reachable — start Docker Desktop and retry")

    if action == "doctor":
        doctor()
    elif action == "down":
        compose("down")
        run_api("down")
    elif action == "logs":
        compose("logs", "-f")
    elif action == "up":
        compose("up", "-d")
        run_api("up")
        if ENV["MODE"] == "dev":
            run_dev()
        else:
            port = ENV.get("NGINX_PORT", "8080")
            url = (
                f"https://{ENV['PROD_URL']}"
                if ENV["MODE"] == "prod"
                else f"http://localhost:{port}"
            )
            print(f"→ {url}")
    else:
        sys.exit(__doc__)
