import json
import os
import zipfile

from django.core.files.storage import default_storage

from django.http import JsonResponse
from django.shortcuts import render
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth.decorators import login_required, user_passes_test

from app.config.settings import SAS_APP_URL, APP_NAME, DEBUG, SAS_USERNAME, SAS_PASSWORD
from app.webapp.filters import jpg_to_none

from app.webapp.utils.functions import (
    credentials,
    zip_images_and_files,
    is_url,
)
from app.webapp.utils.iiif import gen_iiif_url
from app.webapp.utils.logger import log
from app.webapp.utils.iiif.annotation import formatted_annotations

from app.vectorization.const import SVG_PATH
from app.vectorization.utils import (
    vectorization_request_for_one,
    delete_and_relauch_request,
)
from app.webapp.views import check_ref, is_superuser


def save_svg_files(zip_file):
    """
    Dézippe un fichier ZIP contenant des fichiers SVG et les enregistre dans le répertoire de médiafiles.

    :param zip_file: Fichier ZIP reçu de l'API
    """
    # Vérifie si le répertoire SVG_PATH existe, sinon le crée
    if not os.path.exists(SVG_PATH):
        os.makedirs(SVG_PATH)

    with zipfile.ZipFile(zip_file, "r") as zip_ref:
        for file_info in zip_ref.infolist():
            # Vérifie si le fichier est un fichier SVG
            if file_info.filename.endswith(".svg"):
                file_path = os.path.join(SVG_PATH, os.path.basename(file_info.filename))

                # Supprime le fichier existant s'il y en a un
                if os.path.exists(file_path):
                    os.remove(file_path)

                # Extrait le fichier SVG et l'écrit dans le répertoire spécifié
                with zip_ref.open(file_info) as svg_file:
                    with open(file_path, "wb") as output_file:
                        output_file.write(svg_file.read())


@csrf_exempt
def receive_vectorization(request):
    """
    Vue pour recevoir un fichier ZIP via une requête POST.
    """
    if "file" not in request.FILES:
        return JsonResponse({"error": "aucun fichier reçu"}, status=400)

    file = request.FILES["file"]

    if file.name == "":
        return JsonResponse({"error": "No selected file"}, status=400)

    if file and file.name.endswith(".zip"):
        try:
            # Sauvegarde temporairement le fichier ZIP reçu
            temp_zip_path = default_storage.save("temp.zip", file)
            temp_zip_file = default_storage.path(temp_zip_path)

            # Dézippe et enregistre les fichiers SVG
            save_svg_files(temp_zip_file)

            # Supprime le fichier ZIP temporaire
            default_storage.delete(temp_zip_path)

            return JsonResponse(
                {"message": "Files successfully uploaded and extracted"}, status=200
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Unsupported file type"}, status=400)


@login_required(login_url=f"/{APP_NAME}-admin/login/")
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
def smash_and_relauch_vectorization(request, regions_ref):
    """
    delete the imgs in the API from the repo corresponding to doc_id + relauch vectorization
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


@login_required(login_url=f"/{APP_NAME}-admin/login/")
def send_vectorization(request, regions_ref):
    """
    Send vectorization request from the witness info template
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


@login_required(login_url=f"/{APP_NAME}-admin/login/")
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


@login_required(login_url=f"/{APP_NAME}-admin/login/")
def export_all_images_and_svgs(request, regions_ref):
    passed, regions = check_ref(regions_ref, "Regions")
    if not passed:
        return JsonResponse(regions)

    if not DEBUG:
        credentials(f"{SAS_APP_URL}/", SAS_USERNAME, SAS_PASSWORD)

    urls_list = []
    path_list = []

    _, all_regions = formatted_annotations(regions)
    all_crops = [
        (canvas_nb, coord, img_file)
        for canvas_nb, coord, img_file in all_regions
        if coord
    ]

    for canvas_nb, coord, img_file in all_crops:
        urls_list.extend(gen_iiif_url(img_file, 2, f"{c[0]}/full/0") for c in coord)
        vecto_path = f"{img_file[:-4]}_{''.join(c[0] for c in coord)}.svg"
        # Vérifie si le chemin existe
        if os.path.exists(os.path.join(SVG_PATH, vecto_path)):
            path_list.append(vecto_path)

    return zip_images_and_files(urls_list, path_list)


@login_required(login_url=f"/{APP_NAME}-admin/login/")
def export_selected_imgs_and_svgs(request):
    images_list = json.loads(request.POST.get("liste_images"))
    urls_list = []
    paths_list = []
    for element in images_list:
        if is_url(element):
            urls_list.append(element)
        else:
            paths_list.append(element)
    return zip_images_and_files(urls_list, paths_list)
