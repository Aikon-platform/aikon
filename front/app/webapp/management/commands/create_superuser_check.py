import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.core.management import CommandError
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Create the superuser if they don't aldready exist, and update their password"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        env_vars = ["POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD", "EMAIL_HOST_USER"]
        env_dict = {}
        for vname in env_vars:
            env_dict[vname] = os.environ.get(vname)

        if any(v is None for v in env_dict.items()):
            self.stdout.write(
                self.style.ERROR(f"⛔️ To create the super user, the following environment variables must be set: {env_vars}")
            )
            return

        User = get_user_model()
        try:
            user = User.objects.filter(username=env_dict["POSTGRES_USER"]).first()
            # if the user exists, set it to superuser if necessary and update its password
            if user:
                if not user.is_superuser:
                    user.is_superuser = True
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✔️ User {env_dict['POSTGRES_USER']} updated to superuser."
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✔️ User {env_dict['POSTGRES_USER']} is aldready a superuser. Password updated."
                        )
                    )
                user.set_password(env_dict["POSTGRES_PASSWORD"])
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✔️ User {env_dict['POSTGRES_USER']} password updated to follow .env config."
                    )
                )
            # otherwise, create the superuser
            else:
                User.objects.create_superuser(
                    username=env_dict["POSTGRES_USER"],
                    email=env_dict["EMAIL_HOST_USER"],
                    password=env_dict["POSTGRES_PASSWORD"]
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✔️ New superuser {env_dict['POSTGRES_USER']} created."
                    )
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"⛔️ Error creating superuser: {e}")
            )
