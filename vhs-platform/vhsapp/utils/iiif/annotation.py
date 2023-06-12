import json
import re
from datetime import datetime
from glob import glob
from urllib.parse import urlencode
from urllib.request import urlopen

from vhsapp.utils.paths import MEDIA_PATH, BASE_DIR, VOL_ANNO_PATH, MS_ANNO_PATH
from vhsapp.models.constants import MS, VOL, MS_ABBR, VOL_ABBR
from vhs.settings import VHS_APP_URL, CANTALOUPE_APP_URL, SAS_APP_URL
from vhsapp.utils.constants import APP_NAME
from vhsapp.utils.functions import console, log, read_json_file, write_json_file


def unindex_anno(canvas, anno_id):
    # TODO (check js function in script.js)
    return True


def index_annos_on_canvas(base_url, wit_id, canvas, last_canvases=None):
    if last_canvases is None:
        last_canvases = get_last_indexed_canvas()

    # {base_url}/list/anno-{c}.json is calling format_canvas_annos(), thus returning formatted annos for each canvas
    params = urlencode({"uri": f"{base_url}/list/anno-{canvas}.json"}).encode("ascii")
    urlopen(
        f"{SAS_APP_URL}/annotation/populate", params
    )  # POST request that index the annos
    set_last_indexed_canvas(wit_id, canvas, last_canvases)


def get_last_indexed_canvas(wit_id=None):
    last_canvases = read_json_file(f"{BASE_DIR}/{MEDIA_PATH}/all_anno.json")
    if not last_canvases:
        return 0 if wit_id is not None else {}

    if wit_id is None:
        return last_canvases

    if str(wit_id) not in last_canvases:
        return 0
    return last_canvases[str(wit_id)]


def set_last_indexed_canvas(wit_id, last_canvas=0, last_canvases=None):
    if last_canvases is None:
        last_canvases = get_last_indexed_canvas()

    last_canvases[str(wit_id)] = int(last_canvas)
    write_json_file(f"{BASE_DIR}/{MEDIA_PATH}/all_anno.json", last_canvases)


def get_annos_per_canvas(wit_id, wit_type, last_canvas=0, specific_canvas=""):
    """
    Returns a dict with the text annotation file info:
    { "canvas1": [ coord1, coord2 ], "canvas2": [], "canvas3": [ coord1 ] }

    if specific_canvas, returns [ coord1, coord2 ]

    coord = (x, y, width, height)
    """
    lines = get_txt_annos(wit_id, VOL_ANNO_PATH if wit_type == VOL else MS_ANNO_PATH)
    if lines is None:
        log(f"[get_annos_per_canvas] no annotation file for {wit_type} n°{wit_id}")
        return {}

    annotated_canvases = {}
    current_canvas = "0"
    for line in lines:
        # if the current line concerns an img (ie: line = "img_nb img_file.jpg")
        if len(line.split()) == 2:
            current_canvas = line.split()[0]
            if int(current_canvas) > last_canvas or specific_canvas == current_canvas:
                # if the current annotation was not already annotated, add it to the list to annotate
                # or if it is the specific canvas that we need to retrieve
                annotated_canvases[current_canvas] = []
        # if the current line contains coordinates (ie "x y width height")
        else:
            if current_canvas in annotated_canvases:
                annotated_canvases[current_canvas].append(
                    tuple(int(coord) for coord in line.split())
                )

    if specific_canvas != "":
        return (
            annotated_canvases[specific_canvas]
            if specific_canvas in annotated_canvases
            else []
        )

    return annotated_canvases


def check_wit_annotation(wit_id, wit_type):
    wit_abbr = VOL_ABBR if wit_type == VOL else MS_ABBR
    last_canvases = get_last_indexed_canvas()
    last_index_canvas = (
        last_canvases[str(wit_id)] if str(wit_id) in last_canvases else 0
    )

    # contains only annotations that were not yet indexed in SAS
    annotated_canvases = get_annos_per_canvas(
        wit_id, wit_type, last_canvas=last_index_canvas
    )

    if not bool(annotated_canvases):
        # if the annotation file is empty
        return True

    iiif_url = f"{VHS_APP_URL}/{APP_NAME}/iiif/v2/{wit_type}/{wit_abbr}-{wit_id}"
    for c in annotated_canvases:
        try:
            index_annos_on_canvas(iiif_url, wit_id, c, last_canvases)
        except Exception as e:
            log(
                f"[check_wit_annotation]: Problem indexing annotation for {wit_type} n°{wit_id} (canvas {c}): {e}"
            )

    return True


def get_txt_annos(wit_id, annotations_path):
    try:
        with open(f"{BASE_DIR}/{MEDIA_PATH}/{annotations_path}/{wit_id}.txt") as f:
            return [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        return None


def get_anno_img(wit_id, wit_type):
    annotations_path = VOL_ANNO_PATH if wit_type == VOL else MS_ANNO_PATH

    lines = get_txt_annos(wit_id, annotations_path)
    if lines is None:
        return []

    imgs = []
    img_name = f"{wit_type}{wit_id}_0000.jpg"
    for line in lines:
        if len(line.split()) == 2:
            img_name = line.split()[1]
        else:
            x, y, w, h = line.split()
            imgs.append(
                f"{CANTALOUPE_APP_URL}/iiif/2/{img_name}/{x},{y},{w},{h}/full/0/default.jpg"
            )
    return imgs


def get_indexed_wit_annos(wit_id, wit_type):
    return {}


def get_indexed_canvas_annos(canvas_nb, wit_id, wit_type):
    wit_abbr = VOL_ABBR if wit_type == VOL else MS_ABBR
    iiif_url = f"{VHS_APP_URL}/{APP_NAME}/iiif/v2/{wit_type}/{wit_abbr}-{wit_id}"
    try:
        response = urlopen(
            f"{SAS_APP_URL}/annotation/search?uri={iiif_url}/canvas/c{canvas_nb}.json"
        )
        return json.loads(response.read())
    except Exception as e:
        log(
            f"[get_indexed_canvas_annos] Could not retrieve anno for {wit_type} n°{wit_id}: {e}"
        )
        return []


def format_canvas_annos(wit_id, version, wit_type, wit_abbr, canvas):
    canvas_annos = get_annos_per_canvas(wit_id, wit_type, specific_canvas=str(canvas))
    if len(canvas_annos) == 0:
        return {"@type": "sc:AnnotationList", "resources": []}

    return {
        "@type": "sc:AnnotationList",
        "resources": [
            format_annotation(
                wit_id,
                version,
                wit_type,
                wit_abbr,
                canvas,
                canvas_annos[anno_num],
                anno_num,
            )
            for anno_num in range(len(canvas_annos))
        ],
    }


def format_annotation(wit_id, version, wit_type, wit_abbr, canvas, xywh, num_anno):
    base_url = f"{VHS_APP_URL}/{APP_NAME}/iiif/{version}/{wit_type}/{wit_abbr}-{wit_id}"

    x, y, w, h = xywh

    width = w // 2
    height = h // 2

    anno_id = f"{wit_abbr}-{wit_id}-{canvas}-{num_anno + 1}"
    d = f"M{x} {y} h {width} v 0 h {width} v {height} v {height} h -{width} h -{width} v -{height}Z"
    r_id = f"rectangle_{anno_id}"
    d_paper = "{&quot;strokeWidth&quot;:1,&quot;rotation&quot;:0,&quot;annotation&quot;:null,&quot;nonHoverStrokeColor&quot;:[&quot;Color&quot;,0,1,0],&quot;editable&quot;:true,&quot;deleteIcon&quot;:null,&quot;rotationIcon&quot;:null,&quot;group&quot;:null}"

    path = f"""<path xmlns='http://www.w3.org/2000/svg'
                    d='{d}'
                    id='{r_id}'
                    data-paper-data='{d_paper}'
                    fill-opacity='0'
                    fill='#00ff00'
                    fill-rule='nonzero'
                    stroke='#00ff00'
                    stroke-width='1'
                    stroke-linecap='butt'
                    stroke-linejoin='miter'
                    stroke-miterlimit='10'
                    stroke-dashoffset='0'
                    style='mix-blend-mode: normal'/>"""
    path = re.sub(r"\s+", " ", path).strip()

    set_last_indexed_canvas(wit_id, canvas)

    return {
        "@id": f"{SAS_APP_URL.replace('https', 'http')}/annotation/{anno_id}",
        "@type": "oa:Annotation",
        "dcterms:created": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "dcterms:modified": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "resource": [
            {
                "@type": "dctypes:Text",
                f"{SAS_APP_URL}/full_text": "",
                "format": "text/html",
                "chars": "<p></p>",
            }
        ],
        "on": [
            {
                "@type": "oa:SpecificResource",
                "within": {
                    "@id": f"{base_url}/manifest.json",
                    "@type": "sc:Manifest",
                },
                "selector": {
                    "@type": "oa:Choice",
                    "default": {
                        "@type": "oa:FragmentSelector",
                        "value": f"xywh={x},{y},{w},{h}",
                    },
                    "item": {
                        "@type": "oa:SvgSelector",
                        "value": f'<svg xmlns="http://www.w3.org/2000/svg">{path}</svg>',
                    },
                },
                "full": f"{base_url}/canvas/c{canvas}.json",
            }
        ],
        "motivation": ["oa:commenting", "oa:tagging"],
        "@context": "http://iiif.io/api/presentation/2/context.json",
    }


def set_canvas(seq, canvas_nb, img_name, img, version):
    """
    Build the canvas and annotation for each image
    Called for each manifest (v2) image when a witness is being indexed
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
    anno = canvas.annotation(ident=f"a{canvas_nb}")
    if re.match(r"https?://(.*?)/", img_name):
        # to build hybrid manifest referencing images from other IIIF repositories
        img = anno.image(img_name, iiif=False)
        setattr(img, "format", "image/jpeg")
    else:
        img = anno.image(ident=img_name, iiif=True)

    img.set_hw(h, w)
    if version == "auto":
        anno_list = canvas.annotationList(ident=f"anno-{canvas_nb}")
        anno = anno_list.annotation(ident=f"a-list-{canvas_nb}")
        anno.text("Annotation")


def has_annotations(witness, wit_type):
    # if there is at least one image file named after the current witness
    wit_dir = "manuscripts" if wit_type == "ms" else "volumes"
    if len(glob(f"{BASE_DIR}/{MEDIA_PATH}/{wit_dir}/annotation/{witness.id}.txt")) > 0:
        return True
    return False
