import json
import threading
from os.path import exists

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth.decorators import login_required
from vhs.settings import ENV

from vhsapp.models.witness import Volume, Manuscript
from vhsapp.models.constants import MS, VOL, MS_ABBR, VOL_ABBR
from vhsapp.utils.paths import MEDIA_PATH, BASE_DIR, VOL_ANNO_PATH, MS_ANNO_PATH
from vhs.settings import VHS_APP_URL, CANTALOUPE_APP_URL, SAS_APP_URL, API_GPU_URL

from vhsapp.utils.constants import (
    APP_NAME,
    APP_NAME_UPPER,
    APP_DESCRIPTION,
    MANIFEST_AUTO,
)
from vhsapp.utils.iiif.manifest import (
    process_images,
    manifest_wit_type,
)
from vhsapp.utils.iiif.annotation import (
    get_txt_annos,
    format_canvas_annos,
    index_wit_annotations,
    get_anno_img,
    formatted_wit_anno,
    # index_anno,
    get_canvas_list,
    get_indexed_canvas_annos,
    check_anno_file,
    check_wit_annos,
)
from vhsapp.utils.functions import (
    console,
    log,
    get_time,
    read_json_file,
    write_json_file,
    get_imgs,
    get_img_prefix,
    credentials,
    list_to_txt,
    credentials,
)
import requests


def admin_vhs(request):
    return redirect("admin:index")


def manifest_manuscript(request, wit_id, version):
    """
    Build a manuscript manifest using iiif-prezi library IIIF Presentation API 2.0
    """
    return JsonResponse(manifest_wit_type(wit_id, MS, version))


def manifest_volume(request, wit_id, version):
    """
    Build a volume manifest using iiif-prezi library IIIF Presentation API 2.0
    """
    return JsonResponse(manifest_wit_type(wit_id, VOL, version))


def send_anno(request, wit_id, wit_type):
    """
    To relaunch annotations in case the automatic annotation failed
    """
    wit_abbr = MS_ABBR if wit_type == MS else VOL_ABBR
    manifest_url = f"{VHS_APP_URL}/{APP_NAME}/iiif/{MANIFEST_AUTO}/{wit_type}/{wit_id}/manifest.json"
    try:
        requests.post(
            url=f"{GPU_URL}/run_detect",
            data={"manifest_url": manifest_url, "wit_abbr": wit_abbr},
        )
    except Exception as e:
        log(
            f"[send_anno] Failed to send annotation request for {wit_type} #{wit_id}: {e}"
        )
        return JsonResponse(
            {
                "response": f"Failed to send annotation request for {wit_type} #{wit_id}",
                "cause": e,
            },
            safe=False,
        )

    return JsonResponse(
        {"response": f"Annotations were relaunched for {wit_type} #{wit_id}"},
        safe=False,
    )


@csrf_exempt
def receive_anno(request, wit_id, wit_type):
    if request.method == "POST":
        # TODO: vérification du format des annotations reçues
        annotation_file = request.FILES["annotation_file"]
        file_content = annotation_file.read()

        if check_anno_file(file_content):
            anno_path = f"{BASE_DIR}/{MEDIA_PATH}/{MS_ANNO_PATH if wit_type == 'manuscript' else VOL_ANNO_PATH}"
            try:
                with open(f"{anno_path}/{wit_id}.txt", "w+b") as f:
                    f.write(file_content)

            except Exception as e:
                log(
                    f"[receive_anno] Failed to open received annotations for {wit_type} #{wit_id}: {e}"
                )

            # manifest_url = (
            #     f"{VHS_APP_URL}/{APP_NAME}/iiif/v2/{wit_type}/{wit_id}/manifest.json"
            # )
            try:
                index_wit_annotations(wit_id, wit_type)
                # index_anno(manifest_url, wit_type, wit_id)
            except Exception as e:
                log(
                    f"[receive_anno] Failed to index annotations for {wit_type} #{wit_id}: {e}"
                )

            return JsonResponse({"message": "Annotation received and indexed."})

        else:
            return JsonResponse(
                {"message": "Invalid request. File is not a text file."}, status=400
            )
    else:
        return JsonResponse({"message": "Invalid request."}, status=400)


def export_anno_img(request, wit_id, wit_type):
    annotations = get_anno_img(wit_id, wit_type)
    return list_to_txt(annotations, f"{wit_type}#{wit_id}_annotations")


def canvas_annotations(request, wit_id, version, wit_type, canvas):
    return JsonResponse(format_canvas_annos(wit_id, version, wit_type, canvas))


def populate_annotation(request, wit_id, wit_type):
    """
    Populate annotation store from IIIF Annotation List
    """
    if not ENV("DEBUG"):
        credentials(f"{SAS_APP_URL}/", ENV("SAS_USERNAME"), ENV("SAS_PASSWORD"))

    return HttpResponse(status=200 if index_wit_annotations(wit_id, wit_type) else 500)


def validate_annotation(request, wit_id, wit_type):
    """
    Validate the manually corrected annotations
    """
    try:
        witness = get_object_or_404(
            Volume if wit_type == VOL else Manuscript, pk=wit_id
        )
        witness.manifest_final = True
        witness.save()
        return HttpResponse(status=200)
    except (Manuscript.DoesNotExist, Volume.DoesNotExist):
        return HttpResponse(f"{wit_type} #{wit_id} does not exist", status=500)
    except Exception as e:
        return HttpResponse(f"An error occurred: {e}", status=500)


def witness_sas_annotations(request, wit_id, wit_type):
    witness = get_object_or_404(Volume if wit_type == VOL else Manuscript, pk=wit_id)
    _, canvas_annos = formatted_wit_anno(witness, wit_type)
    return JsonResponse(canvas_annos, safe=False)


def test(request, wit_id, wit_type):
    start = get_time()
    model = Volume if wit_type == VOL else Manuscript
    try:
        wit_id = int(wit_id)
        if int(wit_id) == 0:
            witnesses = model.objects.all()
        else:
            witnesses = [get_object_or_404(model, pk=wit_id)]
    except ValueError as e:
        console(f"[test] wit_id is not an integer: {e}")
        return JsonResponse(
            {"response": f"wit_id is not an integer: {wit_id}\n{e}"},
            safe=False,
        )

    threads = []
    wit_ids = []
    for witness in witnesses:
        if not witness.manifest_final:
            wit_ids.append(witness.id)
            thread = threading.Thread(
                target=check_wit_annos, args=(witness.id, wit_type, True)
            )
            thread.start()
            threads.append(thread)
    # for thread in threads:
    #     thread.join()

    return JsonResponse(
        {"response": f"Execution time: {start} > {get_time()}", "checked ids": wit_ids},
        safe=False,
    )


@login_required(login_url=f"/{APP_NAME}-admin/")
def show_witness(request, wit_id, wit_type):
    witness = get_object_or_404(Volume if wit_type == VOL else Manuscript, pk=wit_id)

    if not ENV("DEBUG"):
        credentials(f"{SAS_APP_URL}/", ENV("SAS_USERNAME"), ENV("SAS_PASSWORD"))

    bboxes, canvas_annos = formatted_wit_anno(witness, wit_type)

    paginator = Paginator(canvas_annos, 50)
    try:
        page_annos = paginator.page(request.GET.get("page"))
    except PageNotAnInteger:
        page_annos = paginator.page(1)
    except EmptyPage:
        page_annos = paginator.page(paginator.num_pages)

    return render(
        request,
        "vhsapp/show.html",
        context={
            "wit_type": wit_type,
            "wit_obj": witness,
            "page_annos": page_annos,
            "bboxes": json.dumps(bboxes),
            "url_manifest": f"{VHS_APP_URL}/{APP_NAME}/iiif/v2/{wit_type}/{wit_id}/manifest.json",
        },
    )


# TODO: create test to find integrity of a manuscript:
#  if it has the correct number of images, if all its images are img files
#  if annotations were correctly defined (same img name in file that images on server)
