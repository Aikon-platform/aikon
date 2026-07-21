from app.webapp.utils.paths import IMG_PATH


def iiif_to_img(manifest_url, digit_ref, digit):
    from iiif_download import IIIFManifest

    manifest = IIIFManifest(manifest_url, prefix=f"{digit_ref}_")
    manifest.download(save_dir=IMG_PATH)
    if manifest.content is None:
        raise RuntimeError(f"manifest fetch failed: {manifest_url}")
    digit.add_info(manifest.license)
    return [
        {"name": img.img_path, "h": img.height, "w": img.width}
        for img in manifest.images
    ]
