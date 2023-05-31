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
    WIT,
)
from vhsapp.utils.functions import convert_to_jpeg, get_last_file
from vhsapp.utils.paths import (
    BASE_DIR,
    IMG_PATH,
    MS_PDF_PATH,
    VOL_PDF_PATH,
    MEDIA_DIR,
    IMG_DIR,
)

from vhsapp.utils.iiif import (
    parse_manifest,
    validate_manifest,
    extract_images_from_iiif_manifest,
)

from vhsapp.models.witness import Volume, Manuscript


# TODO make import work, make deletion work, make the link between witness and its digitizitaion work


class Digitization(models.Model):
    class Meta:
        abstract = True

    # TODO: make this reference the Witness class
    # witness = None  # models.ForeignKey(Witness, on_delete=models.CASCADE)
    wit_type = WIT  # TODO remove to use self.witness.type
    digit_type = "digit"

    def __init__(self, nb=None, ext=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.nb = nb
        self.ext = ext

    def get_witness(self):
        try:
            return self.witness
        except AttributeError:
            return None

    def get_wit_type(self):
        witness = self.get_witness()
        if witness is None:
            return self.wit_type
        return witness.type

    def get_digit_type(self):
        return self.digit_type

    def set_ext(self, extension):
        self.ext = extension

    def get_nb(self):
        if self.get_digit_type() != "img":
            return ""
        if self.nb is None:
            self.set_nb(
                get_last_file(self.get_absolute_path(), f"{self.get_wit_ref()}_") + 1
            )
        return f"_{self.nb:04d}"

    def set_nb(self, nb):
        self.nb = nb

    def get_wit_abbr(self):
        return VOL_ABBR if self.wit_type == VOL else MS_ABBR

    def get_wit_id(self):
        witness = self.get_witness()
        if witness is None:
            return 0
        return witness.id

    def get_wit_ref(self):
        return f"{self.get_wit_abbr()}{self.get_wit_id()}"

    def get_filename(self):
        """
        Returns filename without extension
        """
        try:
            return f"{self.get_wit_ref()}{self.get_nb()}"
        except Exception:
            return None

    def get_relative_path(self):
        # must be relative to MEDIA_DIR
        return ""

    def get_absolute_path(self):
        return f"{BASE_DIR}/{MEDIA_DIR}/{self.get_relative_path()}"

    def get_file_path(self, is_abs=True):
        path = self.get_absolute_path() if is_abs else self.get_relative_path()
        return f"{path}/{self.get_filename()}.{self.ext}"


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
    return f"{instance.get_relative_path()}/{new_filename}.{instance.ext}"


#############################
#           IMG             #
#############################


class Picture(Digitization):
    class Meta:
        verbose_name = "Image file"
        verbose_name_plural = "Images files"
        abstract = True  # TODO: make this class not abstract

    digit_type = "img"
    image = models.ImageField(
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

    def get_relative_path(self):
        return IMG_DIR


# Receive the pre_delete signal and delete the file associated with the model instance
@receiver(pre_delete, sender=Picture)
def imagewitness_delete(sender, instance, **kwargs):
    # Pass false so ImageField doesn't save the model
    instance.image.delete(False)


class ImageVolume(Picture):
    wit_type = VOL
    witness = models.ForeignKey(Volume, on_delete=models.CASCADE)


# Receive the pre_delete signal and delete the file associated with the model instance
@receiver(pre_delete, sender=ImageVolume)
def imagevolume_delete(sender, instance, **kwargs):
    # Pass false so ImageField doesn't save the model
    instance.image.delete(False)


class ImageManuscript(Picture):
    wit_type = MS
    witness = models.ForeignKey(
        Manuscript, on_delete=models.CASCADE, related_name="images"
    )


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

    digit_type = "pdf"
    pdf = models.FileField(
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
        self.pdf.storage.delete(self.get_file_path(False))
        # TODO delete images extracted from the pdf
        super().delete()

    def get_page_nb(self):
        import PyPDF2

        with open(self.get_file_path(), "rb") as pdf_file:
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
                    self.get_file_path(),
                    dpi=300,
                    first_page=img_nb,
                    last_page=min(img_nb + step - 1, page_nb),
                )
                # Iterate through all the batch pages stored above
                for page in batch_pages:
                    page.save(
                        f"{BASE_DIR}/{MEDIA_DIR}/{IMG_DIR}/{filename}_{img_nb:04d}.jpg",
                        format="JPEG",
                    )
                    # Increment the counter to update filename
                    img_nb += 1
        except Exception as e:
            log(f"Failed to convert {filename}.pdf to images:\n{e}")


class PdfManuscript(Pdf):
    witness = models.ForeignKey(Manuscript, on_delete=models.CASCADE)
    wit_type = MS

    def get_relative_path(self):
        return MS_PDF_PATH


class PdfVolume(Pdf):
    witness = models.ForeignKey(Volume, on_delete=models.CASCADE)
    wit_type = VOL

    def get_relative_path(self):
        return VOL_PDF_PATH


############################
#         MANIFEST         #
############################


class Manifest(Digitization):
    class Meta:
        verbose_name = "IIIF manifest"
        verbose_name_plural = "IIIF manifests"
        abstract = True  # TODO: make this class not abstract

    digit_type = "manifest"
    manifest = models.URLField(
        verbose_name=MANIFEST,
        help_text=MANIFEST_INFO,
        validators=[validate_manifest],
    )

    def __str__(self):
        return self.manifest

    def save(self, *args, **kwargs):
        # Call the parent save method to save the model
        super().save(*args, **kwargs)
        # Run the async extraction of images from an IIIF manifest in the background using threading
        t = threading.Thread(
            target=extract_images_from_iiif_manifest,
            args=(
                self.manifest,
                f"{IMG_PATH}",  # TODO here do we need an absolute path?
                f"{self.get_wit_abbr()}{self.get_wit_id()}",
            ),
        )
        t.start()


class ManifestVolume(Manifest):
    witness = models.ForeignKey(Volume, on_delete=models.CASCADE)
    wit_type = VOL


class ManifestManuscript(Manifest):
    witness = models.ForeignKey(Manuscript, on_delete=models.CASCADE)
    wit_type = MS


# import threading
# from PIL import Image
# from functools import partial
#
# from django.core.validators import FileExtensionValidator
# from django.db import models
# from django.db.models.signals import pre_delete
# from django.dispatch.dispatcher import receiver
# from pdf2image import convert_from_path
#
# from vhsapp.utils.logger import log, console
#
# from vhsapp.models.constants import (
#     MANIFEST,
#     MS_ABBR,
#     VOL_ABBR,
#     IMG_INFO,
#     MANIFEST_INFO,
# )
# from vhsapp.utils.functions import rename_file, convert_to_jpeg, pdf_to_img
# from vhsapp.utils.paths import (
#     BASE_DIR,
#     IMG_PATH,
#     MS_PDF_PATH,
#     VOL_PDF_PATH,
#     MEDIA_PATH,
# )
#
# from vhsapp.utils.iiif.iiif_validation import (
#     parse_manifest,
#     validate_manifest,
# )
#
# from vhsapp.utils.iiif.iiif_extraction import (
#     extract_images_from_iiif_manifest,
# )
#
# from vhsapp.models.witness import Volume, Manuscript
#
#
# class Digitization(models.Model):
#     # TODO link this class to a unique
#     # source = models.ForeignKey(
#     #     Witness, verbose_name=WITNESS, on_delete=models.SET_NULL, null=True
#     # )
#
#     class Meta:
#         abstract = True
#
#
# #############################
# #           IMG           #
# #############################
#
#
# class Picture(Digitization):
#     class Meta:
#         verbose_name = "Image file"
#         verbose_name_plural = "Images files"
#         abstract = True  # TODO: make this class not abstract
#
#     def __str__(self):
#         return self.image.name
#
#     image = models.ImageField(
#         verbose_name="Image",
#         upload_to=partial(rename_file, path=IMG_PATH),
#         validators=[
#             FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "tif"])
#         ],
#         help_text=IMG_INFO,
#     )
#
#     def save(self, *args, **kwargs):
#         if self.image:
#             img = Image.open(self.image)
#             # Check if the image format is not JPEG
#             if img.format != "JPEG":
#                 # Convert the image to JPEG format
#                 self.image = convert_to_jpeg(self.image)
#         # Call the parent save method to save the model
#         super().save(*args, **kwargs)
#
#     def delete(self, using=None, keep_parents=False):
#         super().delete()
#
#
# # Receive the pre_delete signal and delete the file associated with the model instance
# @receiver(pre_delete, sender=Picture)
# def image_delete(sender, instance, **kwargs):
#     # Pass false so ImageField doesn't save the model
#     instance.image.delete(False)
#
#
# class ImageVolume(Picture):
#     volume = models.ForeignKey(Volume, on_delete=models.CASCADE)
#
#     def get_wit_ref(self):
#         return f"vol{self.volume.id}"
#
#
# # Receive the pre_delete signal and delete the file associated with the model instance
# @receiver(pre_delete, sender=ImageVolume)
# def imagevolume_delete(sender, instance, **kwargs):
#     # Pass false so ImageField doesn't save the model
#     instance.image.delete(False)
#
#
# class ImageManuscript(Picture):
#     manuscript = models.ForeignKey(Manuscript, on_delete=models.CASCADE)
#
#     def get_wit_ref(self):
#         return f"ms{self.manuscript.id}"
#
#
# # Receive the pre_delete signal and delete the file associated with the model instance
# @receiver(pre_delete, sender=ImageManuscript)
# def imagemanuscript_delete(sender, instance, **kwargs):
#     # Pass false so ImageField doesn't save the model
#     instance.image.delete(False)
#
#
# #############################
# #            PDF            #
# #############################
#
#
# class Pdf(Digitization):
#     class Meta:
#         verbose_name = "PDF File"
#         verbose_name_plural = "PDF Files"
#         abstract = True  # TODO: make this class not abstract
#
#     def __str__(self):
#         return self.pdf.name
#
#     def save(self, *args, **kwargs):
#         # Call the parent save method to save the model
#         super().save(*args, **kwargs)
#         # Run the PDF to image async conversion task in the background using threading
#         # t = threading.Thread(target=self.to_img())
#         t = threading.Thread(target=pdf_to_img, args=(f"{self.pdf.name}",))
#         t.start()
#
#     def delete(self, using=None, keep_parents=False):
#         self.pdf.storage.delete(self.pdf.name)
#         # TODO delete images extracted from the pdf
#         super().delete()
#
#     def get_path(self):
#         return f"{BASE_DIR}/{MEDIA_PATH}/{self.pdf.name}"
#
#     def get_filename(self):
#         # e.g. self.pdf.name = "volumes/pdf/filename.pdf" => filename = "filename"
#         return self.pdf.name.split("/")[-1].split(".")[0]
#
#     def get_page_nb(self):
#         import PyPDF2
#
#         with open(self.get_path(), "rb") as pdf_file:
#             pdf_reader = PyPDF2.PdfFileReader(pdf_file)
#             page_nb = pdf_reader.getNumPages()
#         return page_nb
#
#     def to_img(self):
#         """
#         Convert the PDF file to JPEG images
#         """
#         filename = self.get_filename()
#         page_nb = self.get_page_nb()
#         step = 2
#         try:
#             for img_nb in range(1, page_nb + 1, step):
#                 batch_pages = convert_from_path(
#                     self.get_path(),
#                     dpi=300,
#                     first_page=img_nb,
#                     last_page=min(img_nb + step - 1, page_nb),
#                 )
#                 # Iterate through all the batch pages stored above
#                 for page in batch_pages:
#                     page.save(
#                         f"{BASE_DIR}/{IMG_PATH}/{filename}_{img_nb:04d}.jpg",
#                         format="JPEG",
#                     )
#                     # Increment the counter to update filename
#                     img_nb += 1
#         except Exception as e:
#             log(f"Failed to convert {filename}.pdf to images:\n{e}")
#
#
# class PdfManuscript(Pdf):
#     manuscript = models.ForeignKey(Manuscript, on_delete=models.CASCADE)
#     pdf = models.FileField(
#         verbose_name="PDF",
#         upload_to=partial(rename_file, path=MS_PDF_PATH),
#         validators=[FileExtensionValidator(allowed_extensions=["pdf"])],
#     )
#
#     def get_wit_ref(self):
#         return f"ms{self.manuscript.id}"
#
#
# class PdfVolume(Pdf):
#     volume = models.ForeignKey(Volume, on_delete=models.CASCADE)
#     pdf = models.FileField(
#         verbose_name="PDF",
#         upload_to=partial(rename_file, path=VOL_PDF_PATH),
#         validators=[FileExtensionValidator(allowed_extensions=["pdf"])],
#     )
#
#     def get_wit_ref(self):
#         return f"vol{self.volume.id}"
#
#
# ############################
# #         MANIFEST         #
# ############################
#
#
# class Manifest(Digitization):
#     class Meta:
#         verbose_name = "IIIF manifest"
#         verbose_name_plural = "IIIF manifests"
#         abstract = True  # TODO: make this class not abstract
#
#     manifest = models.URLField(
#         verbose_name=MANIFEST,
#         help_text=MANIFEST_INFO,
#         validators=[validate_manifest],
#     )
#
#     def __str__(self):
#         return self.manifest
#
#     # TODO: make a common save method for manifests
#     # def save(self, *args, **kwargs):
#     #     # Call the parent save method to save the model
#     #     super().save(*args, **kwargs)
#     #     # Run the async extraction of images from an IIIF manifest in the background using threading
#     #     t = threading.Thread(
#     #         target=extract_images_from_iiif_manifest,
#     #         args=(
#     #             self.manifest,
#     #             f"{SRC_ABBR}{self.source.id}",
#     #         ),
#     #     )
#     #     t.start()
#
#
# class ManifestVolume(Manifest):
#     volume = models.ForeignKey(Volume, on_delete=models.CASCADE)
#
#     def save(self, *args, **kwargs):
#         # Call the parent save method to save the model
#         super().save(*args, **kwargs)
#         # Run the async extraction of images from an IIIF manifest in the background using threading
#         t = threading.Thread(
#             target=extract_images_from_iiif_manifest,
#             args=(
#                 self.manifest,
#                 f"{VOL_ABBR}{self.volume.id}",
#             ),
#         )
#         t.start()
#
#     def get_wit_ref(self):
#         return f"vol{self.volume.id}"
#
#
# class ManifestManuscript(Manifest):
#     manuscript = models.ForeignKey(Manuscript, on_delete=models.CASCADE)
#
#     def save(self, *args, **kwargs):
#         # Call the parent save method to save the model
#         super().save(*args, **kwargs)
#         # Run the async extraction of images from an IIIF manifest in the background using threading
#         t = threading.Thread(
#             target=extract_images_from_iiif_manifest,
#             args=(
#                 self.manifest,
#                 f"{MS_ABBR}{self.manuscript.id}",
#             ),
#         )
#         t.start()
#
#     def get_wit_ref(self):
#         return f"ms{self.manuscript.id}"
