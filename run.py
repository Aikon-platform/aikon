#!/usr/bin/env python3
"""
Start / stop AIKON.

    python run.py [up|down|logs|doctor]

up   (default)  docker services up; in dev mode also runs the front on the
                host (runserver, celery, vite --watch, livereload) until Ctrl+C.
down            stops everything (docker compose down + api if delegated)
logs            follows the docker services logs
doctor          summarize
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

if str(FRONT) not in sys.path:
    sys.path.append(str(FRONT))
from app.webapp.utils.logger import log

LOG_KWARGS = {
    "msg_type": "magenta",
    "with_time": False,
    "compact": True
}

# host processes started in dev mode: (name, command, cwd).
# celery is called through the venv bin directly (`uv run celery` fails, cf. front/run.sh);
# the worker's -B was dropped since beat runs as its own process (was doubled in run.sh).
VENV_BIN = FRONT / "app/.venv" / ("Scripts" if WIN else "bin")
DEV_PROCS = [
    (
        # NOTE: runserver on 0.0.0.0: 127.0.0.1 is only for the host's loopback, 0.0.0.0 can be accessed from the docker-compose bridge network
        "django",
        ["uv", "run", "manage.py", "runserver", "0.0.0.0:{FRONT_PORT}"],
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


def read_env(path: Path = ROOT / ".env") -> dict:
    if not path.exists():
        sys.exit(f"no {path.name} found: run `python install.py` first")
    return dict(
        line.split("=", 1)
        for line in path.read_text().splitlines()
        if "=" in line and not line.startswith("#")
    )


def compose(*args) -> None:
    subprocess.run(["docker", "compose", *args], cwd=DOCKER_DIR, check=True)


def spawn(name: str, cmd: list, cwd: Path, env: dict = None) -> subprocess.Popen:
    cmd = [c.format(**ENV) for c in cmd]
    cmd[0] = shutil.which(cmd[0]) or sys.exit(
        f"'{cmd[0]}' not found, run `python install.py` first"
    )
    kwargs = (
        {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
        if WIN
        else {"start_new_session": True}
    )
    log(f"starting {name}: {' '.join(cmd)}", **{**LOG_KWARGS, "msg_type": "white"})
    return subprocess.Popen(cmd, cwd=cwd, env={**os.environ, **(env or {})}, **kwargs)


def kill_stale(*patterns: str) -> None:
    if WIN:
        return
    for p in patterns:
        if not subprocess.run(["pkill", "-f", p], capture_output=True).returncode:
            log(f"killed stale '{p}'", **{**LOG_KWARGS, "msg_type": "white"})
    time.sleep(1)


def stop(name: str, proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    try:
        if WIN:
            proc.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            os.killpg(proc.pid, signal.SIGTERM)
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill() if WIN else os.killpg(proc.pid, signal.SIGKILL)
        proc.wait()
    except ProcessLookupError:
        pass
    log(f"stopped {name}", **LOG_KWARGS)


def run_dev() -> None:
    kill_stale("celery -A app.config.celery", "manage.py runserver")
    procs_def = [(n, c, cwd, None) for n, c, cwd in DEV_PROCS]
    if (ROOT / "api/run.py").exists():
        procs_def += api_dev_procs()
    procs = {name: spawn(name, cmd, cwd, env) for name, cmd, cwd, env in procs_def}
    log(f"\n→ http://localhost:{ENV['FRONT_PORT']}  (Ctrl+C to stop, twice to also stop docker)\n", **LOG_KWARGS)
    try:
        while True:
            for name, p in procs.items():
                if p.poll() not in (None, 0):
                    print(f"\n'{name}' exited with code {p.returncode}, shutting down")
                    raise KeyboardInterrupt
            time.sleep(2)
    except KeyboardInterrupt:
        pass
    finally:
        log("\nstopping host processes (hit Ctrl+C again to also stop docker services)", **LOG_KWARGS)
        teardown = False

        def on_sigint(*_):
            nonlocal teardown
            teardown = True

        signal.signal(signal.SIGINT, on_sigint)
        for name, p in procs.items():
            stop(name, p)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        if teardown:
            compose("down")
        else:
            log("docker services still running: run `python run.py down` to stop them", **LOG_KWARGS)


def run_api(action: str) -> None:
    api_run = ROOT / "api/run.py"
    if not api_run.exists() or ENV.get("MODE") == "dev":
        return
    subprocess.run([sys.executable, str(api_run), action], cwd=ROOT / "api")


def doctor() -> None:
    ok = True
    doctor_kwargs = {**LOG_KWARGS, "msg_type": "white"}

    def check(label: str, passed: bool, hint: str = "") -> None:
        nonlocal ok
        ok &= passed
        log(f"  {'✓' if passed else '✗'} {label}" + (f" — {hint}" if not passed and hint else ""), **{**LOG_KWARGS, "msg_type": "success" if passed else "error"})

    log("docker", **doctor_kwargs)
    check("daemon reachable", docker_ok(), "start Docker Desktop: open -a Docker")
    if not ok:
        sys.exit(1)

    log("containers", **doctor_kwargs)
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

    log("database", **doctor_kwargs)
    check(
        "postgres accepts the .env password",
        db_password_ok(),
        "stale volume → dev: `python install.py --mode dev` auto-wipes; "
        "else `docker compose down -v` (DESTROYS DATA)",
    )

    log("ports", **doctor_kwargs)
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


def db_password_ok() -> bool:
    return not subprocess.run(
        ["docker", "compose", "exec", "-T",
         "-e", f"PGPASSWORD={ENV['POSTGRES_PASSWORD']}", "db",
         "psql", "-U", ENV["POSTGRES_USER"], "-d", ENV["POSTGRES_DB"], "-c", "\\q"],
        cwd=DOCKER_DIR, capture_output=True,
    ).returncode


def port_open(port: str) -> bool:
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", int(port))) == 0


def api_dev_procs() -> list:
    kill_stale("dramatiq app.main", "flask --app app.main")
    api_env = read_env(ROOT / "api/.env")
    port = api_env.get("API_PORT", "5001")
    device = api_env.get("DEVICE_NB", "") or "0"
    return [
        ("api-flask",
         ["uv", "run", "flask", "--app", "app.main", "run", "--debug", "-p", port],
         ROOT / "api", {"CUDA_VISIBLE_DEVICES": device}),
        ("api-dramatiq",
         ["uv", "run", "dramatiq", "app.main", "-t", "1", "-p", "1"],
         ROOT / "api", {"CUDA_VISIBLE_DEVICES": device}),
    ]


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "up"
    ENV = read_env()
    if not docker_ok():
        sys.exit("docker daemon not reachable — start Docker and retry")

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
            log(f"→ {url}", **{**LOG_KWARGS, "compact": False})
    else:
        sys.exit(__doc__)
