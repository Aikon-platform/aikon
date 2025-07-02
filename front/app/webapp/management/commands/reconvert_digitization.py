from django.core.management.base import BaseCommand

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
        group.add_argument(
            "--all",
            "-a",
            action="store_true",
            help="Reconvert digitizations for all witnesses",
        )

    def handle(self, *args, **options):
        digitization_id = options.get("digitization")
        witness_id = options.get("witness")
        process_all = options.get("all")

        if digitization_id:
            self.process_digitization(digitization_id)
        elif witness_id:
            self.process_witness(witness_id)
        elif process_all:
            self.process_all_witnesses()

    def process_digitization(self, digitization_id):
        """Process a single digitization"""
        try:
            digitization = Digitization.objects.get(id=digitization_id)
            self.stdout.write(
                self.style.SUCCESS(
                    f"⚙️ Processing Digitization #{digitization_id} ({digitization.digit_type})"
                )
            )

            task = convert_digitization.delay(digitization_id)
            self.stdout.write(self.style.SUCCESS(f"Task started with ID: {task.id}"))

        except Digitization.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"⛔️ Digitization #{digitization_id} does not exist")
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
                self.style.ERROR(f"⛔️ Witness #{witness_id} does not exist")
            )

    def process_all_witnesses(self):
        """Process all digitizations for all witnesses"""
        witnesses = Witness.objects.all()

        if not witnesses.exists():
            self.stdout.write(self.style.WARNING("No witnesses found in the database"))
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Processing digitizations for all {witnesses.count()} witnesses:"
            )
        )

        digit_count = 0

        for witness in witnesses:
            digits = witness.get_digits()

            if not digits:
                self.stdout.write(
                    self.style.WARNING(f"Witness #{witness.id} has no digitizations")
                )
                continue

            self.stdout.write(
                f"Witness #{witness.id}: Processing {digits.count()} digitization(s)"
            )

            for digit in digits:
                digit_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"📜 Digitization #{digit.id} ({digit.digit_type})"
                    )
                )
                task = convert_digitization.delay(digit.id)
                self.stdout.write(f"Task started with ID: {task.id}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Started conversion for {digit_count} digitizations across {witnesses.count()} witnesses"
            )
        )
        self.stdout.write(
            self.style.WARNING(
                "The conversion processes are running in the background."
            )
        )
