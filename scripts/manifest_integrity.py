import json
import requests
import sys


"""
Checks that a list of manifests has the correct number of canvases
"""


def compare_manifests(manifest_url):
    with open(manifest_url, "r") as f:
        manifest = json.load(f)

    source_manifest_url = None
    for metadata in manifest["metadata"]:
        if metadata["label"] == "Source manifest":
            source_manifest_url = metadata["value"]
            break

    if source_manifest_url:
        source_manifest = fetch_manifest(source_manifest_url)
        num_canvases1 = len(manifest["sequences"][0]["canvases"])
        num_canvases2 = len(source_manifest["sequences"][0]["canvases"])

        if num_canvases1 < num_canvases2:
            print(f"{manifest} has fewer canvases than original {num_canvases1}")
            append_to_file(str(manifest), "incomplete_manifests.txt")
        elif num_canvases2 < num_canvases1:
            print(
                f"The source manifest ({source_manifest_url}) has fewer canvases: {num_canvases2}"
            )
        else:
            print("Both manifests have the same number of canvases.")
    else:
        print("No source manifest found in the metadata.")


def fetch_manifest(manifest_url):
    response = requests.get(manifest_url)
    return response.json()


def append_to_file(text, file_path="output.txt"):
    with open(file_path, "a") as file:
        file.write(text + "\n")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python compare_manifests.py manifest_list.txt")
    else:
        manifest_list_path = sys.argv[1]
        with open(manifest_list_path, "r") as f:
            manifest_list = f.read().splitlines()

        for manifest in manifest_list:
            compare_manifests(manifest)
            print()
