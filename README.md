# <img alt="Aikon logo" src="https://raw.githubusercontent.com/Aikon-platform/aikon/refs/heads/main/front/app/webapp/static/favicon.ico" height="50" width="auto" style="display: inline; margin-bottom:-10px;"> AIKON platform

**[Aikon](https://aikon-platform.github.io/)** is a modular computer vision platform that enables historians to build, process, and analyze
visual corpora at scale. The platform guides users through a complete workflow from corpus construction
to algorithmic processing and result validation, without requiring technical expertise. Built on IIIF
standards and featuring a flexible data model, Aikon supports collaborative research while maintaining
full user control over automatic processing. Its modular architecture allows easy integration of new
computer vision algorithms and visualization tools, making it adaptable to diverse research needs across
historical document analysis.

<img src="https://aikon-platform.github.io/aikon-platform.png" alt="" height="500" width="auto">

This repository contains the code for the frontend platform, as well as a submodule for the worker API.

## General requirements

> - **Sudo** privileges
> - **Python** == 3.10
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

If you find this work useful, please consider citing:

```bibtex
@article{albouy2025aikon,
    title={{AIKON : A Modular Computer Vision Platform for Historical Corpora}},
    author={
        Albouy, Ségolène and
        Norindr, Somkeo and
        Kervegan, Paul and
        Aouinti, Fouad and
        Delanaux, Rémy and
        Champenois, Robin and
        Grometto, Clara and
        Lazaris, Stavros and
        Guilbaud, Alexandre and
        Husson, Matthieu and
        Aubry, Mathieu
    },
    url={https://hal.science/hal-05248250},
    year={2025},
    month={Sep},
    number={hal-05248250},
    journal={HAL Pre-Print},
    keyword={Digital Humanities, Computer Vision, Historical Documents, Visual Analysis},
}
```
