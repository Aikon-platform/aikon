from django.core.management.base import BaseCommand

from app.webapp.models.witness import Witness
from app.webapp.tasks import convert_digitization
from webapp.utils.functions import zip_dirs, zip_img
from webapp.utils.iiif.annotation import get_training_regions


class Command(BaseCommand):
    help = "Export formatted files for object extraction model training"

    def add_arguments(self, parser):
        # Create a mutually exclusive group
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--witness",
            "-w",
            type=int,
            help="ID of the witness to download files",
        )

    def handle(self, *args, **options):
        witness_id = options.get("witness")
        self.export_training_files(witness_id)

    def export_training_files(self, witness_id):
        """Process all files for a witness"""
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

            dirnames_contents = {}
            img_urls = []

            for digit in digits:
                dirnames_contents[digit.get_ref()] = []
                regions = digit.get_regions()

                if not regions:
                    self.stdout.write(
                        self.style.WARNING(f"Digitization {digit.id} has no regions")
                    )
                    return

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Processing {regions.count()} regions for digitization {digit.id}:"
                    )
                )

                for region in regions:
                    dirnames_contents[region.get_ref()].extend(
                        get_training_regions(region)
                    )
                    print(dirnames_contents)

                    self.stdout.write(
                        self.style.SUCCESS(f"📜 Regions #{region.id} exported")
                    )

                img_urls.extend(digit.get_imgs(is_abs=False))

                self.stdout.write(self.style.SUCCESS(f"📜 Images #{digit.id} exported"))

            return zip_dirs(dirnames_contents), zip_img(img_urls)

        except Witness.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"⛔️ Witness #{witness_id} does not exist")
            )

    def process_witnesses(self, witness_id):
        """Process all files for a witness list"""
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
