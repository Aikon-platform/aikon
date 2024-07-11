from typing import List
from app.config.celery import celery_app


# @celery_app.task
def compute_similarity_scores(
    regions_refs: List[str] = None, max_rows: int = 50, show_checked_ref: bool = False
):
    from app.webapp.views import check_ref
    from app.similarity.utils import compute_total_similarity

    checked_regions = regions_refs[0]

    regions = [
        region
        for (passed, region) in [check_ref(ref, "Regions") for ref in regions_refs]
        if passed
    ]

    if not len(regions):
        from app.webapp.utils.logger import log

        log(
            f"[compute_similarity_scores] No annotation corresponding to {regions_refs}"
        )
        return {}
    return compute_total_similarity(
        regions, checked_regions, regions_refs, max_rows, show_checked_ref
    )


@celery_app.task
def check_similarity_files(file_names):
    # TODO: check content of similarity files
    # must contain a list of dictionaries with keys: 'ref1', 'ref2', 'score'
    pass
