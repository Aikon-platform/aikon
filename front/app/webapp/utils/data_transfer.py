"""
Generic serialization of records for cross-instance transfer.
Export side: symmetric with webapp.utils.data_import (import side).
"""
from django.apps import apps
from django.db import models

from app.config.settings import APP_URL, APP_NAME

def witness_extras(witness) -> dict:
    """Operational data needed to import a witness, alongside its raw metadata"""
    from app.config.settings import ADDITIONAL_MODULES

    endpoints = {
        "extracted_regions": ("region_extraction", "extracted-regions"),
        "vectorizations": ("vectorization", "vectorized-images"),
    }
    regions = {
        r.id: {
            "digitization_id": r.digitization_id,
            "treatments": {
                name: f"{APP_URL}/{APP_NAME}/witness/{witness.id}/regions/{r.id}/json/{suffix}"
                for name, (module, suffix) in endpoints.items()
                if module in ADDITIONAL_MODULES
            },
        }
        for r in witness.get_regions()
    }
    return {
        "digitizations": {d.id: d.get_manifest_url() for d in witness.get_digits()},
        "regions_extraction": regions,
    }


# Models allowed to travel between instances.
# owned: always created on import (belongs to a parent record), never deduplicated
# parent: name of the FK field pointing to the record that owns it
# extras: callable adding operational data to the serialized payload
TRANSFER_MODELS = {
    "person": {},
    "place": {},
    "language": {},
    "tag": {},
    "conservationplace": {},
    "work": {},
    "edition": {},
    "series": {},
    "witness": {"owned": True, "extras": witness_extras},
    "content": {"owned": True, "parents": ("witness",)},
    "role": {"owned": True, "parents": ("content", "series")},
}

EXCLUDED_FIELDS = {
    "json",
    "slug",
    "user",
    "is_public",
    "created_at",
    "updated_at",
    "shared_with",
}


def transferable(model) -> bool:
    return model._meta.model_name in TRANSFER_MODELS


def get_transfer_model(model_name: str):
    name = model_name.lower()
    if name not in TRANSFER_MODELS:
        raise ValueError(f"Model '{model_name}' cannot be transferred")
    return apps.get_model("webapp", name)


def record_raw_url(record) -> str:
    return f"{APP_URL}/{APP_NAME}/raw/{record._meta.model_name}/{record.pk}"


def serialize_record(record) -> dict:
    """
    {
        "class": model name,
        "fields": {scalar field: value},
        "related": {fk field: raw url | None},
        "m2m": {m2m field: [raw urls]},
        "children": {accessor: [raw urls]}  # owned reverse FKs (e.g. witness.contents)
    }
    """
    meta = record._meta
    data = {
        "id": record.pk,
        "class": meta.model_name,
        "fields": {},
        "related": {},
        "m2m": {},
        "children": {},
    }

    for f in meta.concrete_fields:
        if f.primary_key or f.name in EXCLUDED_FIELDS:
            continue
        if f.is_relation:
            if transferable(f.related_model):
                rel = getattr(record, f.name)
                data["related"][f.name] = record_raw_url(rel) if rel else None
        elif not isinstance(f, models.FileField):
            data["fields"][f.name] = f.value_from_object(record)

    for f in meta.many_to_many:
        if f.name not in EXCLUDED_FIELDS and transferable(f.related_model):
            data["m2m"][f.name] = [
                record_raw_url(r) for r in getattr(record, f.name).all()
            ]

    for rel in meta.related_objects:
        conf = TRANSFER_MODELS.get(rel.related_model._meta.model_name, {})
        if conf.get("owned") and rel.field.name in conf.get("parents", ()):
            accessor = rel.get_accessor_name()
            data["children"][accessor] = [
                record_raw_url(r) for r in getattr(record, accessor).all()
            ]

    if extras := TRANSFER_MODELS[meta.model_name].get("extras"):
        data |= extras(record)

    return data
