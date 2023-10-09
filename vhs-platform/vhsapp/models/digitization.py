import threading
from PIL import Image
from functools import partial

from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
from pdf2image import convert_from_path

from vhsapp.utils.logger import log, console

from vhsapp.models.constants import (
    MANIFEST,
    MS_ABBR,
    VOL_ABBR,
    IMG_INFO,
    MANIFEST_INFO,
)
from vhsapp.utils.functions import (
    rename_file,
    convert_to_jpeg,
    pdf_to_img,
    get_imgs,
    delete_files,
)
from vhsapp.utils.paths import (
    BASE_DIR,
    IMG_PATH,
    MS_PDF_PATH,
    VOL_PDF_PATH,
    MEDIA_PATH,
)
from vhsapp.utils.iiif.validation import (
    parse_manifest,
    validate_manifest,
)

from vhsapp.utils.iiif.download import extract_images_from_iiif_manifest
from vhsapp.utils.iiif.annotation import send_anno_request, unindex_witness
from vhsapp.models.witness import Volume, Manuscript
from vhsapp.models import get_wit_type, get_wit_abbr


def remove_digitization(wit_id, wit_abbr, other_media=None):
    unindex_witness(wit_id, get_wit_type(wit_abbr))
    delete_files(get_imgs(f"{wit_abbr}{wit_id}"))
    if other_media:
        delete_files(other_media, f"{BASE_DIR}/{MEDIA_PATH}")


class Digitization(models.Model):
    # TODO link this class to a unique
    # source = models.ForeignKey(
    #     Witness, verbose_name=WITNESS, on_delete=models.SET_NULL, null=True
    # )

    class Meta:
        abstract = True


#############################
#           IMG           #
#############################


class Picture(Digitization):
    class Meta:
        verbose_name = "Image file"
        verbose_name_plural = "Images files"
        abstract = True  # TODO: make this class not abstract

    def __str__(self):
        return self.image.name

    image = models.ImageField(
        verbose_name="Image",
        upload_to=partial(rename_file, path=IMG_PATH),
        validators=[
            FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "tif"])
        ],
        help_text=IMG_INFO,
    )

    def get_wit_id(self):
        return self.volume.id if "vol" in self.image.name else self.manuscript.id

    def get_wit_abbr(self):
        return VOL_ABBR if "vol" in self.image.name else MS_ABBR

    def save(self, *args, **kwargs):
        if self.image:
            img = Image.open(self.image)
            # Check if the image format is not JPEG
            if img.format != "JPEG":
                # Convert the image to JPEG format
                self.image = convert_to_jpeg(self.image)
        # Call the parent save method to save the model
        super().save(*args, **kwargs)

        event = threading.Event()

        t = threading.Thread(
            target=send_anno_request,
            args=(
                event,
                f"{self.get_wit_id()}",
                f"{self.get_wit_abbr()}",
            ),
        )
        t.start()

    def delete(self, using=None, keep_parents=False):
        super().delete()


# Receive the pre_delete signal and delete the file associated with the model instance
@receiver(pre_delete, sender=Picture)
def image_delete(sender, instance, **kwargs):
    # Pass false so ImageField doesn't save the model
    unindex_witness(instance.get_wit_id(), get_wit_type(instance.get_wit_abbr()))
    instance.image.delete(False)


class ImageVolume(Picture):
    volume = models.ForeignKey(Volume, on_delete=models.CASCADE)

    def get_wit_ref(self):
        return f"vol{self.volume.id}"


# Receive the pre_delete signal and delete the file associated with the model instance
@receiver(pre_delete, sender=ImageVolume)
def imagevolume_delete(sender, instance, **kwargs):
    # Pass false so ImageField doesn't save the model
    # TODO use remove_digitization for all type of digit
    # unindex_witness(instance.get_wit_id(), get_wit_type(instance.get_wit_abbr()))
    instance.image.delete(False)


class ImageManuscript(Picture):
    manuscript = models.ForeignKey(Manuscript, on_delete=models.CASCADE)

    def get_wit_ref(self):
        return f"ms{self.manuscript.id}"


# Receive the pre_delete signal and delete the file associated with the model instance
@receiver(pre_delete, sender=ImageManuscript)
def imagemanuscript_delete(sender, instance, **kwargs):
    # Pass false so ImageField doesn't save the model
    # TODO use remove_digitization for all type of digit
    # unindex_witness(instance.get_wit_id(), get_wit_type(instance.get_wit_abbr()))
    instance.image.delete(False)


#############################
#            PDF            #
#############################


class Pdf(Digitization):
    class Meta:
        verbose_name = "PDF File"
        verbose_name_plural = "PDF Files"
        abstract = True  # TODO: make this class not abstract

    def __str__(self):
        return self.pdf.name

    def get_wit_id(self):
        return self.volume.id if "vol" in self.pdf.name else self.manuscript.id

    def get_wit_abbr(self):
        return VOL_ABBR if "vol" in self.pdf.name else MS_ABBR

    def save(self, *args, **kwargs):
        # Call the parent save method to save the model
        super().save(*args, **kwargs)
        # Run the PDF to image async conversion task in the background using threading
        # t = threading.Thread(target=self.to_img())

        event = threading.Event()

        t = threading.Thread(
            target=pdf_to_img,
            args=(
                event,
                f"{self.pdf.name}",
            ),
        )
        t.start()

        t2 = threading.Thread(
            target=send_anno_request,
            args=(
                event,
                f"{self.get_wit_id()}",
                f"{self.get_wit_abbr()}",
            ),
        )
        t2.start()

    def delete(self, using=None, keep_parents=False):
        t = threading.Thread(
            target=remove_digitization,
            args=(self.get_wit_id(), self.get_wit_abbr(), self.pdf.name),
        )
        t.start()
        super().delete()

    def get_path(self):
        return f"{BASE_DIR}/{MEDIA_PATH}/{self.pdf.name}"

    def get_filename(self):
        # e.g. self.pdf.name = "volumes/pdf/filename.pdf" => filename = "filename"
        return self.pdf.name.split("/")[-1].split(".")[0]

    def get_page_nb(self):
        import PyPDF2

        with open(self.get_path(), "rb") as pdf_file:
            pdf_reader = PyPDF2.PdfFileReader(pdf_file)
            page_nb = pdf_reader.getNumPages()
        return page_nb

    def to_img(self):
        """
        Convert the PDF file to JPEG images
        NOTE: it is not functioning and use apparently
        """
        filename = self.get_filename()
        page_nb = self.get_page_nb()
        step = 2
        try:
            for img_nb in range(1, page_nb + 1, step):
                batch_pages = convert_from_path(
                    self.get_path(),
                    dpi=300,
                    first_page=img_nb,
                    last_page=min(img_nb + step - 1, page_nb),
                )
                # Iterate through all the batch pages stored above
                for page in batch_pages:
                    page.save(
                        f"{BASE_DIR}/{IMG_PATH}/{filename}_{img_nb:04d}.jpg",
                        format="JPEG",
                    )
                    # Increment the counter to update filename
                    img_nb += 1
        except Exception as e:
            log(f"Failed to convert {filename}.pdf to images:\n{e}")


class PdfManuscript(Pdf):
    manuscript = models.ForeignKey(Manuscript, on_delete=models.CASCADE)
    pdf = models.FileField(
        verbose_name="PDF",
        upload_to=partial(rename_file, path=MS_PDF_PATH),
        validators=[FileExtensionValidator(allowed_extensions=["pdf"])],
    )

    def get_wit_ref(self):
        return f"ms{self.manuscript.id}"


class PdfVolume(Pdf):
    volume = models.ForeignKey(Volume, on_delete=models.CASCADE)
    pdf = models.FileField(
        verbose_name="PDF",
        upload_to=partial(rename_file, path=VOL_PDF_PATH),
        validators=[FileExtensionValidator(allowed_extensions=["pdf"])],
    )

    def get_wit_ref(self):
        return f"vol{self.volume.id}"


############################
#         MANIFEST         #
############################


class Manifest(Digitization):
    class Meta:
        verbose_name = "IIIF manifest"
        verbose_name_plural = "IIIF manifests"
        abstract = True  # TODO: make this class not abstract

    manifest = models.URLField(
        verbose_name=MANIFEST,
        help_text=MANIFEST_INFO,
        validators=[validate_manifest],
    )

    def __str__(self):
        return self.manifest


def save_manifest(instance, wit_id, wit_abbr):
    event = threading.Event()

    # Run the async extraction of images from an IIIF manifest in the background using threading
    t = threading.Thread(
        target=extract_images_from_iiif_manifest,
        args=(
            instance.manifest,
            f"{wit_abbr}{wit_id}",
            event,
        ),
    )
    t.start()

    t2 = threading.Thread(
        target=send_anno_request,
        args=(event, wit_id, wit_abbr),
    )
    t2.start()


class ManifestVolume(Manifest):
    volume = models.ForeignKey(Volume, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        # Call the parent save method to save the model
        super().save(*args, **kwargs)
        save_manifest(self, self.volume.id, VOL_ABBR)

    def get_wit_ref(self):
        return f"vol{self.volume.id}"


class ManifestManuscript(Manifest):
    manuscript = models.ForeignKey(Manuscript, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        # Call the parent save method to save the model
        super().save(*args, **kwargs)
        save_manifest(self, self.manuscript.id, MS_ABBR)

    def get_wit_ref(self):
        return f"ms{self.manuscript.id}"
