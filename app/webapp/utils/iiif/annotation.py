import json
import re
from datetime import datetime
from urllib.parse import urlencode
from urllib.request import urlopen

import requests
from PIL import Image

from app.webapp.models.regions import Regions, get_name
from app.webapp.models.digitization import Digitization

from app.webapp.utils.constants import MANIFEST_V2, MANIFEST_V1
from app.config.settings import (
    CANTALOUPE_APP_URL,
    SAS_APP_URL,
    APP_NAME,
    APP_URL,
    ADDITIONAL_MODULES,
)
from app.webapp.utils.functions import log, get_img_nb_len, gen_img_ref, flatten_dict
from app.webapp.utils.iiif import parse_ref, gen_iiif_url, region_title
from app.webapp.utils.paths import REGIONS_PATH, IMG_PATH
from app.webapp.utils.regions import get_txt_regions

IIIF_CONTEXT = "http://iiif.io/api/presentation/2/context.json"


def get_manifest_annotations(
    regions_ref, only_ids=True, min_c: int = None, max_c: int = None
):
    manifest_annotations = []
    next_page = f"{SAS_APP_URL}/search-api/{regions_ref}/search"

    while next_page:
        try:
            response = requests.get(next_page)
            annotations = response.json()

            if response.status_code != 200:
                log(
                    f"[get_manifest_annotations] Failed to get annotations from SAS for {regions_ref}: {response.status_code}"
                )
                return []

            resources = annotations.get("resources", [])
            if not resources:
                break

            # if only a certain range is needed (do not work because the annotations are sorted alphabetically by canvas number)
            # TODO change the SAS code to add canvas number in the annotation metadata
            #  AND/OR sort the annotations by canvas number
            # if min_c is not None:
            #     first_canvas = int(
            #         resources[0]["on"].split("/canvas/c")[1].split(".json")[0]
            #     )
            #     last_canvas = int(
            #         resources[-1]["on"].split("/canvas/c")[1].split(".json")[0]
            #     )
            #
            #     if max_c is not None and first_canvas > max_c:
            #         break
            #
            #     # Skip this page if the entire range is outside min_c and max_c
            #     if last_canvas < min_c:
            #         next_page = annotations.get("next")
            #         continue

            if only_ids:
                manifest_annotations.extend(
                    annotation["@id"] for annotation in annotations["resources"]
                )
            else:
                manifest_annotations.extend(annotations["resources"])

            next_page = annotations.get("next")

        except requests.exceptions.RequestException as e:
            log(
                f"[get_manifest_annotations] Failed to retrieve annotations for {next_page}",
                e,
            )
            return []
        except Exception as e:
            log(
                f"[get_manifest_annotations] Failed to parse annotations for {next_page}",
                e,
            )
            return []

    return manifest_annotations


def get_regions_annotations(
    regions: Regions, as_json=False, r_annos=None, min_c: int = None, max_c: int = None
):
    # TODO improve efficiency: too slow for witness with a lot of annotations (because it parse all annotations)
    if r_annos is None:
        r_annos = {} if as_json else []

    regions_ref = regions.get_ref()
    annos = get_manifest_annotations(regions_ref, False, min_c, max_c)
    if len(annos) == 0:
        return r_annos

    img_name = regions_ref.split("_anno")[0]
    nb_len = get_img_nb_len(img_name)

    if as_json:
        min_c = min_c or 1
        max_c = max_c or regions.get_json()["img_nb"]
        r_annos = {str(c): {} for c in range(min_c, max_c)}

    for anno in annos:
        try:
            on_value = anno["on"]
            canvas = on_value.split("/canvas/c")[1].split(".json")[0]
            try:
                canvas_num = int(canvas)
            except ValueError:
                log(
                    f"[get_regions_annotations] Failed to parse canvas value '{canvas}' for annotation {on_value}"
                )
                continue

            # Stop once max_c is reached
            # DO NOT WORK since the annotations are sorted ALPHABETICALLY by canvas number
            # if max_c is not None and (canvas_num > max_c):
            #     break

            if (max_c is not None and canvas_num > max_c) or (
                min_c is not None and canvas_num < min_c
            ):
                continue

            if canvas not in r_annos:
                log(
                    f"[get_regions_annotations] Key '{canvas}' should be included between {min_c}-{max_c} => pass"
                )
                continue

            xyhw = on_value.split("xywh=")[1]
            if as_json:
                img = f"{img_name}_{canvas.zfill(nb_len)}"
                aid = anno["@id"].split("/")[-1]

                r_annos[canvas][aid] = {
                    "id": aid,
                    "ref": f"{img}_{xyhw}",
                    "class": "Region",
                    "type": get_name("Regions"),
                    "title": region_title(canvas, xyhw),
                    "url": gen_iiif_url(img, res=f"{xyhw}/full/0"),
                    "canvas": canvas,
                    "xyhw": xyhw.split(","),
                    "img": img,
                }
            else:
                r_annos.append((canvas, xyhw, f"{img_name}_{canvas.zfill(nb_len)}"))
        except Exception as e:
            log(f"[get_regions_annotations]: Failed to parse annotation {anno}", e)
            continue

    return r_annos


# def get_regions_annotations(
#     regions: Regions, as_json=False, r_annos=None, min_c: int = None, max_c: int = None
# ) -> Dict[str, Dict] | List[Tuple[str, str, str]]:
#
#     regions_ref = regions.get_ref()
#     img_name = regions_ref.split("_anno")[0]
#     nb_len = get_img_nb_len(img_name)
#
#     if r_annos is None:
#         r_annos = {} if as_json else []
#
#     if as_json:
#         min_c = min_c or 1
#         max_c = max_c or regions.get_json()["img_nb"]
#         r_annos = {str(c): {} for c in range(min_c, max_c)}
#
#     def process_page(p_url: str) -> List[Dict]:
#         try:
#             res = requests.get(p_url)
#             if res.status_code != 200:
#                 log(
#                     f"[get_regions_annotations] Failed to get annotations from SAS for {p_url}: {res.status_code}"
#                 )
#                 return []
#             return res.json().get("resources", [])
#         except Exception as e:
#             log(
#                 f"[get_regions_annotations] Failed to retrieve or parse annotations for {p_url}",
#                 e,
#             )
#             return []
#
#     def process_annotation(anno: Dict) -> Optional[Tuple[str, Dict | Tuple]]:
#         try:
#             on_value = anno["on"]
#             c = on_value.split("/canvas/c")[1].split(".json")[0]
#             canvas_num = int(c)
#
#             if (max_c is not None and canvas_num > max_c) or (
#                 min_c is not None and canvas_num < min_c
#             ):
#                 return None
#
#             xyhw = on_value.split("xywh=")[1]
#             img = f"{img_name}_{c.zfill(nb_len)}"
#
#             if as_json:
#                 aid = anno["@id"].split("/")[-1]
#                 return c, {
#                     aid: {
#                         "id": aid,
#                         "ref": f"{img}_{xyhw}",
#                         "class": "Region",
#                         "type": get_name("Regions"),
#                         "title": region_title(c, xyhw),
#                         "url": gen_iiif_url(img, res=f"{xyhw}/full/0"),
#                         "canvas": c,
#                         "xyhw": xyhw.split(","),
#                         "img": img,
#                     }
#                 }
#             return c, (c, xyhw, img)
#         except Exception as e:
#             log(f"[get_regions_annotations]: Failed to parse annotation {anno}", e)
#             return None
#
#     with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
#         next_page = f"{SAS_APP_URL}/search-api/{regions_ref}/search"
#         future_to_url = {executor.submit(process_page, next_page): next_page}
#
#         while True:
#             done, _ = concurrent.futures.wait(
#                 future_to_url, return_when=concurrent.futures.FIRST_COMPLETED
#             )
#             for future in done:
#                 page_url = future_to_url[future]
#                 annotations = future.result()
#
#                 annotation_futures = list(executor.map(process_annotation, annotations))
#                 for result in annotation_futures:
#                     if result:
#                         canvas, data = result
#                         if as_json:
#                             try:
#                                 r_annos[canvas].update(data)
#                             except Exception as e:
#                                 log(
#                                     f"[get_regions_annotations] {canvas} exceeds {min_c}-{max_c}",
#                                     e,
#                                 )
#                                 r_annos[canvas] = {}
#                                 r_annos[canvas].update(data)
#                         else:
#                             r_annos.append(data)
#
#                 del future_to_url[future]
#
#                 response = requests.get(page_url)
#                 next_page = response.json().get("next")
#                 if next_page:
#                     future_to_url[executor.submit(process_page, next_page)] = next_page
#
#             if not future_to_url:
#                 break
#     return r_annos


def index_regions(regions: Regions):
    if not index_manifest_in_sas(regions.gen_manifest_url(version=MANIFEST_V2), True):
        return

    canvases_to_annotate = get_annotations_per_canvas(regions)
    if not bool(canvases_to_annotate):
        # if the annotation file is empty
        return True

    for c in canvases_to_annotate:
        try:
            index_annotations_on_canvas(regions, c)
        except Exception as e:
            log(
                f"[index_regions] Problem indexing region #{regions.id} (canvas {c})",
                e,
            )

    return True


def reindex_file(filename):
    a_ref = filename.replace(".txt", "")
    ref = parse_ref(a_ref)
    if not ref or not ref["regions"]:
        # if there is no regions_id in the ref, pass
        return False, a_ref
    regions_id = ref["regions"][1]
    regions = Regions.objects.filter(pk=regions_id).first()
    if not regions:
        digit = Digitization.objects.filter(pk=ref["digit"][1]).first()
        if not digit:
            # if there is no digit corresponding to the ref, pass
            return False, a_ref
        # create new Regions record if none existing
        regions = Regions(id=regions_id, digitization=digit, model="CHANGE THIS VALUE")
        regions.save()

    from app.webapp.tasks import reindex_from_file

    reindex_from_file.delay(regions_id)
    return True, a_ref


def unindex_annotation(annotation_id):
    http_sas = SAS_APP_URL.replace("https", "http")

    # annotation_id = f"{wit_abbr}{wit_id}_{digit_abbr}{digit_id}_anno{regions_id}_c{canvas_nb}_{uuid4().hex[:8]}
    delete_url = (
        f"{SAS_APP_URL}/annotation/destroy?uri={http_sas}/annotation/{annotation_id}"
    )
    try:
        response = requests.delete(delete_url)
        if response.status_code == 204:
            return True
        else:
            log(
                f"[unindex_annotation] Unindex annotation request failed with status code: {response.status_code}"
            )
    except requests.exceptions.RequestException as e:
        log(f"[unindex_annotation] Unindex annotation request failed", e)
    return False


def index_annotations_on_canvas(regions: Regions, canvas_nb):
    # this url (view canvas_annotations()) is calling format_canvas_annotations(),
    # thus returning formatted annotations for each canvas
    formatted_annos = f"{APP_URL}/{APP_NAME}/iiif/{MANIFEST_V2}/{regions.get_ref()}/list/anno-{canvas_nb}.json"
    # POST request that index the annotations
    response = urlopen(
        f"{SAS_APP_URL}/annotation/populate",
        urlencode({"uri": formatted_annos}).encode("ascii"),
    )

    if response.status != 201:
        log(
            f"[index_annotations_on_canvas] Failed to index annotations. Status: {response.status_code}",
            response.text,
        )
        return


def get_annotations_per_canvas(region: Regions, last_canvas=0, specific_canvas=""):
    """
    Returns a dict with the text annotation file info:
    { "canvas1": [ coord1, coord2 ], "canvas2": [], "canvas3": [ coord1 ] }

    if specific_canvas, returns [ coord1, coord2 ]

    coord = (x, y, width, height)
    """
    lines = get_txt_regions(region)
    if lines is None:
        log(f"[get_annotations_per_canvas] No annotation file for Regions #{region.id}")
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


def format_annotation(regions: Regions, canvas_nb, xywh):
    base_url = regions.gen_manifest_url(only_base=True, version=MANIFEST_V2)
    x, y, w, h = xywh

    width = w // 2
    height = h // 2

    annotation_id = regions.gen_annotation_id(canvas_nb)
    d = f"M{x} {y} h {width} v 0 h {width} v {height} v {height} h -{width} h -{width} v -{height}Z"
    r_id = f"rectangle_{annotation_id}"
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
        "@id": f"{SAS_APP_URL.replace('https', 'http')}/annotation/{annotation_id}",
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
        "@context": IIIF_CONTEXT,
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
    annotation = canvas.annotation(ident=f"a{canvas_nb}")
    if re.match(r"https?://(.*?)/", img_name):
        # to build hybrid manifest referencing images from other IIIF repositories
        img = annotation.image(img_name, iiif=False)
        setattr(img, "format", "image/jpeg")
    else:
        img = annotation.image(ident=img_name, iiif=True)

    img.set_hw(h, w)
    # In case we do not really index "automatic" annotations but keep them as "otherContents"
    if version == MANIFEST_V1:
        # is calling f"{APP_NAME}/iiif/{version}/{anno.get_ref()}/list/anno-{canvas_nb}.json"
        # (canvas_annotations() view) that returns formatted annotations format_canvas_annotations()
        annotation_list = canvas.annotationList(ident=f"anno-{canvas_nb}")
        annotation = annotation_list.annotation(ident=f"a-list-{canvas_nb}")
        annotation.text("Annotation")


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
        print(r)
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


def get_canvas_list(regions: Regions, all_img=False):
    imgs = regions.get_imgs()
    if all_img:
        # Display all images associated to the digitization, even if no regions were extracted
        return [(int(img.split("_")[-1].split(".")[0]), img) for img in imgs]

    lines = get_txt_regions(regions)
    if not lines:
        log(f"[get_canvas_list] No regions file for regions #{regions.id}")
        return {
            "error": "the regions file was not yet generated"
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
    for regions in digit.get_regions():
        canvases.extend(get_canvas_list(regions, all_img))
    return canvases


def get_indexed_annotations(regions: Regions):
    # not used
    annotations = {}
    for canvas_nb, _ in get_canvas_list(regions):
        annotations[canvas_nb] = get_indexed_canvas_annotations(regions, canvas_nb)
    return annotations


def get_indexed_canvas_annotations(regions: Regions, canvas_nb):
    try:
        response = urlopen(
            f"{SAS_APP_URL}/annotation/search?uri={regions.gen_manifest_url(only_base=True, version=MANIFEST_V2)}/canvas/c{canvas_nb}.json"
        )
        return json.loads(response.read())
    except Exception as e:
        log(
            f"[get_indexed_canvas_annotations] Could not retrieve annotation for regions #{regions.id}",
            e,
        )
        return []


def get_coord_from_annotation(sas_annotation):
    try:
        # coord => "x,y,w,h"
        coord = (sas_annotation["on"][0]["selector"]["default"]["value"]).split("=")[1]
        # remove negative values if some of the coordinates exceed the image boundaries
        return ",".join(["0" if int(num) < 0 else num for num in coord.split(",")])
    except Exception as e:
        log(
            f"[get_coord_from_annotation] Could not retrieve coord from SAS annotation",
            e,
        )
        return "0,0,0,0"


def get_id_from_annotation(sas_annotation):
    try:
        # annotation_id => "{wit_abbr}{wit_id}_{digit_abbr}{digit_id}_anno{regions_id}_c{canvas_nb}_{uuid4().hex[:8]}"
        return sas_annotation["@id"].split("/")[-1]
    except Exception as e:
        log(f"[get_id_from_annotation] Could not retrieve id from SAS annotation", e)
        return ""


def formatted_annotations(regions: Regions):
    canvas_annotations = []
    annotation_ids = []

    try:
        for canvas_nb, img_file in get_canvas_list(regions):
            c_annotations = get_indexed_canvas_annotations(regions, canvas_nb)
            coord_annotations = []

            if bool(c_annotations):
                coord_annotations = [
                    (
                        get_coord_from_annotation(sas_anno),
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


def total_annotations(regions: Regions):
    response = requests.get(f"{SAS_APP_URL}/search-api/{regions.get_ref()}/search")
    res = response.json()
    try:
        return res["within"]["total"]
    except KeyError:
        total_sas_anno_count = 0

        try:
            for canvas_nb, _ in get_canvas_list(regions):
                c_annotations = get_indexed_canvas_annotations(regions, canvas_nb)
                total_sas_anno_count += len(c_annotations)
        except ValueError as e:
            log(
                f"[count_total_annotations] Error when counting annotations (probably no annotation file)",
                e,
            )

        return total_sas_anno_count


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


def check_indexation(regions: Regions, reindex=False):
    """
    Check if the number of generated annotations is the same as the number of indexed annotations
    If not, unindex all annotations and (if reindex=True) reindex the regions
    """
    lines = get_txt_regions(regions)

    if not lines:
        return False

    if not index_manifest_in_sas(regions.gen_manifest_url(version=MANIFEST_V2)):
        return False

    generated_annotations = 0
    indexed_annotations = 0

    sas_annotations_ids = []
    try:
        for line in lines:
            line_el = line.split()
            if len(line_el) == 2:
                # if line = "canvas_nb img_name"
                canvas_nb = line_el[0]
                sas_annotations = get_indexed_canvas_annotations(regions, canvas_nb)
                nb_annotations = len(sas_annotations)

                if nb_annotations != 0:
                    indexed_annotations += nb_annotations
                    sas_annotations_ids.extend(
                        [
                            get_id_from_annotation(sas_annotation)
                            for sas_annotation in sas_annotations
                        ]
                    )
                else:
                    if not index_manifest_in_sas(
                        regions.gen_manifest_url(version=MANIFEST_V2)
                    ):
                        return False
            elif len(line_el) == 4:
                # if line = "x y w h"
                generated_annotations += 1
    except Exception as e:
        log(
            f"[check_indexation] Failed to check indexation for regions #{regions.id}",
            e,
        )
        return False

    if generated_annotations != indexed_annotations:
        for sas_annotation_id in sas_annotations_ids:
            unindex_annotation(sas_annotation_id)
        if reindex:
            if index_regions(regions):
                log(f"[check_indexation] Regions #{regions.id} were reindexed")
                return True
    return True


def get_images_annotations(regions: Regions):
    # Used to export images annotations
    imgs = []

    try:
        for canvas_nb, img_file in get_canvas_list(regions):
            c_annotations = get_indexed_canvas_annotations(regions, canvas_nb)

            if bool(c_annotations):
                canvas_imgs = [
                    f"{CANTALOUPE_APP_URL}/iiif/2/{img_file}/{get_coord_from_annotation(sas_annotation)}/full/0/default.jpg"
                    for sas_annotation in c_annotations
                ]
                imgs.extend(canvas_imgs)
    except ValueError as e:
        log(f"[get_images_annotations] Error when retrieving SAS annotations", e)

    return imgs


# def unindex_manifest(regions: Regions):
#     # DO NOT WORK
#     response = requests.delete(f"{SAS_APP_URL}/manifests/{regions.get_ref()}")
#     if response.status_code != 200:
#         log(
#             f"[unindex_manifest] Failed to un-index manifest for Regions #{regions.id}. "
#             f"Status code: {response.status_code} / {response.text}"
#         )
#         return False
#     return True


def unindex_regions(regions_ref, manifest_url):
    index_manifest_in_sas(manifest_url)
    sas_annotation_id = 0
    try:
        for sas_annotation in get_manifest_annotations(regions_ref):
            sas_annotation_id = sas_annotation.split("/")[-1]
            unindex_annotation(sas_annotation_id)
    except Exception as e:
        log(
            f"[delete_regions] Failed to unindex SAS annotation #{sas_annotation_id}", e
        )
        return False

    return True


def delete_regions(regions: Regions):
    manifest_url = regions.gen_manifest_url(version=MANIFEST_V2)
    regions_ref = regions.get_ref()

    if "similarity" in ADDITIONAL_MODULES:
        from app.similarity.utils import delete_pairs_with_regions

        delete_pairs_with_regions(regions.id)

    try:
        # Delete the regions record in the database
        regions.delete()
    except Exception as e:
        log(f"[delete_regions] Failed to delete regions record #{regions.id}", e)
        return False

    # Remove all annotations associated with this record
    return unindex_regions(regions_ref, manifest_url)


def get_training_regions(regions: Regions):
    # Returns a list of tuples [(file_name, file_content), (...)]
    filenames_contents = []
    for canvas_nb, img_file in get_canvas_list(regions):
        sas_annotations = get_indexed_canvas_annotations(regions, canvas_nb)
        img = Image.open(f"{IMG_PATH}/{img_file}")
        width, height = img.size
        if bool(sas_annotations):
            train_regions = []
            for sas_annotation in sas_annotations:
                x, y, w, h = [
                    int(n) for n in get_coord_from_annotation(sas_annotation).split(",")
                ]
                train_regions.append(
                    f"0 {((x + x + w) / 2) / width} {((y + y + h) / 2) / height} {w / width} {h / height}"
                )

            filenames_contents.append(
                (f"{img_file}".replace(".jpg", ".txt"), "\n".join(train_regions))
            )
    return filenames_contents


def process_regions(regions_file_content, digit, model="Unknown model"):
    # treatment = Treatment.objects.filter(pk=treatment_id).first()

    try:
        # TODO add step to check if regions weren't generated before for the same model
        regions = Regions.objects.create(digitization=digit, model=model)
    except Exception as e:
        log(
            f"[process_regions] Failed to create regions record for digit #{digit.id}",
            e,
        )
        return False

    try:
        with open(f"{REGIONS_PATH}/{regions.get_ref()}.txt", "w+b") as f:
            f.write(regions_file_content.encode("utf-8"))
    except Exception as e:
        # treatment.error_treatment(e)
        log(
            f"[process_regions] Failed to save received regions file for digit #{digit.id}",
            e,
        )
        return False

    try:
        index_regions(regions)
    except Exception as e:
        # treatment.error_treatment(e)
        log(f"[process_regions] Failed to index regions for digit #{digit.id}", e)
        return False

    # treatment.complete_treatment(regions.get_ref())
    return True


def get_regions_urls(regions: Regions):
    """
    {
        "wit1_man191_0009_166,1325,578,516": ""https://eida.obspm.fr/iiif/2/wit1_man191_0009.jpg/166,1325,578,516/full/0/default.jpg"",
        "wit1_man191_0027_1143,2063,269,245": "https://eida.obspm.fr/iiif/2/wit1_man191_0027.jpg/1143,2063,269,245/full/0/default.jpg",
        "wit1_man191_0031_857,2013,543,341": "https://eida.obspm.fr/iiif/2/wit1_man191_0031.jpg/857,2013,543,341/full/0/default.jpg",
        "img_name": "..."
    }
    """
    folio_regions = []

    _, canvas_annotations = formatted_annotations(regions)
    for canvas_nb, annotations, img_name in canvas_annotations:
        if len(annotations):
            folio_regions.append(
                {
                    gen_img_ref(img_name, a[0]): gen_iiif_url(
                        img_name, 2, f"{a[0]}/full/0"
                    )
                    for a in annotations
                }
            )

    return flatten_dict(folio_regions)
