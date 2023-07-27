import json
import re
from datetime import datetime
from glob import glob
from urllib.parse import urlencode
from urllib.request import urlopen

import requests
from vhsapp.utils.paths import MEDIA_PATH, BASE_DIR, VOL_ANNO_PATH, MS_ANNO_PATH
from vhsapp.models import get_wit_abbr, get_wit_type
from vhsapp.models.constants import MS, VOL, MS_ABBR, VOL_ABBR
from vhs.settings import VHS_APP_URL, CANTALOUPE_APP_URL, SAS_APP_URL, GPU_URL
from vhsapp.utils.constants import APP_NAME, MANIFEST_AUTO
from vhsapp.utils.functions import (
    console,
    log,
    read_json_file,
    write_json_file,
    get_imgs,
    get_img_prefix,
)


def annotate_wit(event, wit_id, wit_abbr=MS_ABBR, version=MANIFEST_AUTO):
    wit_type = MS if wit_abbr == MS_ABBR else VOL

    manifest_url = (
        f"{VHS_APP_URL}/{APP_NAME}/iiif/{version}/{wit_type}/{wit_id}/manifest.json"
    )

    event.wait()

    try:
        requests.post(
            url=f"{GPU_URL}/run_detect",
            data={"manifest_url": manifest_url, "wit_abbr": wit_abbr},
        )
    except Exception as e:
        log(
            f"[annotate_wit] Failed to send annotation request for {wit_type} #{wit_id}: {e}"
        )
        return

    return


def index_anno(manifest_url, wit_type, wit_id):
    if not index_manifest_in_sas(manifest_url):
        return

    try:
        # Populate the annotation
        requests.get(f"{VHS_APP_URL}/{APP_NAME}/iiif/v2/{wit_type}/{wit_id}/populate/")
    except Exception as e:
        log(
            f"[index_anno]: Failed to index annotations generated for {wit_type} #{wit_id}: {e}"
        )


def index_wit_annotations(wit_id, wit_type):
    # last_canvases = get_last_indexed_canvas()
    # last_indexed_canvas = (
    #     last_canvases[str(wit_id)] if str(wit_id) in last_canvases else 0
    # )

    canvases_to_annotate = get_annos_per_canvas(wit_id, wit_type)

    if not bool(canvases_to_annotate):
        # if the annotation file is empty
        return True

    iiif_url = f"{VHS_APP_URL}/{APP_NAME}/iiif/v2/{wit_type}/{wit_id}"
    for c in canvases_to_annotate:
        try:
            index_annos_on_canvas(iiif_url, c, 0)
        except Exception as e:
            log(
                f"[index_wit_annotations]: Problem indexing annotation for {wit_type} n°{wit_id} (canvas {c}): {e}"
            )

    return True


def unindex_anno(anno_id):
    http_sas = SAS_APP_URL.replace("https", "http")
    # anno_id = f"{wit_abbr}-{wit_id}-{canvas_nb}-{anno_nb}"
    delete_url = f"{SAS_APP_URL}/annotation/destroy?uri={http_sas}/annotation/{anno_id}"
    try:
        response = requests.delete(delete_url)
        if response.status_code == 204:
            return True
        else:
            log(
                f"[unindex_anno] Delete anno request failed with status code: {response.status_code}"
            )
    except requests.exceptions.RequestException as e:
        log(f"[unindex_anno] Delete anno request failed: {e}")
    return False


def index_annos_on_canvas(wit_url, canvas, last_canvases=None):
    # this url is calling format_canvas_annos(), thus returning formatted annos for each canvas
    formatted_annos = f"{wit_url}/list/anno-{canvas}.json"
    # POST request that index the annotations
    response = urlopen(
        f"{SAS_APP_URL}/annotation/populate",
        urlencode({"uri": formatted_annos}).encode("ascii"),
    )

    if response.status != 201:
        log(
            f"[index_annos_on_canvas] Failed to index annotations. Status code: {response.status_code}: {response.text}"
        )
        return
    # set_last_indexed_canvas(wit_id, canvas, last_canvases)


"""
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
"""


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
            # TODO change, because for one specific canvas, we retrieve all the canvas before
            # todo maybe create a json file to store annotations in another form
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


def format_canvas_annos(wit_id, version, wit_type, canvas):
    canvas_annos = get_annos_per_canvas(wit_id, wit_type, specific_canvas=str(canvas))
    # todo, check that
    if len(canvas_annos) == 0:
        return {"@type": "sc:AnnotationList", "resources": []}

    return {
        "@type": "sc:AnnotationList",
        "resources": [
            format_annotation(
                wit_id,
                version,
                wit_type,
                canvas,
                canvas_annos[anno_num],
                anno_num,
            )
            for anno_num in range(len(canvas_annos))
        ],
    }


def format_annotation(wit_id, version, wit_type, canvas, xywh, num_anno):
    wit_abbr = get_wit_abbr(wit_type)
    base_url = f"{VHS_APP_URL}/{APP_NAME}/iiif/{version}/{wit_type}/{wit_id}"

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


def has_annotations(witness, wit_abbr):
    # if there is at least one image file named after the current witness
    wit_dir = "manuscripts" if wit_abbr == MS_ABBR else "volumes"
    if len(glob(f"{BASE_DIR}/{MEDIA_PATH}/{wit_dir}/annotation/{witness.id}.txt")) > 0:
        return True
    return False


def index_manifest_in_sas(manifest_url):
    try:
        manifest = requests.get(manifest_url)
        manifest_content = manifest.json()
    except Exception as e:
        log(f"[index_manifest_in_sas]: Failed to load manifest for {manifest_url}: {e}")
        return False

    try:
        # Index the manifest into SAS
        r = requests.post(f"{SAS_APP_URL}/manifests", json=manifest_content)
        if r.status_code != 200:
            log(
                f"[index_manifest_in_sas] Failed to index manifest. Status code: {r.status_code}: {r.text}"
            )
            return False
    except Exception as e:
        log(
            f"[index_manifest_in_sas]: Failed to index manifest {manifest_url} in SAS: {e}"
        )
        return False
    return True


def get_canvas_list(witness, wit_type):
    lines = get_txt_annos(
        witness.id, VOL_ANNO_PATH if wit_type == VOL else MS_ANNO_PATH
    )
    if not lines:
        log(f"[get_canvas_list] no annotation file for {wit_type} n°{witness.id}")
        return {
            "error": "the annotations were not yet generated"
        }  # TODO find a way to display error msg

    wit_imgs = get_imgs(get_img_prefix(witness, wit_type))

    canvases = []
    for line in lines:
        # if the current line concerns an img (ie: line = "img_nb img_file.jpg")
        if len(line.split()) == 2:
            _, img_file = line.split()
            # use the image number as canvas number because it is more reliable that the one provided in the anno file
            canvas_nb = int(img_file.split("_")[1].split(".")[0])
            if img_file in wit_imgs:
                canvases.append((canvas_nb, img_file))

    return canvases


def get_indexed_wit_annos(wit_id, wit_type):
    return {}


def get_indexed_canvas_annos(canvas_nb, wit_id, wit_type):
    iiif_url = f"{VHS_APP_URL}/{APP_NAME}/iiif/v2/{wit_type}/{wit_id}"
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


def get_coord_from_anno(anno):
    try:
        # coordinates => "x,y,w,h"
        return (anno["on"][0]["selector"]["default"]["value"]).split("=")[1]
    except Exception as e:
        log(f"[get_coord_from_anno] Could not retrieve coord from anno: {e}")
        return "0,0,0,0"


def get_id_from_anno(anno):
    try:
        # annotation id => "wit_abbr-wit_id-canvas_nb-anno_nb
        return anno["@id"].split("/")[-1]
    except Exception as e:
        log(f"[get_id_from_anno] Could not retrieve id from anno: {e}")
        return ""


def formatted_wit_anno(witness, wit_type):
    canvas_annos = []
    wit_anno_ids = []

    try:
        for canvas_nb, img_file in get_canvas_list(witness, wit_type):
            c_annos = get_indexed_canvas_annos(canvas_nb, witness.id, wit_type)
            coord_annos = []

            if bool(c_annos):
                coord_annos = [
                    (
                        get_coord_from_anno(anno),
                        get_id_from_anno(anno),
                    )
                    for anno in c_annos
                ]
                wit_anno_ids.extend(anno_id for _, anno_id in coord_annos)

            canvas_annos.append((canvas_nb, coord_annos, img_file))
    except ValueError as e:
        log(
            f"[formatted_wit_anno] Error when generating auto annotation list (probably no annotation file): {e}"
        )

    return wit_anno_ids, canvas_annos


def check_anno_file(file_content):
    textchars = (
        bytearray([7, 8, 9, 10, 12, 13, 27])
        + bytearray(range(0x20, 0x7F))
        + bytearray(range(0x80, 0x100))
    )
    is_binary_string = lambda bytes: bool(bytes.translate(None, textchars))

    if not is_binary_string(file_content[:1024]):
        return True
    else:
        return False


def get_manifest_annotations(manifest_uri):
    # NOTE Do not work: always return []
    try:
        response = requests.get(
            f"{SAS_APP_URL}/annotation/search", params={"uri": manifest_uri}
        )

        if response.status_code == 200:
            return response.json()
        else:
            log(
                f"[get_manifest_annotations] Failed to retrieve annotations: {response.status_code}"
            )
    except requests.exceptions.RequestException as e:
        log(f"[get_manifest_annotations] Failed to retrieve annotations: {e}")
    return False


def check_wit_annos(wit_id, wit_type, reindex=False):
    lines = get_txt_annos(wit_id, VOL_ANNO_PATH if wit_type == VOL else MS_ANNO_PATH)
    if not lines:
        return

    generated_annos = 0
    indexed_annos = 0

    anno_ids = []
    try:
        for line in lines:
            len_line = len(line.split())
            if len_line == 2:
                # if line = "canvas_nb img_name"
                canvas_nb = line.split()[0]
                sas_annos = get_indexed_canvas_annos(canvas_nb, wit_id, wit_type)
                nb_annos = len(sas_annos)

                if nb_annos != 0:
                    indexed_annos += nb_annos
                    anno_ids.extend([get_id_from_anno(anno) for anno in sas_annos])
                else:
                    res = index_manifest_in_sas(
                        f"{VHS_APP_URL}/{APP_NAME}/iiif/v2/{wit_type}/{wit_id}/manifest.json"
                    )
                    if not res:
                        return
            elif len_line == 4:
                # if line = "x y w h"
                generated_annos += 1
    except Exception as e:
        log(
            f"[check_wit_annos] Failed to compare annotations for {wit_type} #{wit_id}: {e}"
        )

    if generated_annos != indexed_annos:
        for anno_id in anno_ids:
            unindex_anno(anno_id)
        if reindex:
            log(f"[check_wit_annos] reindexing {wit_id}")
            index_wit_annotations(wit_id, wit_type)


def get_imgs_annotations(witness, wit_type):
    imgs = []

    try:
        for canvas_nb, img_file in get_canvas_list(witness, wit_type):
            c_annos = get_indexed_canvas_annos(canvas_nb, witness.id, wit_type)

            if bool(c_annos):
                canvas_imgs = [
                    f"{CANTALOUPE_APP_URL}/iiif/2/{img_file}/{get_coord_from_anno(anno)}/full/0/default.jpg"
                    for anno in c_annos
                ]
                imgs.extend(canvas_imgs)
    except ValueError as e:
        log(f"[get_imgs_annotations] Error when retrieving annotations: {e}")

    return imgs
