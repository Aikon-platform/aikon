import json
import re
from datetime import datetime
from glob import glob
from urllib.request import urlopen

from vhsapp.utils.paths import MEDIA_PATH, BASE_DIR, VOL_ANNO_PATH, MS_ANNO_PATH
from vhsapp.models.constants import MS, VOL, MS_ABBR, VOL_ABBR
from vhs.settings import VHS_APP_URL, CANTALOUPE_APP_URL, SAS_APP_URL
from vhsapp.utils.constants import APP_NAME
from vhsapp.utils.functions import console, log


def unindex_anno(canvas, anno_id):
    return True


def annotate_wit(wit_id, version, wit_type, wit_abbr, canvas):
    annotations_path = VOL_ANNO_PATH if wit_type == VOL else MS_ANNO_PATH

    lines = get_txt_annos(wit_id, annotations_path)
    if lines is None:
        log(f"[annotate_witness] no annotation file for {wit_type} n°{wit_id}")
        return {"@type": "sc:AnnotationList", "resources": []}

    nb_of_annos = 0
    list_anno = []
    check = False
    for line in lines:
        if len(line.split()) == 2 and line.split()[0] == str(canvas):
            check = True
            continue
        if check:
            if len(line.split()) == 4:
                nb_of_annos += 1
                list_anno.append(tuple(int(item) for item in tuple(line.split())))
            else:
                break
    return {
        "@type": "sc:AnnotationList",
        "resources": [
            index_annotation(
                wit_id,
                version,
                wit_type,
                wit_abbr,
                canvas,
                list_anno[num_anno],
                num_anno,
            )
            for num_anno in range(nb_of_annos)
            if nb_of_annos > 0
        ],
    }


def get_txt_annos(wit_id, annotations_path):
    try:
        with open(f"{BASE_DIR}/{MEDIA_PATH}/{annotations_path}/{wit_id}.txt") as f:
            return [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        return None


def get_sas_annos(wit_id, wit_type):
    return {}


def get_indexed_annos(canvas_nb, wit_id, wit_type):
    wit_abbr = VOL_ABBR if wit_type == VOL else MS_ABBR
    iiif_url = f"{VHS_APP_URL}/{APP_NAME}/iiif/v2/{wit_type}/{wit_abbr}-{wit_id}"
    try:
        response = urlopen(
            f"{SAS_APP_URL}/annotation/search?uri={iiif_url}/canvas/c{canvas_nb}.json"
        )
        return json.loads(response.read())
    except Exception as e:
        log(
            f"[get_indexed_annos] Could not retrieve anno for {wit_type} n°{wit_id}: {e}"
        )
        return []


def index_annotation(wit_id, version, wit_type, wit_abbr, canvas, xywh, num_anno):
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


def set_canvas_annos(seq, canvas_nb, img_name, img, version):
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
