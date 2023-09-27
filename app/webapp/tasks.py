from celery import shared_task


@shared_task
def convert_pdf_to_imgs(pdf_path, img_path):
    # TODO: pdf_to_images_conversion
    pass


@shared_task
def extract_imgs_from_manifest(url, img_path, work):
    # TODO: manifest_image_extraction
    pass


@shared_task
def search_similarity(exp_path, work):
    # TODO: similarity_search
    pass
