import colorsys
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from typing import List, Dict, Any, Tuple

from django.db.models import Q
import requests
from PIL import Image

from app.webapp.models.regions import Regions, get_name
from app.webapp.models.digitization import Digitization
from app.webapp.models.witness import Witness

from app.config.settings import (
    CANTALOUPE_APP_URL,
    AIIINOTATE_BASE_URL,
    APP_NAME,
    APP_URL,
)
from app.webapp.utils.functions import log, get_img_nb_len, gen_img_ref
from app.webapp.utils.iiif import parse_ref, gen_iiif_url, region_title
from app.webapp.utils.paths import REGIONS_PATH, IMG_PATH
from app.webapp.utils.regions import get_file_regions

IIIF_CONTEXT = "http://iiif.io/api/presentation/2/context.json"
IIIF_SEARCH_VERSION = 1
IIIF_PRESENTATION_VERSION = 2


# ********************************************
# UTILS


def update_params(urlstr: str, q_params: Dict) -> str:
    """
    update the url string `urlstr` with the dictionnary of query parameters `q_str` and return the updated url string.
    https://coderivers.org/blog/python-url-replace/
    """
    url = urlparse(urlstr)
    url_q_params = parse_qs(url.query)
    for k, v in q_params.items():
        url_q_params[k] = v
    url_q_params = urlencode(url_q_params, doseq=True)
    url = url._replace(query=url_q_params)
    return urlunparse(url)


def to_annotation_url(id_short_manifest: str, id_short_annotation: str) -> str:
    """build an URL to an annotation based on its short ID (the unique part of the URL string)"""
    return f"{AIIINOTATE_BASE_URL}/data/{IIIF_PRESENTATION_VERSION}/{id_short_manifest}/annotation/{id_short_annotation}"


def format_canvas_annotations(regions: Regions, canvas_nb):
    canvas_annotations = get_annotations_per_canvas(
        regions, specific_canvas=str(canvas_nb)
    )
    if len(canvas_annotations) == 0:
        return {"@type": "sc:AnnotationList", "resources": []}

    return {
        "@type": "sc:AnnotationList",
        "resources": [
            format_annotation(
                regions,
                canvas_nb,
                canvas_annotations[annotation_num],
            )
            for annotation_num in range(len(canvas_annotations))
        ],
    }


def string_to_color(s: str, saturation=0.9, lightness=0.5) -> str:
    """Generate a deterministic hex color from a string."""
    hash_int = int(hashlib.md5(s.encode()).hexdigest(), 16)
    hue = (hash_int % 360) / 360.0

    r, g, b = colorsys.hls_to_rgb(hue, lightness, saturation)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


def format_annotation(regions: Regions, canvas_nb, xywh, tags=None):
    # regions.get_manifest_url returns digitization manifest
    base_url = regions.get_manifest_url(only_base=True)
    x, y, w, h = xywh

    annotation_id = regions.gen_annotation_id(canvas_nb)
    canvas_id = f"{base_url}/canvas/c{canvas_nb}.json"
    xywh_str = f"xywh={x},{y},{w},{h}"

    if tags is None:
        tags = []
    # put in first position of tags the tag that would be the most fitted to be displayed in the UI
    # using a different bounding box color for each annotations sharing the same first tag
    # e.g. its extraction class (letter, illustration, etc.) or extraction model ("yolo_finetuned", "layout_model", etc.)
    if model := regions.model:
        tags = [model] if tags is None else tags + [model]
    tags.append(regions.get_ref())

    resources = [{"@type": "oa:Tag", "chars": tag} for tag in tags]

    # # SVG path data
    # width = w // 2
    # height = h // 2
    # d = f"M{x} {y} h {width} v 0 h {width} v {height} v {height} h -{width} h -{width} v -{height}Z"
    # r_id = f"rectangle_{annotation_id}"
    # Paper.js data
    # d_paper = json.dumps({
    #     "strokeWidth": 1,
    #     "rotation": 0,
    #     "annotation": None,
    #     "nonHoverStrokeColor": ["Color", 0, 1, 0],
    #     "editable": True,
    #     "deleteIcon": None,
    #     "rotationIcon": None,
    #     "group": None
    # }).replace('"', '&quot;')
    #
    # path = (
    #     f"<path xmlns='http://www.w3.org/2000/svg' "
    #     f"d='{d}' id='{r_id}' data-paper-data='{d_paper}' "
    #     f"fill-opacity='0' fill='{string_to_color(tags[0])}' fill-rule='nonzero' "
    #     f"stroke='{string_to_color(tags[0])}' stroke-width='1' stroke-linecap='butt' "
    #     f"stroke-linejoin='miter' stroke-miterlimit='10' "
    #     f"stroke-dashoffset='0' style='mix-blend-mode: normal'/>"
    # )
    # path = re.sub(r"\s+", " ", path).strip()

    return {
        "@id": f"{AIIINOTATE_BASE_URL.replace('https', 'http')}/annotations/{IIIF_PRESENTATION_VERSION}/{annotation_id}",
        "@type": "oa:Annotation",
        "dcterms:created": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "dcterms:modified": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "resource": resources,
        "on": [
            {
                "@id": f"{canvas_id}#{xywh_str}",
                "@type": "oa:SpecificResource",
                "within": {
                    "@id": f"{base_url}/manifest.json",
                    "@type": "sc:Manifest",
                },
                "selector": {
                    "@type": "oa:FragmentSelector",
                    "value": xywh_str,
                },
                # "item": {
                #     "@type": "oa:SvgSelector",
                #     "value": f'<svg xmlns="http://www.w3.org/2000/svg">{path}</svg>',
                # },
                "full": f"{base_url}/canvas/c{canvas_nb}.json",
            },
        ],
        "motivation": ["oa:commenting", "oa:tagging"],
        "@context": IIIF_CONTEXT,
    }


def split_ref(ref: str) -> Tuple[str, str | None]:
    """
    Parse a reference to extract digit_ref and optional regions tag.
    Returns (digit_ref, regions_ref or None)

    Examples:
        "wit1_man1_anno3" -> ("wit1_man1", "wit1_man1_anno3")
        "wit1_man1" -> ("wit1_man1", None)
    """
    if "_anno" in ref:
        digit_ref = ref.split("_anno")[0]
        return digit_ref, ref
    return ref, None


def filter_annotations_by_tag(annotations: List[Dict], tag: str) -> List[Dict]:
    """Filter annotations that contain the specified tag in their resources."""
    if not tag:
        return annotations

    filtered = []
    for anno in annotations:
        resources = anno.get("resource", [])
        if isinstance(resources, dict):
            resources = [resources]

        for res in resources:
            if res.get("@type") == "oa:Tag" and res.get("chars") == tag:
                filtered.append(anno)
                break

    return filtered


def get_annotation_tags(anno: Dict) -> List[str]:
    """Extract all tags from an annotation."""
    resources = anno.get("resource", [])
    if isinstance(resources, dict):
        resources = [resources]
    return [r.get("chars") for r in resources if r.get("@type") == "oa:Tag"]


def set_canvas(seq, canvas_nb, img_name, img):
    """
    Build the canvas and annotation for each image
    Called for each manifest (v2: corrected annotations) image when a witness is being indexed
    """
    try:
        h, w = int(img["height"]), int(img["width"])
    except TypeError:
        h, w = img.height, img.width
    except ValueError:
        h, w = 900, 600
    # Build the canvas
    canvas = seq.canvas(ident=f"c{canvas_nb}", label=f"Page {canvas_nb}")
    canvas.set_hw(h, w)

    # Build the image annotation
    annotation = canvas.annotation(ident=f"a{canvas_nb}")
    if re.match(r"https?://(.*?)/", img_name):
        # to build hybrid manifest referencing images from other IIIF repositories
        img = annotation.image(img_name, iiif=False)
        setattr(img, "format", "image/jpeg")
    else:
        img = annotation.image(ident=img_name, iiif=True)

    img.set_hw(h, w)


def get_coord_from_annotation(aiiinotation, as_str=False):
    try:
        # coord => "x,y,w,h"
        # since AIIINOTATE_STRICT_MODE is true, `xywh` will always be defined
        coord = aiiinotation["on"][0]["xywh"]
        # remove negative values if some of the coordinates exceed the image boundaries
        if as_str:
            return ",".join(["0" if num < 0 else str(num) for num in coord])
        return coord
    except Exception as e:
        log(
            f"[get_coord_from_annotation] Could not retrieve coord from aiiinotation",
            e,
        )
        return "0,0,0,0"


def get_id_from_annotation(aiiinotation):
    try:
        # annotation_id => "{wit_abbr}{wit_id}_{digit_abbr}{digit_id}_anno{regions_id}_c{canvas_nb}_{uuid4().hex[:8]}"
        return aiiinotation["@id"].split("/")[-1]
    except Exception as e:
        log(
            f"[get_id_from_annotation] Could not retrieve id from aiiinotation",
            e,
        )
        return ""


def iter_canvas_annotations(regions: Regions):
    """
    Generator yielding (canvas_nb, img_name, coords) for each canvas.
    coords is a list of (x, y, w, h) tuples.
    """
    data, anno_format = get_file_regions(regions)
    if not data:
        return

    digit = regions.get_digit()
    imgs = digit.get_imgs()

    if anno_format == "txt":
        current_img = None
        coords = []

        for line in data:
            parts = line.split()
            if len(parts) == 2:
                if current_img is not None:
                    canvas_nb = int(current_img.split("_")[-1].split(".")[0])
                    yield (canvas_nb, current_img, coords)
                _, current_img = parts
                coords = []
            elif len(parts) == 4:
                coords.append(tuple(map(int, parts)))

        if current_img is not None:
            canvas_nb = int(current_img.split("_")[-1].split(".")[0])
            yield (canvas_nb, current_img, coords)

    elif anno_format == "json":
        digit_ref = data[0]["doc_uid"] if data else ""

        for idx, annotation in enumerate(data):
            canvas_nb = idx + 1
            src = annotation["source"]

            img_name = None
            for variant in [
                src,
                src.replace("0", ""),
                src.replace("00", ""),
                src.replace("000", ""),
            ]:
                candidate = f"{digit_ref}_{variant}"
                if candidate in imgs:
                    img_name = candidate
                    break

            coords = [
                (
                    int(c["absolute"]["x1"]),
                    int(c["absolute"]["y1"]),
                    int(c["absolute"]["width"]),
                    int(c["absolute"]["height"]),
                )
                for c in annotation.get("crops", [])
            ]

            yield (canvas_nb, img_name, coords)


def get_annotations_per_canvas(region: Regions, last_canvas=0, specific_canvas=""):
    """
    Read task result files and build a dict with the text annotation file info:
    { "canvas1": [ coord1, coord2 ], "canvas2": [], "canvas3": [ coord1 ] }

    if specific_canvas, returns [ coord1, coord2 ]

    coord = (x, y, width, height)
    """
    to_include = (
        lambda canvas: int(canvas) > last_canvas or str(canvas) == specific_canvas
    )

    data, anno_format = get_file_regions(region)

    if data is None:
        log(f"[get_annotations_per_canvas] No annotation file for Regions #{region.id}")
        return {}

    annotated_canvases = {}

    for canvas_nb, _, coords in iter_canvas_annotations(region):
        canvas_str = str(canvas_nb)
        if to_include(canvas_str):
            annotated_canvases[canvas_str] = coords

    return (
        annotated_canvases.get(specific_canvas, [])
        if specific_canvas
        else annotated_canvases
    )


def formatted_annotations(
    regions: Regions,
) -> Tuple[List[str], List[Tuple[int, List[int | float], str]]]:
    """
    format all annotations for all canvases in a Regions extraction.

    Returns:
        annotation_ids: [ anno_id_1, anno_id_2, ... ]
        canvas_annotations: [
            (
                canvas_nb: int,  # position of canvas in the manifest
                coord_annotations: List[number],  # xywh bounding box of the annotation
                img_file: str  # name of image file
            )
        ]
    """
    canvas_annotations = []
    annotation_ids = []

    try:
        for canvas_nb, img_file in get_canvas_list(regions):
            c_annotations = get_indexed_canvas_annotations(regions, canvas_nb)
            coord_annotations = []

            if bool(c_annotations):
                coord_annotations = [
                    (
                        get_coord_from_annotation(sas_anno, as_str=True),
                        get_id_from_annotation(sas_anno),
                    )
                    for sas_anno in c_annotations
                ]
                annotation_ids.extend(
                    annotation_id for _, annotation_id in coord_annotations
                )

            canvas_annotations.append((canvas_nb, coord_annotations, img_file))
    except ValueError as e:
        log(
            f"[formatted_annotations] Error when generating automatic annotation list (probably no annotation file)",
            e,
        )

    return annotation_ids, canvas_annotations


def create_list_annotations(regions: Regions):
    # TODO mutualize
    _, all_regions = formatted_annotations(regions)
    all_crops = [
        (canvas_nb, coord, img_file)
        for canvas_nb, coord, img_file in all_regions
        if coord
    ]
    anno_refs = []
    for _, coord, img_file in all_crops:
        name = f"{img_file[:-4]}_{''.join(c[0] for c in coord)}"
        anno_refs.append(name)

    return anno_refs


# ********************************************
# GET


def get_and_parse(q_url: str) -> List | Dict | None:
    """
    GET the resources at `q_url` and return them as a List or Dict. if there's an error, return None.
    """
    try:
        r = requests.get(q_url)
        if r.status_code != 200:
            log(
                f"[get_and_parse] Failed to get data from aiiinotate for URL {q_url}: {r.status_code}"
            )
            return None
        try:
            return r.json()
        except requests.exceptions.JSONDecodeError as e:
            log(f"[get_and_parse] JSON decode error for {q_url}")
            log(r.text, exception=e)
            return None
    except requests.exceptions.RequestException as e:
        log(
            f"[get_and_parse] Failed to retrieve data for {q_url}",
            e,
        )
        return None
    except Exception as e:
        log(
            f"[get_and_parse] Failed to get and parse annotations for {q_url}",
            e,
        )
        return None


def get_paginated_annotations(q_url: str) -> List[Dict]:
    """
    fetch annotations paginated in several AnnotationLists and return them as an array of annotations.
    """
    next_page = q_url
    annotations = []

    while next_page:
        annotation_list = get_and_parse(next_page)  # should be IIIF 2 AnnotationList
        if not isinstance(annotation_list, dict):
            log(
                f"[get_paginated_annotations] annotation_list should be a Dict, got {type(annotation_list)}",
            )
            next_page = None  # avoid infinite loop
        else:
            annotations.extend(annotation_list.get("resources", []))
            next_page = annotation_list.get("next", None)

    return annotations


def get_manifest_annotations(
    ref, only_ids=True, min_c: int | None = None, max_c: int | None = None
):
    """
    Get annotations for a manifest, optionally filtered by regions tag.

    Args:
        ref: Either a digit_ref (wit1_man1) or regions_ref (wit1_man1_anno3).
             If regions_ref, results are filtered to only that extraction.
        only_ids: If True, only return annotation IDs. If False, return full annotation data.
        min_c: If provided, only return annotations for canvases with number >= min_c (1-indexed).
        max_c: If provided, only return annotations for canvases with number <= max_c (1-indexed).
    """
    digit_ref, regions_tag = split_ref(ref)

    # all annotations for a given digit_ref
    q_url = f"{AIIINOTATE_BASE_URL}/search-api/{IIIF_SEARCH_VERSION}/manifests/{digit_ref}/search"

    # JSONSchema used by aiiinotate explicitly requires booleans to be expressed as "true" or "false".
    # https://json-schema.org/understanding-json-schema/reference/boolean
    q_params: Dict[str, Any] = {"onlyIds": "true" if only_ids else "false"}

    # `canvasMin` and `canvasMax` are 0-indexed while `min_c` `max_c` are 1-indexed => convert to 0-indexed
    c_range = [min_c, max_c]
    for (i, c) in enumerate(c_range):
        try:
            c_range[i] = max(int(c) - 1, 0)  # pyright: ignore
        except:  # min_c / max_c not convertible to 0
            c_range[i] = None
    if isinstance(c_range[0], int):
        q_params["canvasMin"] = c_range[0]
        if isinstance(c_range[1], int) and c_range[1] >= c_range[0]:
            q_params["canvasMax"] = c_range[1]

    q_url = update_params(q_url, q_params)

    r = get_and_parse(q_url) if only_ids else get_paginated_annotations(q_url)
    # sanity check to preserve type consistency if there's been an error in `get_and_parse`
    if not isinstance(r, list):
        return []

    if regions_tag and not only_ids:
        # TODO filter by regions tag also for only ids
        r = filter_annotations_by_tag(r, regions_tag)

    return r


def get_canvas_list(regions: Regions, all_img=False):
    """
    Get the list of canvases that have been annotated associated with their images names
    [
        (canvas_nb, img_name.jpg),
        (canvas_nb, img_name.jpg),
        ...
    ]
    """
    digit = regions.get_digit()
    imgs = digit.get_imgs()

    if all_img:
        return [(int(img.split("_")[-1].split(".")[0]), img) for img in imgs]

    canvases = []

    indexed_annos = get_manifest_annotations(regions.get_ref(), only_ids=False)
    canvas_imgs = {int(i.split("_")[-1].split(".")[0]): i for i in imgs}
    annotated_canvas_nb = {a["on"][0]["canvasIdx"] + 1 for a in indexed_annos}

    for canvas_nb in annotated_canvas_nb:
        if canvas_nb in canvas_imgs:
            canvases.append((canvas_nb, canvas_imgs[canvas_nb]))

    if canvases:
        return canvases

    for canvas_nb, img_name, _ in iter_canvas_annotations(regions):
        if img_name and img_name in imgs:
            canvases.append((canvas_nb, img_name))

    return canvases


# TODO create a get_digit_annotations / get_regions_annotations and check where to use one or the other
def get_regions_annotations(
    regions: Regions,
    as_json=False,
    r_annos=None,
    min_c: int | None = None,
    max_c: int | None = None,
):
    if r_annos is None:
        r_annos = {} if as_json else []

    digit = regions.get_digit()
    digit_meta = digit.get_json()
    regions_tag = regions.get_ref()

    img_name = digit.get_ref()
    nb_len = digit_meta.get("img_nb_len", get_img_nb_len(img_name))

    if as_json:
        min_c = min_c or 1
        max_c = max_c or digit_meta.get("img_nb")
        # { canvas_nb: {} }, canvas_nb is 1-indexed.
        r_annos = {str(c): {} for c in range(min_c, max_c + 1)}

    annos = get_manifest_annotations(digit.get_ref(), False, min_c, max_c)
    annos = filter_annotations_by_tag(annos, regions_tag)  # TODO filter or not

    if len(annos) == 0:
        return r_annos

    for anno in annos:
        try:
            on_value: List[Dict] = anno["on"][0]
            id_canvas = on_value["full"]
            canvas = id_canvas.split("/canvas/c")[1].split(".json")[0]

            if canvas not in r_annos:
                log(
                    f"[get_regions_annotations] Key '{canvas}' should be included between {min_c}-{max_c} => pass"
                )
                continue

            xywh = on_value["xywh"]
            if not xywh or not len(xywh):
                raise ValueError("Could not extract XYWH coordinates for annotation")
            xywh_str = ",".join(str(c) for c in xywh)

            if as_json:
                img = f"{img_name}_{canvas.zfill(nb_len)}"
                aid = anno["@id"].split("/")[-1]

                r_annos[canvas][aid] = {
                    "id": aid,
                    "ref": f"{img}_{xywh_str}",
                    "class": "Region",
                    "type": get_name("Regions"),
                    "title": region_title(canvas, xywh_str),
                    "url": gen_iiif_url(img, res=f"{xywh}/full/0"),
                    "canvas": canvas,
                    "xywh": xywh,
                    "img": img,
                }
            else:
                r_annos.append((canvas, xywh, f"{img_name}_{canvas.zfill(nb_len)}"))
        except Exception as e:
            log(f"[get_regions_annotations]: Failed to parse annotation {anno}", e)
            continue

    return r_annos


def get_annotations_on_canvases(regions: list[Regions], min_c, max_c):
    anno_regions = {}
    for reg in regions:
        max_canvas = reg.get_json()["img_nb"]
        anno_regions = get_regions_annotations(
            reg,
            as_json=True,
            r_annos=anno_regions,
            min_c=min_c or 1,
            max_c=min(max_c, max_canvas) if max_c else max_canvas,
        )
    return anno_regions


def get_indexed_manifests():
    try:
        r = get_and_parse(
            f"{AIIINOTATE_BASE_URL}/manifests/{IIIF_PRESENTATION_VERSION}"
        )
        manifests = r["members"]  # pyright: ignore
    except Exception as e:
        log(
            f"[get_indexed_manifests]: Failed to load indexed manifests in aiiinotate",
            e,
        )
        return False
    return [m["@id"] for m in manifests]


def get_indexed_canvas_annotations(regions: Regions, canvas_nb):
    canvas_url = f"{AIIINOTATE_BASE_URL}/annotations/{IIIF_PRESENTATION_VERSION}/search?canvasUri={regions.get_manifest_url(only_base=True)}/canvas/c{canvas_nb}.json"
    try:
        return get_and_parse(canvas_url)["resources"]  # pyright: ignore
    except Exception as e:
        log(
            f"[get_indexed_canvas_annotations] Could not retrieve annotation for {canvas_url}",
            e,
        )
        return []


def get_total_annotations(ref: str) -> int:
    """
    Count annotations for a ref (digit_ref or regions_ref).
    If regions_ref, only count annotations with that tag.
    """
    digit_ref, regions_tag = split_ref(ref)

    if regions_tag:
        # IF filter by regions, we have to get all annotations and filter them by tag
        # TODO make aiiinotate support tag filtering by tag
        annos = get_manifest_annotations(ref, only_ids=False)
        return len(annos)

    try:
        r = get_and_parse(
            f"{AIIINOTATE_BASE_URL}/annotations/{IIIF_PRESENTATION_VERSION}/count?manifestShortId={digit_ref}"
        )
        return r["count"]
    except Exception as e:
        log(f"[get_total_annotations]: Error for ref '{ref}'", e)
        return 0


def has_annotation(ref: str) -> bool:
    """
    Check if there are any annotations for the given regions reference.
    Returns True if at least one annotation is found, False otherwise.
    """
    return get_total_annotations(ref) > 0


def get_training_regions(regions: Regions):
    # Returns a list of tuples [(file_name, file_content), (...)]
    filenames_contents = []
    for canvas_nb, img_file in get_canvas_list(regions):
        aiiinotations = get_indexed_canvas_annotations(regions, canvas_nb)
        img = Image.open(f"{IMG_PATH}/{img_file}")
        width, height = img.size
        if bool(aiiinotations):
            train_regions = []
            for aiiinotation in aiiinotations:
                x, y, w, h = get_coord_from_annotation(aiiinotation)
                train_regions.append(
                    f"0 {((x + x + w) / 2) / width} {((y + y + h) / 2) / height} {w / width} {h / height}"
                )

            filenames_contents.append(
                (f"{img_file}".replace(".jpg", ".txt"), "\n".join(train_regions))
            )
    return filenames_contents


def get_regions_urls(regions: Regions):
    """
    {
        "wit1_man191_0009_166,1325,578,516": ""https://eida.obspm.fr/iiif/2/wit1_man191_0009.jpg/166,1325,578,516/full/0/default.jpg"",
        "wit1_man191_0027_1143,2063,269,245": "https://eida.obspm.fr/iiif/2/wit1_man191_0027.jpg/1143,2063,269,245/full/0/default.jpg",
        "wit1_man191_0031_857,2013,543,341": "https://eida.obspm.fr/iiif/2/wit1_man191_0031.jpg/857,2013,543,341/full/0/default.jpg",
        "img_name": "..."
    }
    """
    folio_regions = {}

    _, canvas_annotations = formatted_annotations(regions)

    for canvas_nb, annotations, img_name in canvas_annotations:
        if len(annotations):
            folio_regions.update(
                {
                    gen_img_ref(img_name, a[0]): gen_iiif_url(
                        img_name, 2, f"{a[0]}/full/0"
                    )
                    for a in annotations
                }
            )

    return folio_regions


def get_images_annotations(regions: Regions):
    """
    Get cantaloupe URLs for all regions in a Region extraction. Used to export images annotations
    """
    imgs = []

    try:
        for canvas_nb, img_file in get_canvas_list(regions):
            c_annotations = get_indexed_canvas_annotations(regions, canvas_nb)

            if bool(c_annotations):
                canvas_imgs = [
                    f"{CANTALOUPE_APP_URL}/iiif/2/{img_file}/{get_coord_from_annotation(aiiinotation, as_str=True)}/full/0/default.jpg"
                    for aiiinotation in c_annotations
                ]
                imgs.extend(canvas_imgs)
    except ValueError as e:
        log(f"[get_images_annotations] Error when retrieving aiiinotate annotations", e)

    return imgs


def check_indexation(regions: Regions, reindex=False):
    """
    Check if the number of generated annotations is the same as the number of indexed annotations
    If not, unindex all annotations and (if reindex=True) reindex the regions
    """
    data, anno_format = get_file_regions(regions)

    if not data:
        return False

    if not index_manifest(regions.get_manifest_url()):
        return False

    generated_annotations = 0
    indexed_annotations = 0
    aiiinotations_ids = []

    try:
        for canvas_nb, _, coords in iter_canvas_annotations(regions):
            aiiinotations = get_indexed_canvas_annotations(regions, str(canvas_nb))
            if aiiinotations:
                aiiinotations_ids.extend(
                    get_id_from_annotation(aiiinotation)
                    for aiiinotation in aiiinotations
                )
                indexed_annotations += len(aiiinotations)
            generated_annotations += len(coords)

    except Exception as e:
        log(
            f"[check_indexation] Failed to check indexation for regions #{regions.id}",
            e,
        )
        return False

    if generated_annotations != indexed_annotations:
        for aiiinotation_id in aiiinotations_ids:
            unindex_annotation(aiiinotation_id)
        if reindex:
            if index_regions(regions):
                log(f"[check_indexation] Regions #{regions.id} were reindexed")
                return True
    return True


# ********************************************
# CREATE


def index_regions(regions: Regions):
    # index the manifest
    if not index_manifest(regions.get_manifest_url(), True):
        return

    # fetch the annotations from the annotation file
    canvases_to_annotate: Dict[str, List[int | None]] = get_annotations_per_canvas(
        regions
    )  # pyright: ignore
    if not bool(canvases_to_annotate):
        # if the annotation file is empty
        return True

    for c in canvases_to_annotate:
        # only index canvases that have annotations
        if len(canvases_to_annotate[c]) > 0:
            try:
                index_annotations_on_canvas(regions, c)
            except Exception as e:
                log(
                    f"[index_regions] Problem indexing region #{regions.id} (canvas {c})",
                    e,
                )
    return True


def index_annotations_on_canvas(regions: Regions, canvas_nb):
    # this url (view canvas_annotations()) is calling format_canvas_annotations(),
    # thus returning formatted annotations for each canvas

    formatted_annos = (
        f"{APP_URL}/{APP_NAME}/iiif/{regions.get_ref()}/list/anno-{canvas_nb}.json"
    )
    # POST request that index the annotations
    response = requests.post(
        f"{AIIINOTATE_BASE_URL}/annotations/{IIIF_PRESENTATION_VERSION}/createMany",
        json={"uri": formatted_annos},
    )

    if not response.ok:
        log(
            f"[index_annotations_on_canvas] Failed to index annotations. Status: {response.status_code}",
            response.text,
        )
        return


def reindex_file(filename):
    """
    - if it is a new Regions extraction, create the Regions object and save it to database
    - index the Regions extraction into the annotation server
    """
    a_ref = filename.replace(".txt", "").replace(".json", "")
    ref = parse_ref(a_ref)
    if not ref or not ref["regions"]:
        # if there is no regions_id in the ref, pass
        return False, a_ref
    regions_id = ref["regions"][1]
    regions = Regions.objects.get(pk=regions_id)
    if not regions:
        digit = Digitization.objects.get(pk=ref["digit"][1])
        if not digit:
            # if there is no digit corresponding to the ref, pass
            return False, a_ref
        # create new Regions record if none existing
        regions = Regions(id=regions_id, digitization=digit, model="CHANGE THIS VALUE")
        regions.save()

    from app.webapp.tasks import reindex_from_file

    reindex_from_file.delay(regions_id)
    return True, a_ref


def index_manifest(manifest_url, reindex=False):
    if not reindex:
        manifests = get_indexed_manifests()
        if manifests and manifest_url in manifests:
            # if the manifest was already indexed
            return True

    try:
        manifest = requests.get(manifest_url)
        manifest_content = manifest.json()
    except Exception as e:
        log(
            f"[index_manifest]: Failed to load manifest for {manifest_url}",
            e,
        )
        return False

    try:
        # Index the manifest into aiiinotate
        r = requests.post(
            f"{AIIINOTATE_BASE_URL}/manifests/{IIIF_PRESENTATION_VERSION}/create",
            json=manifest_content,
        )
        if r.status_code != 200:
            log(
                f"[index_manifest]: Failed to index manifest {manifest_url}."
                f"Status code: {r.status_code}: {r.text}"
            )
            return False
    except Exception as e:
        log(
            f"[index_manifest]: Failed to index manifest {manifest_url} in aiiinotate",
            e,
        )
        return False
    return True


def process_regions(
    regions_file_content, digit, model="Unknown model", extension="json"
):
    """
    main function to write a regions extraction result to DB:
    - write task results sent from API to file
    - save Regions to database,
    - fetch all results and convert them to IIIF annotations,
    - index new regions and manifest in aiiinotate
    - update the witness with information on the Region.

    results are sent from the API inbatches, so this will be called several times per Regions extraction.
    """
    try:
        # TODO add step to check if regions weren't generated before for the same model
        regions, is_new = Regions.objects.get_or_create(digitization=digit, model=model)
    except Exception as e:
        log(
            f"[process_regions] Failed to create regions record for digit #{digit.id}",
            e,
        )
        return False

    anno_file = f"{REGIONS_PATH}/{regions.get_ref()}.{extension}"
    if not is_new and Path(anno_file).exists():
        # necessary check because regions are sent several times (once for PROGRESS event, then when SUCCESS event)
        log(
            f"[process_regions] Regions for Digit #{digit.id} already exists with same model, skipping",
        )
        return False

    try:
        with open(anno_file, "w") as f:
            if extension == "json":
                json.dump(regions_file_content, f)
            else:
                f.write(str(regions_file_content))
    except Exception as e:
        log(
            f"[process_regions] Failed to save received content file for digit #{digit.id}",
            e,
        )
        return False

    try:
        index_regions(regions)
    except Exception as e:
        log(f"[process_regions] Failed to index regions for digit #{digit.id}", e)
        return False

    try:
        witness = Witness.objects.get(pk=digit.witness_id)
        witness.set_json_regions()
    except Exception as e:
        log(e)
        log(f"[process_regions] Failed to update witness.json with up-to-date regions.")
        return False

    return True


# ********************************************
# DELETE


def unindex_annotation(annotation_id: str) -> bool:
    # annotation_id = f"{wit_abbr}{wit_id}_{digit_abbr}{digit_id}_anno{regions_id}_c{canvas_nb}_{uuid4().hex[:8]}
    annotation_url = to_annotation_url("", annotation_id).replace("https", "http")
    delete_url = f"{AIIINOTATE_BASE_URL}/annotations/{IIIF_PRESENTATION_VERSION}/delete?uri={annotation_url}"
    try:
        response = requests.delete(delete_url)
        if response.status_code in [200, 204]:
            return True
        else:
            log(
                f"[unindex_annotation] Unindex annotation request failed with status code: {response.status_code}"
            )
    except requests.exceptions.RequestException as e:
        log(f"[unindex_annotation] Unindex annotation request failed", e)
    return False


def unindex_manifest(manifest_url: str) -> bool:
    response = requests.delete(
        f"{AIIINOTATE_BASE_URL}/manifests/2/delete?uri={manifest_url}"
    )
    if response.status_code != 200:
        log(
            f"[unindex_manifest]: Failed to un-index manifest with URL {manifest_url}. "
            f"Status code: {response.status_code}. Error: {response.text}"
        )
        return False
    log(f"[unindex_manifest] unindexed manifest with ID {manifest_url}")
    return True


def unindex_annotations_by_tag(manifest_url: str, tag: str) -> int:
    """
    Delete annotations associated with a specific tag
    Returns count of deleted annotations.
    """
    # manifest_url = http://slug/digit_ref/manifest.json
    digit_ref = manifest_url.split("/")[-2]

    # Fetch all annotations, filter by tag, delete each one
    annos = get_manifest_annotations(digit_ref, only_ids=False)
    tagged_annos = filter_annotations_by_tag(annos, tag)

    deleted = 0
    for anno in tagged_annos:
        anno_id = get_id_from_annotation(anno)
        if anno_id and unindex_annotation(anno_id):
            deleted += 1

    log(
        f"[unindex_annotations_by_tag] Deleted {deleted}/{len(tagged_annos)} annotations with tag '{tag}'"
    )
    return deleted


def delete_manifest_annotations(manifest_url: str) -> bool:
    """delete all annotations of a manifest"""
    try:
        # manifest_url = http://slug/manifest_short_id/manifest.json
        manifest_short_id = manifest_url.split("/")[-2]
        url_delete = f"{AIIINOTATE_BASE_URL}/annotations/{IIIF_PRESENTATION_VERSION}/delete?manifestShortId={manifest_short_id}"
        r = requests.delete(url_delete)
        if r.status_code not in [200, 204]:
            log(
                f"[delete_manifest_annotations]: Failed. Status: {r.status_code}. Error: {r.text}"
            )
            return False
        log(
            f"[delete_manifest_annotations]: Removed {r.json().get('deletedCount', '?')} annotations"
        )
    except Exception as e:
        log(f"[delete_manifest_annotations]: Failed for {manifest_url}", e)
        return False
    return True


# NOTE NOT USED
def unindex_annotations_for_canvas(canvas_uri: str) -> bool:
    """delete all annotations that have for target `canvas_uri`"""
    try:
        url_delete = f"{AIIINOTATE_BASE_URL}/annotations/{IIIF_PRESENTATION_VERSION}/delete?canvasUri={canvas_uri}"
        r = requests.delete(url_delete)
        if not r.status_code in [200, 204]:
            log(
                f"[unindex_annotations_for_canvas]: Failed to remove annotations for canvas {canvas_uri}"
                f"Status code: {r.status_code}. Error: {r.text}"
            )
            return False
        deleted_count = r.json()["deletedCount"]
        log(f"[unindex_annotations_for_canvas]: Removed {deleted_count} annotations")
    except Exception as e:
        log(
            f"[unindex_annotations_for_canvas]: Failed to remove annotations for canvas {canvas_uri}",
            e,
        )
        return False
    return True


def unindex_regions(regions_ref, manifest_url: str) -> bool:
    """
    Delete all aiiinotations for a specific Regions extraction.
    Does NOT unindex the manifest
    """
    index_manifest(manifest_url)  # no effect if manifest is already indexed

    # Delete only annotations tagged with this regions_ref
    deleted = unindex_annotations_by_tag(manifest_url, regions_ref)

    return deleted >= 0  # Success even if 0 annotations found


def destroy_regions(regions: Regions):
    manifest_url = regions.get_manifest_url()
    regions_ref = regions.get_ref()

    try:
        regions.delete()
    except Exception as e:
        log(f"[destroy_regions] Failed to delete regions record #{regions.id}", e)
        return False

    try:
        witness = Witness.objects.get(
            Q(digitizations__witness_id=regions.digitization.witness_id)
        )
        witness.set_json_regions()
    except Exception as e:
        log(f"[destroy_regions] Failed to update witness.json", e)

    regions_file = f"{REGIONS_PATH}/{regions_ref}.json"
    if Path(regions_file).exists():
        try:
            Path(regions_file).unlink()
        except Exception as e:
            log(f"[destroy_regions] Failed to delete regions file #{regions_ref}", e)

    # Only unindex annotations for this extraction, NOT the manifest
    return unindex_regions(regions_ref, manifest_url)
