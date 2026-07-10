"""
Import records from another AIKON instance.
Everything goes through HTTP (source instance may be remote): see webapp.utils.data_transfer for the export side.
"""
from pathlib import Path
from urllib.parse import urlparse

import requests
from django.db import IntegrityError, transaction

from app.config.settings import APP_URL
from app.webapp.models.digitization import Digitization
from app.webapp.models.region_extraction import RegionExtraction
from app.webapp.models.utils.constants import MAN_ABBR, MS_ABBR
from app.webapp.utils.data_transfer import TRANSFER_MODELS, get_transfer_model
from app.webapp.utils.paths import REGIONS_PATH

TIMEOUT = 30


def is_same_instance(url: str) -> bool:
    return urlparse(url).netloc == urlparse(APP_URL).netloc


class ImportContext:
    def __init__(self, treatment):
        self.treatment = treatment
        self.user = treatment.requested_by
        self.opts = treatment.api_parameters or {}
        self.mapping = self.opts.get("mapping") or {
            "witnesses": {},
            "digitizations": {},
            "regions": {},
        }
        self.errors = self.opts.get("errors") or []
        self.records = {}  # {source url: local record}
        self.session = requests.Session()

    def fetch(self, url):
        response = self.session.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()

    def save(self):
        self.opts["mapping"] = self.mapping
        self.opts["errors"] = self.errors
        self.treatment.update(api_parameters=self.opts)


def update_mapping(treatment_id, key, src_id, new_id):
    """Concurrency-safe update of the id mapping stored on the import Treatment"""
    from app.webapp.models.treatment import Treatment

    with transaction.atomic():
        treatment = Treatment.objects.select_for_update().get(pk=treatment_id)
        params = treatment.api_parameters or {}
        params.setdefault("mapping", {}).setdefault(key, {})[str(src_id)] = new_id
        Treatment.objects.filter(pk=treatment_id).update(api_parameters=params)


def dedup_or_create(model, fields):
    """Records with exactly the same metadata are merged"""
    try:
        return model.objects.get_or_create(**fields)[0]
    except model.MultipleObjectsReturned:
        return model.objects.filter(**fields).first()
    except IntegrityError:
        # same unique key (e.g. Person.name) but different metadata: reuse the existing record
        unique = {
            f.name: fields[f.name]
            for f in model._meta.concrete_fields
            if f.unique and f.name in fields
        }
        return model.objects.get(**unique)


def import_record(url, ctx: ImportContext, parent=None, extra=None, data=None):
    """
    Recursively import a metadata record (and its relations) from its raw JSON url.
    parent: local record owning the imported one (for owned models, see TRANSFER_MODELS)
    extra: field overrides applied at creation (e.g. user/is_public for Witness)
    data: pre-fetched payload for `url`
    """
    if url in ctx.records:
        return ctx.records[url]

    data = data or ctx.fetch(url)
    model = get_transfer_model(data["class"])
    conf = TRANSFER_MODELS[model._meta.model_name]
    valid = {f.name for f in model._meta.concrete_fields}

    fields = {k: v for k, v in (data.get("fields") or {}).items() if k in valid}
    for name, ref in (data.get("related") or {}).items():
        if name not in valid:
            continue
        if name in conf.get("parents", ()):
            f = model._meta.get_field(name)
            fields[name] = parent if isinstance(parent, f.related_model) else None
        else:
            fields[name] = import_record(ref, ctx) if ref else None
    fields |= extra or {}

    record = (
        model.objects.create(**fields)
        if conf.get("owned")
        else dedup_or_create(model, fields)
    )
    ctx.records[url] = record

    for name, refs in (data.get("m2m") or {}).items():
        getattr(record, name).set([import_record(r, ctx) for r in refs])
    for refs in (data.get("children") or {}).values():
        for r in refs:
            import_record(r, ctx, parent=record)
    return record


def resolve_source(source_url, ctx: ImportContext):
    """Return ({src_wit_id: witness json url}, similarity url or None)"""
    data = ctx.fetch(source_url)
    if "/witness/" in source_url:
        return ({str(data["id"]): source_url} if data else {}), None
    similarity_url = data.pop("similarity", None) if data else None
    return data or {}, similarity_url


def import_witness(wit_url, ctx: ImportContext):
    """
    Create a Witness (with cascaded metadata) and its Digitizations (as manifests).
    Image download / regions import are chained asynchronously by the caller.
    Return (witness, [(digit, manifest_url, {src_regions_id: extracted_regions_url})])
    """
    from app.webapp.models.witness import Witness

    data = ctx.fetch(wit_url)
    if not data:
        # private witness
        return None, []

    src_wid = str(data["id"])
    if src_wid in ctx.mapping["witnesses"]:
        return None, []

    extra = {"user": ctx.user, "is_public": False}
    if data.get("class") == "witness":
        witness = import_record(wit_url, ctx, extra=extra, data=data)
    else:
        # legacy source instance without raw serialization: minimal witness
        witness = Witness.objects.create(
            type=MS_ABBR, id_nb=(data.get("title") or "")[:150], **extra
        )
    ctx.mapping["witnesses"][src_wid] = witness.id

    regions_by_digit = {}
    for src_rid, regions in (data.get("regions_extraction") or data.get("regions") or {}).items():
        if url := (regions.get("treatments") or {}).get("extracted_regions"):
            regions_by_digit.setdefault(str(regions.get("digitization_id")), {})[
                src_rid
            ] = url

    digits = []
    for src_did, manifest_url in (data.get("digitizations") or {}).items():
        if not manifest_url:
            continue
        digit = Digitization(
            witness=witness, digit_type=MAN_ABBR, manifest=manifest_url
        )
        digit._skip_post_save = True  # conversion is chained explicitly by start_import
        digit.save()
        ctx.mapping["digitizations"][str(src_did)] = digit.id
        digits.append((digit, manifest_url, regions_by_digit.get(str(src_did), {})))

    return witness, digits


def write_regions_file(region_extraction: RegionExtraction, crops: dict):
    """
    Write extracted crops in the txt annotation format:
    "{canvas_nb} {img_name}" line followed by one "x y w h" line per region
    """
    from app.webapp.utils.functions import get_img_nb_len

    digit = region_extraction.get_digit()
    nb_len = get_img_nb_len(digit.get_ref()) or 4

    lines = []
    for canvas in sorted(crops, key=int):
        if not crops[canvas]:
            continue
        lines.append(f"{canvas} {digit.get_ref()}_{str(canvas).zfill(nb_len)}.jpg")
        lines += [" ".join(map(str, crop["xywh"])) for crop in crops[canvas].values()]
    Path(f"{REGIONS_PATH}/{region_extraction.get_ref()}.txt").write_text(
        "\n".join(lines)
    )


def import_region_extraction(digit: Digitization, regions_url: str, model="imported"):
    """
    Import extracted regions for an already downloaded digitization
    and index them into aiiinotate. Return the new RegionExtraction id.
    """
    from app.webapp.utils.iiif.annotation import index_region_extraction

    data = requests.get(regions_url, timeout=TIMEOUT).json()
    crops = data.get("extracted_crops") or {}
    if not any(crops.values()):
        return None

    region_extraction, _ = RegionExtraction.objects.get_or_create(
        digitization=digit, model=model
    )
    write_regions_file(region_extraction, crops)
    index_region_extraction(region_extraction)
    digit.witness.set_json_region_extractions()
    return region_extraction.id


def import_similarity_pairs(ctx: ImportContext, similarity_url: str) -> int:
    """
    Paginate the source similarity endpoint and recreate RegionPairs,
    rewriting image refs with the local witness/digitization ids.
    """
    from app.similarity.models.region_pair import (
        RegionPair,
        get_digit_region_extraction_id,
        parse_img,
    )

    wit_map, digit_map = ctx.mapping["witnesses"], ctx.mapping["digitizations"]

    def rewrite(img):
        ref = parse_img(img)
        wit, digit = wit_map.get(str(ref.wit)), digit_map.get(str(ref.digit))
        if wit is None or digit is None:
            return None
        suffix = f"_{ref.bbox}" if ref.bbox else ""
        # imported digitizations are always manifests
        return f"wit{wit}_{MAN_ABBR}{digit}_{ref.page}{suffix}.jpg"

    hashed, manual, after = [], [], 0
    while True:
        data = ctx.fetch(f"{similarity_url}?after={after}&limit=1000")
        for p in data.get("pairs") or []:
            try:
                img_1, img_2 = rewrite(p["img_1"]), rewrite(p["img_2"])
            except ValueError:
                continue
            if not (img_1 and img_2):
                continue
            # anno_* and regions_id_* are source-specific, category_x holds source user ids: dropped
            pair = RegionPair(
                img_1=img_1,
                img_2=img_2,
                score=p.get("score"),
                category=p.get("category"),
                similarity_type=p.get("similarity_type"),
                similarity_hash=p.get("similarity_hash"),
            )
            pair.clean()  # normalizes ordering + digit_1/digit_2
            (hashed if pair.similarity_hash else manual).append(pair)

        after = data.get("next_cursor")
        if not after:
            break

    RegionPair.objects.bulk_update_or_create(
        hashed,
        update_fields=["digit_1", "digit_2", "score", "category", "similarity_type"],
        match_fields=["img_1", "img_2", "similarity_hash"],
    )
    # NULL hashes are distinct for the unique constraint: ON CONFLICT never
    # matches them, so manual pairs are upserted individually
    for p in manual:
        RegionPair.objects.get_or_create(
            img_1=p.img_1,
            img_2=p.img_2,
            similarity_hash=None,
            defaults={
                "digit_1": p.digit_1,
                "digit_2": p.digit_2,
                "score": p.score,
                "category": p.category,
                "similarity_type": p.similarity_type,
            },
        )

    # pairs are only listed in the UI if a RegionExtraction exists for their digitization
    for digit_id in {d for p in hashed + manual for d in (p.digit_1, p.digit_2)}:
        get_digit_region_extraction_id(digit_id, create_if_missing=True)

    return len(hashed) + len(manual)
