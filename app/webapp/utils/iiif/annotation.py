import json
import re
from datetime import datetime
from urllib.parse import urlencode
from urllib.request import urlopen

import requests
from PIL import Image

from app.webapp.models.annotation import Annotation
from app.webapp.models.digitization import Digitization
from app.webapp.utils.constants import MANIFEST_V2, MANIFEST_V1
from app.webapp.utils.paths import ANNO_PATH, IMG_PATH
from app.config.settings import (
    CANTALOUPE_APP_URL,
    SAS_APP_URL,
    APP_NAME,
    EXAPI_URL,
    EXAPI_KEY,
    APP_URL,
    EXTRACTOR_MODEL,
)
from app.webapp.utils.functions import log


def send_anno_request(digit: Digitization, event):
    event.wait()
    if not EXAPI_URL.startswith("http"):
        # on local to prevent bugs
        return True

    try:
        anno_request(digit)
    except Exception as e:
        log(f"[send_anno_request] Failed to send request for digit #{digit.id}", e)
        return False

    return True


def anno_request(digit: Digitization):
    try:
        response = requests.post(
            url=f"{EXAPI_URL}/extraction/start",
            data={
                "manifest_url": digit.gen_manifest_url(),
                "model": f"{EXTRACTOR_MODEL}",  # Use only if specific model is desire
                "callback": f"{APP_URL}/{APP_NAME}/annotate",  # URL to which the annotations must be sent back
            },
        )
        if response.status_code == 200:
            log(f"[annotation_request] Annotation request send: {response.text or ''}")
            return True
        else:
            error = {
                "source": "[anno_request]",
                "error_message": f"Annotation request for {digit.get_ref()} with status code: {response.status_code}",
                "request_info": {
                    "method": "POST",
                    "url": f"{EXAPI_URL}/extraction/start",
                    "data": {
                        "manifest_url": digit.gen_manifest_url(),
                        "model": f"{EXTRACTOR_MODEL}",
                        "callback": f"{APP_URL}/{APP_NAME}/annotate",
                    },
                },
                "response_info": {
                    "status_code": response.status_code,
                    "text": response.text or "",
                },
            }

            log(error)
            return False
    except Exception as e:
        log(f"[anno_request] Annotation request for {digit.get_ref()} failed", e)
        return False


def delete_anno_request(digit: Digitization):
    try:
        requests.post(
            url=f"{EXAPI_URL}/extraction/restart",
            data={
                "manifest_url": digit.gen_manifest_url(),
                # "model": "yolo_last_sved_vhs_sullivan.pt", # Use only if specific model is desired
                "callback": f"{APP_URL}/{APP_NAME}/annotate",  # URL to which the annotations must be sent back
            },
        )
        return True
    except Exception as e:
        return False


def process_anno(anno_file_content, digit, model="Unknown model"):
    try:
        # TODO add step to check if an annotation wasn't generated before for the same model
        anno = Annotation(digitization=digit, model=model)
        anno.save()
    except Exception as e:
        log(f"[receive_anno] Create annotation record for digit #{digit.id}", e)
        return False

    try:
        with open(f"{ANNO_PATH}/{anno.get_ref()}.txt", "w+b") as f:
            f.write(anno_file_content.encode("utf-8"))
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
    if not index_manifest_in_sas(anno.gen_manifest_url(version=MANIFEST_V2), True):
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

    # if remove_from_anno_ids:
    #     id_annotation = re.search(r"_anno(\d+)", anno_id).group(1)
    #     # TODO remove from anno.anno_ids when it is only one anno that is deleted

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
    index_manifest_in_sas(anno.gen_manifest_url(version=MANIFEST_V2))
    sas_anno_id = 0
    try:
        for sas_anno in get_manifest_annos(anno):
            sas_anno_id = sas_anno.split("/")[-1]
            unindex_anno(sas_anno_id)
    except Exception as e:
        log(f"[delete_annos] Failed to unindex annotation #{sas_anno_id}", e)
        return False

    try:
        # Delete the annotation record in the database
        anno.delete()
    except Exception as e:
        log(f"[delete_annos] Failed to delete annotation record #{anno.id}", e)
        return False

    return True


def index_annos_on_canvas(anno: Annotation, canvas_nb):
    # this url (view canvas_annotations()) is calling format_canvas_annos(), thus returning formatted annos for each canvas
    formatted_annos = f"{APP_URL}/{APP_NAME}/iiif/{MANIFEST_V2}/{anno.get_ref()}/list/anno-{canvas_nb}.json"
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
        with open(f"{ANNO_PATH}/{anno.get_ref()}.txt") as f:
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
    base_url = anno.gen_manifest_url(only_base=True, version=MANIFEST_V2)
    x, y, w, h = xywh

    width = w // 2
    height = h // 2

    anno_id = anno.gen_anno_id(canvas_nb)
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


def set_canvas(seq, canvas_nb, img_name, img, version=None):
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
    anno = canvas.annotation(ident=f"a{canvas_nb}")
    if re.match(r"https?://(.*?)/", img_name):
        # to build hybrid manifest referencing images from other IIIF repositories
        img = anno.image(img_name, iiif=False)
        setattr(img, "format", "image/jpeg")
    else:
        img = anno.image(ident=img_name, iiif=True)

    img.set_hw(h, w)
    # In case we do not really index "automatic" annotations but keep them as "otherContents"
    if version == MANIFEST_V1:
        # is calling f"{APP_NAME}/iiif/{version}/{anno.get_ref()}/list/anno-{canvas_nb}.json"
        # (canvas_annotations() view) that returns formatted annotations format_canvas_annos()
        anno_list = canvas.annotationList(ident=f"anno-{canvas_nb}")
        anno = anno_list.annotation(ident=f"a-list-{canvas_nb}")
        anno.text("Annotation")


def get_indexed_manifests():
    try:
        r = requests.get(f"{SAS_APP_URL}/manifests")
        manifests = r.json()["manifests"]
    except Exception as e:
        log(f"[get_indexed_manifests]: Failed to load indexed manifests in SAS", e)
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
        log(f"[index_manifest_in_sas]: Failed to load manifest for {manifest_url}", e)
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
            f"[index_manifest_in_sas]: Failed to index manifest {manifest_url} in SAS",
            e,
        )
        return False
    return True


def get_canvas_list(anno: Annotation, all_img=False):
    imgs = anno.get_imgs()
    if all_img:
        # Display all images associated to the digitization, even though they were not annotated
        return [(int(img.split("_")[-1].split(".")[0]), img) for img in imgs]

    lines = get_txt_annos(anno)
    if not lines:
        log(f"[get_canvas_list] no annotation file for annotation #{anno.id}")
        return {
            "error": "the annotations were not yet generated"
        }  # TODO find a way to display error msg

    canvases = []
    for line in lines:
        # if the current line concerns an img (ie: line = "img_nb img_file.jpg")
        if len(line.split()) == 2:
            _, img_file = line.split()
            # use the image number as canvas number because it is more reliable that the one provided in the anno file
            canvas_nb = int(img_file.split("_")[-1].split(".")[0])
            if img_file in imgs:
                canvases.append((canvas_nb, img_file))

    return canvases


def get_canvas_lists(digit: Digitization, all_img=False):
    canvases = []
    for anno in digit.get_annotations():
        canvases.extend(get_canvas_list(anno, all_img))
    return canvases


def get_training_anno(anno: Annotation):
    # Returns a list of tuples [(file_name, file_content), (...)]
    filenames_contents = []
    for canvas_nb, img_file in get_canvas_list(anno):
        sas_annos = get_indexed_canvas_annos(anno, canvas_nb)
        img = Image.open(f"{IMG_PATH}/{img_file}")
        width, height = img.size
        if bool(sas_annos):
            train_annos = []
            for sas_anno in sas_annos:
                x, y, w, h = [int(n) for n in get_coord_from_anno(sas_anno).split(",")]
                train_annos.append(
                    f"0 {((x + x + w) / 2) / width} {((y + y + h) / 2) / height} {w / width} {h / height}"
                )

            filenames_contents.append(
                (f"{img_file}".replace(".jpg", ".txt"), "\n".join(train_annos))
            )
    return filenames_contents


def get_indexed_annos(anno: Annotation):
    # not used
    annos = {}
    for canvas_nb, _ in get_canvas_list(anno):
        annos[canvas_nb] = get_indexed_canvas_annos(anno, canvas_nb)
    return annos


def get_indexed_canvas_annos(anno: Annotation, canvas_nb):
    try:
        response = urlopen(
            f"{SAS_APP_URL}/annotation/search?uri={anno.gen_manifest_url(only_base=True, version=MANIFEST_V2)}/canvas/c{canvas_nb}.json"
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
        # coord => "x,y,w,h"
        coord = (sas_anno["on"][0]["selector"]["default"]["value"]).split("=")[1]
        # remove negative values if some of the coordinates exceed the image boundaries
        return ",".join(["0" if int(num) < 0 else num for num in coord.split(",")])
    except Exception as e:
        log(f"[get_coord_from_anno] Could not retrieve coord from anno", e)
        return "0,0,0,0"


def get_id_from_anno(sas_anno):
    try:
        # anno_id => "{wit_abbr}{wit_id}_{digit_abbr}{digit_id}_anno{anno_id}_c{canvas_nb}_{uuid4().hex[:8]}"
        return sas_anno["@id"].split("/")[-1]
    except Exception as e:
        log(f"[get_id_from_anno] Could not retrieve id from anno", e)
        return ""


def create_empty_anno(digit: Digitization):
    imgs = digit.get_imgs()
    if len(imgs) == 0:
        return False

    try:
        anno = Annotation(digitization=digit, model="Manual")
        anno.save()
    except Exception as e:
        log(
            f"[create_empty_anno] unable to create new Annotation for digit #{digit.id} in the database",
            e,
        )
        return False

    try:
        with open(f"{ANNO_PATH}/{anno.get_ref()}.txt", "w") as anno_file:
            for i, img_name in enumerate(imgs, 1):
                anno_file.write(f"{i} {img_name}\n")
    except Exception as e:
        log(
            f"[create_empty_anno] unable to create new Annotation file for digit #{digit.id}",
            e,
        )

    return anno


def formatted_annotations(anno: Annotation):
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
            f"[formatted_annotations] Error when generating auto annotation list (probably no annotation file)",
            e,
        )

    return anno_ids, canvas_annos


def check_anno_file(file_content):
    # Either contains a number then an img.jpg / Or a series of 4 numbers
    pattern = re.compile(r"^\d+\s+\S+\.jpg$|^\d+\s\d+\s\d+\s\d+$")
    for line in file_content.split("\n"):
        if line == "":
            continue
        if not pattern.match(line):
            log(f"[check_anno_file] incorrect line {line}")
            return False
    return True


def get_manifest_annos(anno: Annotation):
    try:
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
        return False

    generated_annos = 0
    indexed_annos = 0

    sas_anno_ids = []
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
                    sas_anno_ids.extend(
                        [get_id_from_anno(sas_anno) for sas_anno in sas_annos]
                    )
                else:
                    if not index_manifest_in_sas(
                        anno.gen_manifest_url(version=MANIFEST_V2)
                    ):
                        return False
            elif len_line == 4:
                # if line = "x y w h"
                generated_annos += 1
    except Exception as e:
        log(
            f"[check_indexation_annos] Failed to check indexation for anno #{anno.id}",
            e,
        )
        return False

    if generated_annos != indexed_annos:
        for sas_anno_id in sas_anno_ids:
            unindex_anno(sas_anno_id)
        if reindex:
            if index_annotations(anno):
                log(f"[check_indexation_annos] Annotation #{anno.id} was reindexed")
                return True
    return True


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
        log(f"[get_anno_images] Error when retrieving annotations", e)

    return imgs
