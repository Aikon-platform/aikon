import os
import django
from django.contrib.auth import get_user_model
from app.config.settings import ENV, EMAIL_HOST_USER


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.config.settings")
django.setup()


def create_superuser():
    User = get_user_model()
    username = ENV.str("POSTGRES_USER", default="")
    email = ENV.str("CONTACT_EMAIL", default=EMAIL_HOST_USER)
    password = ENV.str("POSTGRES_PASSWORD", default="")

    try:
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username, email, password)
            print("Superuser created.")
        else:
            print("Superuser already exists.")
    except Exception as e:
        print(f"Failed to create superuser: {e}")


if __name__ == "__main__":
    create_superuser()
