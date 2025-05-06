from django.core.management.base import BaseCommand, CommandError

from app.webapp.models.digitization import Digitization
from app.webapp.models.witness import Witness
from app.webapp.tasks import convert_digitization


class Command(BaseCommand):
    help = "Reconvert a digitization to images"

    def add_arguments(self, parser):
        # Create a mutually exclusive group
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--digitization",
            "-d",
            type=int,
            help="ID of a specific digitization to reconvert",
        )
        group.add_argument(
            "--witness",
            "-w",
            type=int,
            help="ID of a witness to reconvert all its digitizations",
        )

    def handle(self, *args, **options):
        digitization_id = options.get("digitization")
        witness_id = options.get("witness")

        if digitization_id:
            self.process_digitization(digitization_id)
        elif witness_id:
            self.process_witness(witness_id)

    def process_digitization(self, digitization_id):
        """Process a single digitization"""
        try:
            digitization = Digitization.objects.get(id=digitization_id)
            self.stdout.write(
                self.style.SUCCESS(
                    f"⚙️ Processing digitization {digitization_id} ({digitization.digit_type})"
                )
            )

            task = convert_digitization.delay(digitization_id)
            self.stdout.write(self.style.SUCCESS(f"Task started with ID: {task.id}"))

        except Digitization.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f"Digitization with ID {digitization_id} does not exist"
                )
            )

    def process_witness(self, witness_id):
        """Process all digitizations for a witness"""
        try:
            witness = Witness.objects.get(id=witness_id)
            digits = witness.get_digits()

            if not digits:
                self.stdout.write(
                    self.style.WARNING(f"Witness {witness_id} has no digits")
                )
                return

            self.stdout.write(
                self.style.SUCCESS(
                    f"Processing {digits.count()} digitization(s) for witness {witness_id}:"
                )
            )

            for digit in digits:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"📜 Digitization #{digit.id} ({digit.digit_type})"
                    )
                )
                task = convert_digitization.delay(digit.id)
                self.stdout.write(
                    self.style.SUCCESS(f"Task started with ID: {task.id}")
                )

            self.stdout.write(
                self.style.WARNING(
                    "The conversion processes are running in the background."
                )
            )

        except Witness.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"Witness with ID {witness_id} does not exist")
            )
