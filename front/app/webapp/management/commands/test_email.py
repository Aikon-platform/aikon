import logging
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.core.mail import get_connection

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Test email configuration"

    def add_arguments(self, parser):
        parser.add_argument(
            "--to", type=str, required=True, help="Email address to send test email to"
        )

    def handle(self, *args, **options):
        self.stdout.write("Testing email configuration...")

        self.stdout.write(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        self.stdout.write(f"EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'Not set')}")
        self.stdout.write(f"EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'Not set')}")
        self.stdout.write(
            f"EMAIL_USE_TLS: {getattr(settings, 'EMAIL_USE_TLS', 'Not set')}"
        )
        self.stdout.write(
            f"EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'Not set')}"
        )
        self.stdout.write(
            f"DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set')}"
        )

        try:
            connection = get_connection()
            connection.open()
            self.stdout.write(self.style.SUCCESS("✅ SMTP connection successful"))
            connection.close()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ SMTP connection failed: {e}"))
            return

        try:
            result = send_mail(
                subject="Test Email from Django",
                message="This is a test email to verify web app email configuration.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[options["to"]],
                fail_silently=False,
            )

            if result == 1:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Test email sent successfully to {options['to']}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"❓ Email sending returned: {result}")
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to send test email: {e}"))
