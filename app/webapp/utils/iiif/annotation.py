import json
import re
from datetime import datetime
from glob import glob
from urllib.parse import urlencode
from urllib.request import urlopen

import requests

from app.webapp.models.annotation import Annotation
from app.webapp.models.digitization import Digitization
from app.webapp.utils.constants import MANIFEST_V2, MANIFEST_V1
from app.webapp.utils.paths import MEDIA_DIR, BASE_DIR, ANNO_PATH
from app.webapp.models import get_wit_abbr, get_wit_type
from app.webapp.models.utils.constants import MS, VOL, MS_ABBR, VOL_ABBR
from app.config.settings import (
    APP_URL,
    CANTALOUPE_APP_URL,
    SAS_APP_URL,
    APP_NAME,
    API_GPU_URL,
    API_KEY,
)
from app.webapp.utils.functions import (
    console,
    log,
    read_json_file,
    write_json_file,
    get_imgs,
    get_img_prefix,
)


def send_anno_request(event, digit: Digitization):
    event.wait()
    try:
        anno_request(digit)
    except Exception as e:
        log(f"[send_anno_request] Failed to send request for digit #{digit.id}: {e}")
        return False

    return True


def anno_request(digit: Digitization):
    requests.post(
        url=f"{API_GPU_URL}/run_detect",
        headers={"X-API-Key": API_KEY},
        data={
            "manifest_url": digit.gen_manifest_url()
        },  # TODO see what additional data is needed for the API
    )


def process_anno(anno_file_content, digit):
    if check_anno_file(anno_file_content):
        try:
            anno = Annotation(digitization=digit, model="CHANGE THIS VALUE")
            anno.save()
        except Exception as e:
            log(f"[receive_anno] Create annotation record for digit #{digit.id}", e)
            return False

        try:
            with open(f"{BASE_DIR}/{ANNO_PATH}/{anno.get_ref}.txt", "w+b") as f:
                f.write(anno_file_content)
        except Exception as e:
            log(
                f"[receive_anno] Failed to save received annotations for digit #{digit.id}",
                e,
            )
            return False

        try:
            index_annotations(anno)
        except Exception as e:
            log(f"[receive_anno] Failed to index annotations for digit #{digit.id}", e)
            return False

    return True


def index_annotations(anno: Annotation):
    if not index_manifest_in_sas(anno.gen_manifest_url(), True):
        return

    canvases_to_annotate = get_annos_per_canvas(anno)
    if not bool(canvases_to_annotate):
        # if the annotation file is empty
        return True

    for c in canvases_to_annotate:
        try:
            index_annos_on_canvas(anno, c)
        except Exception as e:
            log(
                f"[index_annotations]: Problem indexing annotation #{anno.id} (canvas {c})",
                e,
            )

    return True


def unindex_anno(anno_id, remove_from_anno_ids=False):
    http_sas = SAS_APP_URL.replace("https", "http")
    if remove_from_anno_ids:
        id_annotation = re.search(r"_anno(\d+)", anno_id).group(1)
        # TODO remove from anno.anno_ids when it is only one anno that is deleted

    # anno_id = f"{wit_abbr}{wit_id}_{digit_abbr}{digit_id}_anno{anno_id}_c{canvas_nb}_{uuid4().hex[:8]}
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
        log(f"[unindex_anno] Delete anno request failed", e)
    return False


def delete_annos(anno: Annotation):
    index_manifest_in_sas(anno.gen_manifest_url())
    anno_id = 0
    try:
        for anno in get_manifest_annos(anno):
            anno_id = anno.split("/")[-1]
            unindex_anno(anno_id)
    except Exception as e:
        log(f"[delete_annos] Failed to unindex annotation #{anno_id}", e)
        return False

    try:
        # Delete the annotation record in the database
        anno.delete()
        anno.save()
    except Exception as e:
        log(f"[delete_annos] Failed to delete annotation record #{anno.id}", e)
        return False

    return True


def index_annos_on_canvas(anno: Annotation, canvas):
    # this url is calling format_canvas_annos(), thus returning formatted annos for each canvas
    formatted_annos = f"{anno.gen_manifest_url(True)}/list/anno-{canvas}.json"
    # POST request that index the annotations
    response = urlopen(
        f"{SAS_APP_URL}/annotation/populate",
        urlencode({"uri": formatted_annos}).encode("ascii"),
    )

    if response.status != 201:
        log(
            f"[index_annos_on_canvas] Failed to index annotations. Status: {response.status_code}",
            response.text,
        )
        return


def get_annos_per_canvas(anno: Annotation, last_canvas=0, specific_canvas=""):
    """
    Returns a dict with the text annotation file info:
    { "canvas1": [ coord1, coord2 ], "canvas2": [], "canvas3": [ coord1 ] }

    if specific_canvas, returns [ coord1, coord2 ]

    coord = (x, y, width, height)
    """
    lines = get_txt_annos(anno)
    if lines is None:
        log(f"[get_annos_per_canvas] no annotation file for Annotation #{anno.id}")
        return {}

    annotated_canvases = {}
    current_canvas = "0"
    for line in lines:
        # if the current line concerns an img (ie: line = "img_nb img_file.jpg")
        if len(line.split()) == 2:
            current_canvas = line.split()[0]
            # TODO change, because for one specific canvas, we retrieve all the canvas before
            # TODO maybe create a json file to store annotations in another form
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


def get_txt_annos(anno: Annotation):
    try:
        with open(f"{BASE_DIR}/{ANNO_PATH}/{anno.get_ref()}.txt") as f:
            return [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        return None


def get_anno_img(anno: Annotation):
    lines = get_txt_annos(anno)
    if lines is None:
        return []

    imgs = []
    img_name = f"{anno.get_ref()}_0000.jpg"
    for line in lines:
        if len(line.split()) == 2:
            img_name = line.split()[1]
        else:
            x, y, w, h = line.split()
            imgs.append(
                f"{CANTALOUPE_APP_URL}/iiif/2/{img_name}/{x},{y},{w},{h}/full/0/default.jpg"
            )
    return imgs


def format_canvas_annos(anno: Annotation, canvas_nb):
    canvas_annos = get_annos_per_canvas(anno, specific_canvas=str(canvas_nb))
    if len(canvas_annos) == 0:
        return {"@type": "sc:AnnotationList", "resources": []}

    return {
        "@type": "sc:AnnotationList",
        "resources": [
            format_annotation(
                anno,
                canvas_nb,
                canvas_annos[anno_num],
            )
            for anno_num in range(len(canvas_annos))
        ],
    }


def format_annotation(anno: Annotation, canvas_nb, xywh):
    base_url = anno.gen_manifest_url(only_base=True)

    x, y, w, h = xywh

    width = w // 2
    height = h // 2

    anno_id = anno.gen_anno_id(canvas_nb)  # TODO do we store annotations ids?
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
                "full": f"{base_url}/canvas/c{canvas_nb}.json",
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
    anno = canvas.annotation(
        ident=f"a{canvas_nb}"
    )  # TODO here maybe generated id with anno.gen_anno_id()
    if re.match(r"https?://(.*?)/", img_name):
        # to build hybrid manifest referencing images from other IIIF repositories
        img = anno.image(img_name, iiif=False)
        setattr(img, "format", "image/jpeg")
    else:
        img = anno.image(ident=img_name, iiif=True)

    img.set_hw(h, w)
    # TODO here check if this is correct for manifest_v1
    if version == MANIFEST_V1:
        anno_list = canvas.annotationList(ident=f"anno-{canvas_nb}")
        anno = anno_list.annotation(ident=f"a-list-{canvas_nb}")
        anno.text("Annotation")


def get_indexed_manifests():
    try:
        r = requests.get(f"{SAS_APP_URL}/manifests")
        manifests = r.json()["manifests"]
    except Exception as e:
        log(f"[get_indexed_manifests]: Failed to load indexed manifests in SAS: {e}")
        return False
    return [m["@id"] for m in manifests]


def index_manifest_in_sas(manifest_url, reindex=False):
    if not reindex:
        manifests = get_indexed_manifests()
        if manifests and manifest_url in manifests:
            # if the manifest was already indexed
            return True

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


def get_canvas_list(anno: Annotation):
    lines = get_txt_annos(anno)
    if not lines:
        log(f"[get_canvas_list] no annotation file for annotation #{anno.id}")
        return {
            "error": "the annotations were not yet generated"
        }  # TODO find a way to display error msg

    imgs = anno.get_imgs()

    canvases = []
    for line in lines:
        # if the current line concerns an img (ie: line = "img_nb img_file.jpg")
        if len(line.split()) == 2:
            _, img_file = line.split()
            # use the image number as canvas number because it is more reliable that the one provided in the anno file
            canvas_nb = int(img_file.split("_")[1].split(".")[0])
            if img_file in imgs:
                canvases.append((canvas_nb, img_file))

    return canvases


def get_indexed_annos(anno: Annotation):
    # not used
    annos = {}
    for canvas_nb, _ in get_canvas_list(anno):
        annos[canvas_nb] = get_indexed_canvas_annos(anno, canvas_nb)
    return annos


def get_indexed_canvas_annos(anno: Annotation, canvas_nb):
    try:
        response = urlopen(
            f"{SAS_APP_URL}/annotation/search?uri={anno.gen_manifest_url(True)}/canvas/c{canvas_nb}.json"
        )
        return json.loads(response.read())
    except Exception as e:
        log(
            f"[get_indexed_canvas_annos] Could not retrieve anno for annotation #{anno.id}",
            e,
        )
        return []


def get_coord_from_anno(sas_anno):
    try:
        # coordinates => "x,y,w,h"
        return (sas_anno["on"][0]["selector"]["default"]["value"]).split("=")[1]
    except Exception as e:
        log(f"[get_coord_from_anno] Could not retrieve coord from anno: {e}")
        return "0,0,0,0"


def get_id_from_anno(sas_anno):
    try:
        # anno_id => "{wit_abbr}{wit_id}_{digit_abbr}{digit_id}_anno{anno_id}_c{canvas_nb}_{uuid4().hex[:8]}"
        return sas_anno["@id"].split("/")[-1]  # todo check if it is still the case
    except Exception as e:
        log(f"[get_id_from_anno] Could not retrieve id from anno", e)
        return ""


def formatted_digit_anno(anno: Annotation):
    canvas_annos = []
    anno_ids = []

    # TODO: here allow to display images that are not present in the annotation file

    try:
        for canvas_nb, img_file in get_canvas_list(anno):
            c_annos = get_indexed_canvas_annos(anno, canvas_nb)
            coord_annos = []

            if bool(c_annos):
                coord_annos = [
                    (
                        get_coord_from_anno(sas_anno),
                        get_id_from_anno(sas_anno),
                    )
                    for sas_anno in c_annos
                ]
                anno_ids.extend(anno_id for _, anno_id in coord_annos)

            canvas_annos.append((canvas_nb, coord_annos, img_file))
    except ValueError as e:
        log(
            f"[formatted_digit_anno] Error when generating auto annotation list (probably no annotation file): {e}"
        )

    return anno_ids, canvas_annos


def check_anno_file(file_content):
    # TODO check file content (if it contains the correct info)
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


def get_manifest_annos(anno: Annotation):
    try:
        # TODO: check which ref is used
        response = requests.get(f"{SAS_APP_URL}/search-api/{anno.get_ref()}/search")
        annos = response.json()

        if response.status_code != 200:
            log(
                f"[get_manifest_annos] Failed to get annos from SAS: {response.status_code}"
            )
            return []
    except requests.exceptions.RequestException as e:
        log(f"[get_manifest_annos] Failed to retrieve annotations", e)
        return []

    if "resources" not in annos or len(annos["resources"]) == 0:
        return []

    try:
        manifest_annos = [anno["@id"] for anno in annos["resources"]]
    except Exception as e:
        log(f"[get_manifest_annos] Failed to parse annotations", e)
        return []

    return manifest_annos


def check_indexation_annos(anno: Annotation, reindex=False):
    lines = get_txt_annos(anno)
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
                sas_annos = get_indexed_canvas_annos(anno, canvas_nb)
                nb_annos = len(sas_annos)

                if nb_annos != 0:
                    indexed_annos += nb_annos
                    anno_ids.extend(
                        [get_id_from_anno(sas_anno) for sas_anno in sas_annos]
                    )
                else:
                    if not index_manifest_in_sas(anno.gen_manifest_url()):
                        return
            elif len_line == 4:
                # if line = "x y w h"
                generated_annos += 1
    except Exception as e:
        log(
            f"[check_indexation_annos] Failed to check indexation for anno #{anno.id}",
            e,
        )

    if generated_annos != indexed_annos:
        for anno_id in anno_ids:
            unindex_anno(anno_id)
        if reindex:
            if index_annotations(anno):
                log(f"[check_indexation_annos] Annotation #{anno.id} was reindexed")


def get_anno_images(anno: Annotation):
    # Used to export images annotations
    imgs = []

    try:
        for canvas_nb, img_file in get_canvas_list(anno):
            c_annos = get_indexed_canvas_annos(anno, canvas_nb)

            if bool(c_annos):
                canvas_imgs = [
                    f"{CANTALOUPE_APP_URL}/iiif/2/{img_file}/{get_coord_from_anno(sas_anno)}/full/0/default.jpg"
                    for sas_anno in c_annos
                ]
                imgs.extend(canvas_imgs)
    except ValueError as e:
        log(f"[get_anno_images] Error when retrieving annotations: {e}")

    return imgs
