from vhsapp.utils.logger import iiif_log, console, log


IIIF_ICON = "<img alt='IIIF' src='https://iiif.io/assets/images/logos/logo-sm.png' height='15'/>"


def get_id(dic):
    if type(dic) == list:
        dic = dic[0]

    if type(dic) == dict:
        try:
            return dic["@id"]
        except KeyError:
            try:
                return dic["id"]
            except KeyError as e:
                log(f"[Get id] No id provided {e}")

    if type(dic) == str:
        return dic

    return None


def get_img_rsrc(iiif_img):
    try:
        img_rscr = iiif_img["resource"]
    except KeyError:
        try:
            img_rscr = iiif_img["body"]
        except KeyError:
            return None
    return img_rscr


def get_height(img_rsrc):
    try:
        img_height = img_rsrc["height"]
    except KeyError:
        return None
    return img_height


def get_width(img_rsrc):
    try:
        img_width = img_rsrc["width"]
    except KeyError:
        return None
    return img_width


# NOT USED
def get_canvas_img(canvas_img, only_img_url=False):
    img_url = get_id(canvas_img["resource"]["service"])
    if only_img_url:
        return img_url
    return get_img_id(canvas_img["resource"]), img_url


# NOT USED
def get_item_img(item_img, only_img_url=False):
    img_url = get_id(item_img["body"]["service"][0])
    if only_img_url:
        return img_url
    return get_img_id(item_img), img_url


# NOT USED
def get_img_id(img):
    img_id = get_id(img)
    if ".jpg" in img_id:
        try:
            return img_id.split("/")[-5]
        except IndexError:
            return None
        # return Path(urlparse(img_id).path).parts[-5]
    return img_id.split("/")[-1]


def get_formatted_size(width="", height=""):
    if not width and not height:
        return "full"
    return f"{width or ''},{height or ''}"


def get_iiif_resources(manifest, only_img_url=False):
    try:
        img_list = [canvas["images"] for canvas in manifest["sequences"][0]["canvases"]]
        # img_info = [get_canvas_img(img, only_img_url) for imgs in img_list for img in imgs]
        img_info = [get_img_rsrc(img) for imgs in img_list for img in imgs]
    except KeyError:
        try:
            img_list = [
                item
                for items in manifest["items"]
                for item in items["items"][0]["items"]
            ]
            # img_info = [get_item_img(img, only_img_url) for img in img_list]
            img_info = [get_img_rsrc(img) for img in img_list]
        except KeyError as e:
            log(
                f"[get_iiif_resources] Unable to retrieve resources from manifest {manifest}\n{e}"
            )
            return []

    return img_info
