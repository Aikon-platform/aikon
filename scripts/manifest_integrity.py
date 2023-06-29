import json
from os.path import exists

import requests
import sys


"""
Checks that a list of manifests has the correct number of canvases
"""

output_file = "incomplete_manifests.txt"


def compare_manifests(manifest_url):
    manifest = fetch_manifest(manifest_url)
    if manifest is None:
        return

    app_id = get_app_id(manifest_url)

    source_manifest_url = None
    try:
        for metadata in manifest["metadata"]:
            if metadata["label"] == "Source manifest":
                source_manifest_url = metadata["value"]
                break
    except KeyError as e:
        append_to_file(f"🛑 {app_id}", "no_manifests.txt")
        print(f"🛑 Non existing metadata for {app_id}: {e}")
        return

    if source_manifest_url:
        source_manifest = fetch_manifest(source_manifest_url)
        if source_manifest is None:
            return

        try:
            num_canvases1 = len(manifest["sequences"][0]["canvases"])
            num_canvases2 = len(source_manifest["sequences"][0]["canvases"])
        except KeyError as e:
            print(f"🛑 Non existing sequences or canvases for {app_id}: {e}")
            return

        if num_canvases1 < num_canvases2:
            print(
                f"💩 {app_id} has fewer canvases than original: {num_canvases1} < {num_canvases2}"
            )
            append_to_file(f"{app_id}: {num_canvases1} < {num_canvases2}", output_file)
            if "gallica" in source_manifest_url:
                append_to_file(
                    f"{app_id} {source_manifest_url} {num_canvases1 - 1}", "gallica.txt"
                )
        elif num_canvases2 < num_canvases1:
            print(
                f"👽 {app_id}: The source manifest ({source_manifest_url}) has fewer canvases: {num_canvases2} < {num_canvases1}"
            )
        else:
            append_to_file(manifest_url, "complete_manifests.txt")
            print(
                f"👌 {app_id}: Both manifests have the same number of canvases: {num_canvases1}."
            )
    else:
        append_to_file(manifest_url, "complete_manifests.txt")
        print(f"👌 {app_id}: No source manifest found in the metadata.")


def fetch_manifest(manifest_url):
    try:
        response = requests.get(manifest_url)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"🛑 Non existing manifest for {get_app_id(manifest_url)}: {e}")
    except json.JSONDecodeError as e:
        print(f"🛑 Invalid JSON in the manifest for {get_app_id(manifest_url)}: {e}")
    except Exception as e:
        print(f"🛑 Other error for {get_app_id(manifest_url)}: {e}")
    return None


def get_app_id(manifest_url):
    return manifest_url.replace(
        f"https://eida.obspm.fr/eida/iiif/auto/manuscript/", ""
    ).replace("/manifest.json", "")


def append_to_file(text, file_path="output.txt"):
    with open(file_path, "a") as file:
        file.write(text + "\n")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python manifest_integrity.py manifest_list.txt")
    else:
        manifest_list_path = sys.argv[1]
        if exists(output_file):
            open(output_file, "w").close()

        with open(manifest_list_path, "r") as f:
            manifest_list = f.read().splitlines()

        for manifest in manifest_list:
            compare_manifests(manifest)
            print()
