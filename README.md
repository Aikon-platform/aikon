# <img alt="Aikon logo" src="https://github.com/Aikon-platform/aikon/blob/main/app/webapp/static/favicon.ico" height="50" width="auto" style="display: inline; margin-bottom:-10px;"> AIKON bundle version

This is a bundle version of the AIKON platform : a tool for humanities scholars leveraging artificial intelligence and computer vision methods for analyzing large-scale heritage collections.

[About the AIKON platform](https://aikon-platform.github.io/)

This repo contains the code for the platform + the worker API, allowing the whole to be easily installed and run on your local machine.

## General requirements

> - **Sudo** privileges
> - **Python** >= 3.10
> - **Git**:
>     - `sudo apt install git`
>     - Having configured [SSH access to GitHub](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)

## Install 🛠️

Please refer to [front/README](https://github.com/Aikon-platform/discover-api/blob/main/README.md) and [api/README](front/README.md) for detailed instructions (especially step-by-step install).

1. To install the API and Front application inside the `front` and `api` folders, run:
    ```bash
    bash setup.sh
    ```
2. Define the `.env` variables to fit your requirements:
    For front application (`front/app/conf/.env`), notably
    ```bash
    # Folder where the media files are stored
    MEDIA_DIR=/home/path/to/aikon-bundle/aikon/app/mediafiles
    ```
    For the API (`api/.env`), notably
    ```bash
    # Folder where the data is stored
    API_DATA_FOLDER=data/
    ```
3. To start everything in one killable process, run (after installing each part like advised in the subfolders):
    ```bash
    bash run.sh
    ```
