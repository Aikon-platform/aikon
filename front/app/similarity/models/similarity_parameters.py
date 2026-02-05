import hashlib
import json
from django.db import models

_params_cache = {}


def generate_hash(params):
    serialized = json.dumps(params, sort_keys=True)
    return hashlib.sha256(serialized.encode()).hexdigest()[:8]


class SimilarityParameters(models.Model):
    class Meta:
        app_label = "webapp"

    hash = models.CharField(max_length=8, primary_key=True)
    parameters = models.JSONField()

    @classmethod
    def get_or_create_from_params(cls, params: dict) -> str:
        hash_value = generate_hash(params)
        obj, created = cls.objects.get_or_create(
            hash=hash_value, defaults={"parameters": params}
        )
        _params_cache[hash_value] = params
        return hash_value

    @classmethod
    def get_params(cls, hash_value: str) -> dict | None:
        if hash_value in _params_cache:
            return _params_cache[hash_value]

        try:
            params = cls.objects.get(hash=hash_value).parameters
            _params_cache[hash_value] = params
            return params
        except cls.DoesNotExist:
            return None

    @classmethod
    def load_cache(cls):
        """Preload all parameters into cache (optionnel)"""
        global _params_cache
        _params_cache = {p.hash: p.parameters for p in cls.objects.all()}


def get_similarity_params(hash_value: str) -> dict | None:
    return SimilarityParameters.get_params(hash_value)
