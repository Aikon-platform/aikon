import json
import os

from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test

from app.config.settings import SAS_APP_URL, DEBUG, SAS_USERNAME, SAS_PASSWORD
from app.webapp.templatetags.filters import jpg_to_none

from app.webapp.models.regions import Regions
from app.webapp.models.witness import Witness

from app.webapp.utils.functions import (
    credentials,
    zip_images_and_files,
    is_url,
    get_files_with_prefix,
)
from app.webapp.utils.iiif import gen_iiif_url
from app.webapp.utils.logger import log
from app.webapp.utils.iiif.annotation import formatted_annotations

from app.vectorization.const import SVG_PATH
from app.vectorization.utils import (
    vectorization_request_for_one,
    delete_and_relauch_request,
    save_svg_files,
    reset_vectorization,
)
from app.webapp.views import check_ref, is_superuser

from app.webapp.utils.iiif.annotation import (
    get_regions_annotations,
)


@csrf_exempt
def receive_vectorization(request):
    """
    Endpoint to receive a ZIP file containing SVG files and save them to the media directory.
    """
    if "file" not in request.FILES:
        return JsonResponse({"error": "No file received"}, status=400)

    file = request.FILES["file"]
    # treatment_id = request.DATA["experiment_id"]

    if file.name == "":
        return JsonResponse({"error": "File name is empty"}, status=400)

    if file and file.name.endswith(".zip"):
        try:
            temp_zip_path = default_storage.save("temp.zip", file)
            temp_zip_file = default_storage.path(temp_zip_path)

            save_svg_files(temp_zip_file)
            default_storage.delete(temp_zip_path)

            return JsonResponse(
                {"message": "Files successfully uploaded and extracted"}, status=200
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Unsupported file type"}, status=400)


@login_required
def show_crop_vectorization(request, img_file, coords, regions, canvas_nb):
    svg_filename = f"{jpg_to_none(img_file)}_{coords}.svg"
    svg_path = os.path.join(SVG_PATH, svg_filename)

    if not os.path.exists(svg_path):
        print(f"File {svg_path} not found")

    with open(svg_path, "r", encoding="utf-8") as file:
        svg_content = file.read()

    return render(
        request,
        "crop_vecto.html",
        context={
            "img_file": img_file,
            "coords": coords,
            "svg_content": svg_content,
            "regions": regions,
            "canvas_nb": canvas_nb,
        },
    )


@user_passes_test(is_superuser)
def smash_and_relaunch_vectorization(request, regions_ref):
    """
    Delete the imgs in the API from the repo corresponding to doc_id + relaunch vectorization
    """
    passed, regions = check_ref(regions_ref, "Regions")
    if not passed:
        return JsonResponse(regions)

    print(regions)
    if not regions:
        return JsonResponse(
            {"response": f"No corresponding regions in the database for {regions_ref}"},
            safe=False,
        )

    try:
        if delete_and_relauch_request(regions):
            return JsonResponse(
                {
                    "response": f"Successful smash + vectorization request for {regions_ref}"
                },
                safe=False,
            )
        return JsonResponse(
            {
                "response": f"Failed to send smash + vectorization request for {regions_ref}"
            },
            safe=False,
        )

    except Exception as e:
        error = f"[send_vectorization] Couldn't send request for {regions_ref}"
        log(error, e)

        return JsonResponse({"response": error, "reason": e}, safe=False)


@login_required
def send_vectorization(request, regions_ref):
    """
    To relaunch vectorization request in case the automatic process has failed
    """

    passed, regions = check_ref(regions_ref, "Regions")
    if not passed:
        return JsonResponse(regions)

    if not regions:
        return JsonResponse(
            {"response": f"No corresponding regions in the database for {regions_ref}"},
            safe=False,
        )

    try:
        if vectorization_request_for_one(regions):
            return JsonResponse(
                {"response": f"Successful vectorization request for {regions_ref}"},
                safe=False,
            )
        return JsonResponse(
            {"response": f"Failed to send vectorization request for {regions_ref}"},
            safe=False,
        )

    except Exception as e:
        error = f"[send_vectorization] Couldn't send request for {regions_ref}"
        log(error, e)

        return JsonResponse({"response": error, "reason": e}, safe=False)


@login_required
def show_vectorization(request, regions_ref):
    passed, regions = check_ref(regions_ref, "Regions")
    if not passed:
        return JsonResponse(regions)

    if not DEBUG:
        credentials(f"{SAS_APP_URL}/", SAS_USERNAME, SAS_PASSWORD)

    _, all_regions = formatted_annotations(regions)
    all_crops = [
        (canvas_nb, coord, img_file)
        for canvas_nb, coord, img_file in all_regions
        if coord
    ]

    paginator = Paginator(all_crops, 50)
    try:
        page_regions = paginator.page(request.GET.get("page"))
    except PageNotAnInteger:
        page_regions = paginator.page(1)
    except EmptyPage:
        page_regions = paginator.page(paginator.num_pages)

    return render(
        request,
        "show_vectorization.html",
        context={
            "regions": regions,
            "page_regions": page_regions,
            "all_crops": all_crops,
            "regions_ref": regions_ref,
        },
    )


####ClaraDev


@login_required
def export_all_images_and_svgs(request, witness_id):
    witness = get_object_or_404(Witness, id=witness_id)
    regions_list = witness.get_regions()
    return export_common_logic(regions_list)


@login_required
def export_regions_images_and_svgs(request, regions_id):
    regions = get_object_or_404(Regions, id=regions_id)
    return export_common_logic([regions])


def export_common_logic(regions_list):
    urls_list = []
    path_list = []

    for regions in regions_list:
        anno_regions = get_regions_annotations(regions, as_json=True)

        for canvas_id, regions in anno_regions.items():
            for region_id, region_data in regions.items():
                coord = region_data.get("xyhw")
                reference = region_data.get("ref")
                image = region_data.get("img")

                url = gen_iiif_url(f"{image}.jpg", 2, f"{','.join(coord)}/full/0")
                urls_list.append(url)

                vecto_path = f"{reference}.svg"
                if os.path.exists(os.path.join(SVG_PATH, vecto_path)):
                    path_list.append(vecto_path)

    return zip_images_and_files(urls_list, path_list)


@login_required
def export_selected_imgs_and_svgs(request):
    images_list = json.loads(request.POST.get("img_list"))
    urls_list = []
    paths_list = []
    for element in images_list:
        if is_url(element):
            urls_list.append(element)
        else:
            paths_list.append(element)
    return zip_images_and_files(urls_list, paths_list)


def get_vectorized_images(request, wid, rid=None):
    if rid is not None:
        q_regions = [get_object_or_404(Regions, id=rid)]
    else:
        witness = get_object_or_404(Witness, id=wid)
        q_regions = witness.get_regions()

    try:
        v_imgs = set()
        for q_r in q_regions:
            digit_ref = q_r.get_ref().split("_anno")[0]
            v_imgs.update(get_files_with_prefix(SVG_PATH, digit_ref, ext=".svg"))
        return JsonResponse(sorted(list(v_imgs)), safe=False)
    except Exception as e:
        return JsonResponse(
            {"error": f"Couldn't retrieve svg of regions #{rid}: {e}"},
            status=400,
        )


@user_passes_test(is_superuser)
def reset_regions_vectorization(request, rid=None):
    if rid:
        regions = get_object_or_404(Regions, id=rid)
        if reset_vectorization(regions):
            return JsonResponse(
                {"message": f"Regions #{rid} vectorization has been deleted"}
            )
        return JsonResponse(
            {"error": f"Regions #{rid} vectorization couldn't been deleted"}
        )

    all_regions = Regions.objects.all()
    deleted_vectorization = []
    for regions in all_regions:
        if reset_vectorization(regions):
            deleted_vectorization.append(regions.id)
    return JsonResponse(
        {
            "message": f"Regions {', '.join(map(str, deleted_vectorization))} have been deleted"
        }
    )
