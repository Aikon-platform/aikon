# <img alt="Aikon logo" src="https://github.com/Aikon-platform/aikon/blob/main/app/webapp/static/favicon.ico" height="50" width="auto" style="display: inline; margin-bottom:-10px;"> AIKON bundle version

**[Aikon](https://aikon-platform.github.io/)** is a modular research platform designed to empower humanities scholars
in leveraging artificial intelligence and computer vision methods for analyzing large-scale heritage collections.
It offers a user-friendly interface for visualizing, extracting, and analyzing illustrations from historical documents,
fostering interdisciplinary collaboration and sustainability across digital humanities projects. Built on proven
technologies and interoperable formats, Aikon's adaptable architecture supports all projects involving visual materials.

[About the AIKON platform](https://aikon-platform.github.io/)

This repository contains the code for the frontend platform, as well as a submodule for the worker API.

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
    MEDIA_DIR=/home/path/to/aikon/front/app/mediafiles
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

## Acknowledgements

***Aikon** is funded and supported by the Agence Nationale pour la Recherche and the European Research Council*
- **VHS** [ANR-21-CE38-0008](https://anr.fr/Projet-ANR-21-CE38-0008): computer Vision and Historical analysis of Scientific illustration circulation
- **EiDA** [ANR-22-CE38-0014](https://anr.fr/Projet-ANR-22-CE38-0014): EdIter et analyser les Diagrammes astronomiques historiques avec l’intelligence Artificielle
- **DISCOVER** project [ERC-101076028](https://cordis.europa.eu/project/id/101076028): Discovering and Analyzing Visual Structures

```bibtex
@misc{albouy2024aikon,
    title={AIKON: a computer vision platform for the Digital Humanities},
    author={
        Ségolène Albouy,
        Jade Norindr,
        Fouad Aouinti,
        Clara Grometto,
        Robin Champenois,
        Alexandre Guilbaud,
        Stavros Lazaris,
        Matthieu Husson,
        Mathieu Aubry
    },
    url={https://github.com/Aikon-platform/aikon}
    year={2024}
}
```