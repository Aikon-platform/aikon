#!/usr/bin/env python3
import secrets
import string
from pathlib import Path
from typing import Dict, Optional

"""
Python script to generate all .env files needed for running the project locally
- .env
- front/app/config/.env
- front/cantaloupe/.env
- api/.env
- api/.env.dev
"""

ENV_FILES = {
    ".env": {
        "SETUP_MODE": "dev",
        "DOCKER": True,
        "APP_LANG": "en",
        "ADMIN_PASSWORD": "",
        "DATA_DIR": "/path/to/project/files",  # TODO create mediafiles and api data folder in it as well as sas data
        "INSTALLED_APPS": "regions,similarity",
        "FRONT_PORT": 8000,
        "API_PORT": 5000,
    },
    "front/app/config/.env": {
        "TARGET": "dev",
        "FRONT_PORT": 8000,
        "API_PORT": 5000,
        "DOCKER": True,
        "APP_NAME": "aikon",
        "APP_LANG": "en",
        "DEBUG": True,
        "INSTALLED_APPS": "regions,similarity",
        "MEDIA_DIR": "/absolute/path/to/project/mediafiles",
        "POSTGRES_DB": "aikon",
        "POSTGRES_USER": "admin",
        "POSTGRES_PASSWORD": "",
        "ALLOWED_HOSTS": "localhost,127.0.0.1,redis,web,db,api,cantaloupe,sas",
        "SECRET_KEY": "",
        "DB_PORT": 5432,
        "SAS_PORT": 8888,
        "CANTALOUPE_PORT": 8182,
        "CANTALOUPE_PORT_HTTPS": 8183,
        "REDIS_PORT": 6379,
        "GEONAMES_USER": "aikon",
        "PROD_URL": "app_name.domain-name.com",
        "PROD_API_URL": "api_name.domain-name.com",
        "REDIS_HOST": "redis",
        "DEFAULT_FROM_EMAIL": "noreply@domain.com",
        "EMAIL_HOST": "smtp.gmail.com",
        "EMAIL_HOST_USER": "app_name@mail.com",
        "EMAIL_HOST_PASSWORD": "",
        "APP_LOGO": "anr,ponts",
        "HTTP_PROXY": "",
        "HTTPS_PROXY": "",
    },
    "front/cantaloupe/.env": {
        "CANTALOUPE_PORT": 8182,
        "CANTALOUPE_PORT_HTTPS": 8183,
        "CANTALOUPE_BASE_URI": "",
        "CANTALOUPE_IMG": "/absolute/path/to/project/mediafiles/img/",
        "CANTALOUPE_DIR": "/absolute/path/to/project/cantaloupe/",
    },
    "api/.env": {
        "TARGET": "dev",
        "API_PORT": 5000,
        "DOCKER": True,
        "INSTALLED_APPS": "regions,similarity",
        "PROD_API_URL": "api_name.domain-name.com",
        "DATA_FOLDER": "data/",
        "YOLO_CONFIG_DIR": "data/yolotmp/",
    },
    "api/.env.dev": {
        "API_PORT": 5000,
        "DEVICE_NB": 0,
        "DRAMATIQ_PROM_PORT": 9192,
    },
}


class EnvGenerator:
    def __init__(self, template_path: str = ".env.template", prompt: bool = False):
        self.root = Path(__file__).parent.parent
        self.template_path = self.root / template_path
        self.env_vars: Dict[str, str] = {}
        self.prompt = prompt
        self.current_desc = ""

    def load_template(self) -> None:
        with open(self.template_path) as f:
            for line in f:
                self.set_value(line)

    def set_value(self, line) -> None:
        line = line.strip()
        if line.startswith("#"):
            self.current_desc = line.lstrip("#").strip()
            return
        if not line or "=" not in line:
            return
        key, value = line.split("=", 1)
        self.env_vars[key] = self.get_default_value(key, value)

    def get_default_value(self, key: str, value) -> str:
        key = key.strip()
        value = value.strip()

        if not value and any(secret in key for secret in ["SECRET", "PASSWORD", "KEY"]):
            value = self.generate_secret()

        if "PORT" in key:
            value = self.generate_port(value)

        if self.prompt:
            value = self.prompt_user(key, value)
        return value

    def prompt_user(self, key: str, value: str = None, desc: str = None) -> str:
        prompt_msg = f"Enter value for {key} ({desc or self.current_desc})"
        value = value or self.env_vars.get(key)
        if value:
            prompt_msg += f"\n[Press ENTER to keep: {value}]: "
        user_input = input(prompt_msg).strip()

        # TODO add keep empty option
        if user_input:
            value = user_input

        # TODO verify type?
        return value

    @staticmethod
    def check_port_available(port: int) -> bool:
        import socket

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("localhost", port)) != 0

    @staticmethod
    def generate_secret(length: int = 50) -> str:
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return "".join(secrets.choice(alphabet) for _ in range(length))

    def generate_port(self, port) -> int:
        try:
            port = int(port)
        except ValueError:
            port = 1234

        if not self.check_port_available(port):
            port += 1
            while not self.check_port_available(port):
                port += 1
        return port

    def derive_values(self) -> None:
        mode = self.env_vars.get("SETUP_MODE", "local")

        is_docker = self.env_vars.get("DOCKER", True)
        self.env_vars["DOCKER"] = str(is_docker)
        self.env_vars["TARGET"] = "prod" if mode == "prod" else "dev"
        self.env_vars["DEBUG"] = "False" if mode == "prod" else "True"

        data_dir = Path(self.env_vars.get("DATA_DIR")).resolve()
        # front media directory
        self.env_vars["MEDIA_DIR"] = (
            "/data/mediafiles" if is_docker else f"{data_dir}/mediafiles"
        )
        # api files
        self.env_vars["DATA_FOLDER"] = "/data/api/" if is_docker else f"{data_dir}/api/"
        self.env_vars["YOLO_CONFIG_DIR"] = (
            "/data/yolotmp/" if is_docker else f"{data_dir}/yolotmp/"
        )
        self.env_vars["CANTALOUPE_IMG"] = f"{self.env_vars['MEDIA_DIR']}/img/"

        if mode == "prod":
            self.env_vars["PROD_URL"] = self.prompt_user(
                "PROD_URL", desc="URL for production front-end (without https://)"
            )
            self.env_vars["PROD_API_URL"] = self.prompt_user(
                "PROD_API_URL", desc="URL for production API (with https://)"
            )
            self.env_vars["CANTALOUPE_BASE_URI"] = self.env_vars["PROD_URL"]

            self.env_vars["EMAIL_HOST"] = self.prompt_user(
                "EMAIL_HOST",
                desc="SMTP server (https://github.com/Aikon-platform/aikon/wiki/Email-Setup#smtp-server-setup)",
            )
            self.env_vars["EMAIL_HOST_USER"] = self.prompt_user(
                "EMAIL_HOST_USER",
                desc="Email address (https://github.com/Aikon-platform/aikon/wiki/Email-Setup#smtp-server-setup)",
            )
            self.env_vars["EMAIL_HOST_PASSWORD"] = self.prompt_user(
                "EMAIL_HOST_PASSWORD",
                desc="Email password (https://github.com/Aikon-platform/aikon/wiki/Email-Setup#smtp-server-setup)",
            )
            self.env_vars["DEFAULT_FROM_EMAIL"] = self.prompt_user(
                "DEFAULT_FROM_EMAIL",
                desc="Address sending app emails (https://github.com/Aikon-platform/aikon/wiki/Email-Setup#smtp-server-setup)",
            )

        self.env_vars["REDIS_HOST"] = "redis" if is_docker else "localhost"
        self.env_vars["DB_HOST"] = "db" if is_docker else "localhost"

    def write_env_file(self, path: Path, vars_subset: Optional[Dict] = None) -> None:
        vars_to_write = vars_subset or self.env_vars

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            for key, value in sorted(vars_to_write.items()):
                f.write(f"{key}={value}\n")

    def generate_all(self) -> None:
        self.load_template()
        self.derive_values()

        docker_env = self.root / "docker" / ".env"
        self.write_env_file(docker_env)

        front_env = self.root / "front" / "app" / "config" / ".env"
        front_vars = {
            k: v
            for k, v in self.env_vars.items()
            if not k.startswith("API_") or k in ["API_URL", "API_PORT"]
        }
        self.write_env_file(front_env, front_vars)

        # API
        api_env = self.root / "api" / ".env"
        api_vars = {
            "TARGET": self.env_vars["TARGET"],
            "DOCKER": self.env_vars["DOCKER"],
            "INSTALLED_APPS": self.env_vars.get("API_INSTALLED_APPS", ""),
            "API_PORT": self.env_vars["API_PORT"],
            "PROD_URL": self.env_vars.get("PROD_URL", ""),
            "API_DATA_FOLDER": self.env_vars["API_DATA_FOLDER"],
            "YOLO_CONFIG_DIR": self.env_vars["YOLO_CONFIG_DIR"],
            "REDIS_HOST": self.env_vars["REDIS_HOST"],
            "REDIS_PORT": self.env_vars["REDIS_PORT"],
            "REDIS_PASSWORD": self.env_vars.get("REDIS_PASSWORD", ""),
        }
        self.write_env_file(api_env, api_vars)

        # API dev
        if self.env_vars.get("SETUP_MODE") == "development":
            api_dev_env = self.root / "api" / ".env.dev"
            dev_vars = {
                "DEVICE_NB": self.env_vars.get("DEVICE_NB", "0"),
                "DRAMATIQ_PROM_PORT": self.env_vars.get("DRAMATIQ_PROM_PORT", "9192"),
            }
            self.write_env_file(api_dev_env, dev_vars)

        cantaloupe_env = self.root / "front" / "cantaloupe" / ".env"
        cantaloupe_vars = {
            "CANTALOUPE_BASE_URI": self.env_vars["CANTALOUPE_BASE_URI"],
            "CANTALOUPE_IMG": self.env_vars["CANTALOUPE_IMG"],
            "CANTALOUPE_PORT": self.env_vars["CANTALOUPE_PORT"],
            "CANTALOUPE_PORT_HTTPS": self.env_vars["CANTALOUPE_PORT_HTTPS"],
        }
        self.write_env_file(cantaloupe_env, cantaloupe_vars)

        print("✅ All .env files generated successfully:")
        print(f"   Mode: {self.env_vars['SETUP_MODE']}")
        print(f"   Docker: {self.env_vars['DOCKER']}")


if __name__ == "__main__":
    generator = EnvGenerator()
    generator.generate_all()
