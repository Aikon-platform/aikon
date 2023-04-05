import threading
from uuid import uuid4

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
    MS,
    VOL,
)
from vhsapp.utils.functions import (
    convert_to_jpeg,
)
from vhsapp.utils.paths import (
    BASE_DIR,
    IMG_PATH,
    MS_PDF_PATH,
    VOL_PDF_PATH,
    MEDIA_PATH,
)

from vhsapp.utils.iiif import (
    parse_manifest,
    validate_manifest,
    extract_images_from_iiif_manifest,
)

from vhsapp.models.witness import Volume, Manuscript


class Digitization(models.Model):
    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.witness = None
        self.wit_type = "witness"
        self.digit_type = "digit"
        self.ext = "ext"

    @property
    def witness(self):
        return self.witness

    @witness.setter
    def witness(self, witness):
        self.witness = witness

    @property
    def wit_type(self):
        return self.witness

    @wit_type.setter
    def wit_type(self, wit_type):
        self.wit_type = wit_type

    @property
    def digit_type(self):
        return self.digit_type

    @digit_type.setter
    def digit_type(self, digit_type):
        self.digit_type = digit_type

    @property
    def ext(self):
        return self.ext

    @ext.setter
    def ext(self, extension):
        self.ext = extension

    def get_wit_abbr(self):
        return VOL_ABBR if self.wit_type == VOL else MS_ABBR

    def get_wit_id(self):
        if self.witness is None:
            return 0
        return self.witness.id

    def get_wit_ref(self):
        return f"{self.wit_type}{self.get_wit_id()}"

    def get_filename(self):
        try:
            return f"{self.get_wit_ref()}_{self.digit_type}{self.id}"
        except Exception:
            return None

    def get_path(self):
        return f"{BASE_DIR}/{MEDIA_PATH}"

    def get_filepath(self):
        return f"{self.get_path()}/{self.get_filename()}.{self.ext}"


def rename_file(instance: Digitization, original_filename):
    """
    Rename the file using its witness id and specific id
    The file will be uploaded to "{path}/{filename}.{ext}"
    """
    instance.ext = original_filename.split(".")[-1]
    new_filename = instance.get_filename()
    if new_filename is None:
        # Set filename as random string
        new_filename = f"{uuid4().hex}.{instance.ext}"
    # Return the path to the file
    return f"{instance.get_path()}/{new_filename}.{instance.ext}"


#############################
#           IMG             #
#############################


class Picture(Digitization):
    class Meta:
        verbose_name = "Image file"
        verbose_name_plural = "Images files"
        abstract = True  # TODO: make this class not abstract

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.digit_type = "img"
        self.image = models.ImageField(
            verbose_name="Image",
            upload_to=partial(rename_file),
            validators=[
                FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "tif"])
            ],
            help_text=IMG_INFO,
        )

    def __str__(self):
        return self.image.name

    def save(self, *args, **kwargs):
        if self.image:
            img = Image.open(self.image)
            # Check if the image format is not JPEG
            if img.format != "JPEG":
                # Convert the image to JPEG format
                self.image = convert_to_jpeg(self.image)
        # Call the parent save method to save the model
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        super().delete()


# Receive the pre_delete signal and delete the file associated with the model instance
@receiver(pre_delete, sender=Picture)
def image_delete(sender, instance, **kwargs):
    # Pass false so ImageField doesn't save the model
    instance.image.delete(False)


class ImageVolume(Picture):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wit_type = VOL
        self.witness = models.ForeignKey(Volume, on_delete=models.CASCADE)


# Receive the pre_delete signal and delete the file associated with the model instance
@receiver(pre_delete, sender=ImageVolume)
def imagevolume_delete(sender, instance, **kwargs):
    # Pass false so ImageField doesn't save the model
    instance.image.delete(False)


class ImageManuscript(Picture):
    witness = models.ForeignKey(Manuscript, on_delete=models.CASCADE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wit_type = MS
        self.witness = models.ForeignKey(Manuscript, on_delete=models.CASCADE)


# Receive the pre_delete signal and delete the file associated with the model instance
@receiver(pre_delete, sender=ImageManuscript)
def imagemanuscript_delete(sender, instance, **kwargs):
    # Pass false so ImageField doesn't save the model
    instance.image.delete(False)


#############################
#            PDF            #
#############################


class Pdf(Digitization):
    class Meta:
        verbose_name = "PDF File"
        verbose_name_plural = "PDF Files"
        abstract = True  # TODO: make this class not abstract

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.digit_type = "pdf"
        self.pdf = models.FileField(
            verbose_name="PDF",
            upload_to=partial(rename_file),
            validators=[FileExtensionValidator(allowed_extensions=["pdf"])],
        )

    def __str__(self):
        return self.pdf.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Run the PDF to image async conversion task in the background using threading
        t = threading.Thread(target=self.to_img())
        t.start()

    def delete(self, using=None, keep_parents=False):
        self.pdf.storage.delete(self.pdf.name)
        # TODO delete images extracted from the pdf
        super().delete()

    def get_page_nb(self):
        import PyPDF2

        with open(self.get_path(), "rb") as pdf_file:
            pdf_reader = PyPDF2.PdfFileReader(pdf_file)
            page_nb = pdf_reader.getNumPages()
        return page_nb

    def to_img(self):
        """
        Convert the PDF file to JPEG images
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.witness = models.ForeignKey(Manuscript, on_delete=models.CASCADE)
        self.wit_type = MS

    def get_path(self):
        return f"{BASE_DIR}/{MEDIA_PATH}/{MS_PDF_PATH}"


class PdfVolume(Pdf):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.witness = models.ForeignKey(Volume, on_delete=models.CASCADE)
        self.wit_type = VOL

    def get_path(self):
        return f"{BASE_DIR}/{MEDIA_PATH}/{VOL_PDF_PATH}"


############################
#         MANIFEST         #
############################


class Manifest(Digitization):
    class Meta:
        verbose_name = "IIIF manifest"
        verbose_name_plural = "IIIF manifests"
        abstract = True  # TODO: make this class not abstract

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.digit_type = "manifest"
        self.manifest = models.URLField(
            verbose_name=MANIFEST,
            help_text=MANIFEST_INFO,
            validators=[validate_manifest],
        )

    def __str__(self):
        return self.manifest

    # TODO: make a common save method for manifests
    def save(self, *args, **kwargs):
        # Call the parent save method to save the model
        super().save(*args, **kwargs)
        # Run the async extraction of images from an IIIF manifest in the background using threading
        t = threading.Thread(
            target=extract_images_from_iiif_manifest,
            args=(
                self.manifest,
                f"{IMG_PATH}",
                f"{self.get_wit_abbr()}{self.get_wit_id()}",
            ),
        )
        t.start()


class ManifestVolume(Manifest):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.witness = models.ForeignKey(Volume, on_delete=models.CASCADE)
        self.wit_type = VOL


class ManifestManuscript(Manifest):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.witness = models.ForeignKey(Manuscript, on_delete=models.CASCADE)
        self.wit_type = MS
