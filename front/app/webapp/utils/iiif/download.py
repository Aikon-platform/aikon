from app.webapp.utils.paths import IMG_PATH


def iiif_to_img(manifest_url, digit_ref, digit):
    """
    Extract all images from an IIIF manifest
    """
    from iiif_download import IIIFManifest

    # TODO change config of log fails + do not create img/ folder

    manifest = IIIFManifest(manifest_url, prefix=f"{digit_ref}_")
    manifest.download(save_dir=IMG_PATH)
    digit.add_info(manifest.license)
    return [img.img_path for img in manifest.images]
