from enum import IntEnum
from typing import NamedTuple


class ImgRef(NamedTuple):
    wit: int
    digit_type: str
    digit: int
    page: str
    bbox: str | None  # None = page-level

Bbox = tuple[int, int, int, int]

class Region(NamedTuple):
    img: str  # name stored in RegionPair
    name: str  # normalized name
    box: Bbox

    @property
    def rank(self) -> tuple:
        """Canonical region of a cluster (lowest rank): the smallest, then the one already normalized"""
        return self.box[2] * self.box[3], self.img != self.name, self.img


class SimilarityType(IntEnum):
    AUTO = 1
    MANUAL = 2
    PROPAGATED = 3


class SimilarityCategory(IntEnum):
    EXACT_MATCH = 1
    PARTIAL_MATCH = 2
    SEMANTIC_MATCH = 3
    NO_MATCH = 4
    USER_MATCH = 5


class SourceType:
    REGIONS = "regions"
    PAGES = "pages"


class Priority(IntEnum):
    MANUAL = 0
    PROPAGATED = 1
    CATEGORIZED = 2
    AUTO = 3
    NO_MATCH = 4
    NONE = 5


SIM_DEFAULTS = {
    "algorithm": "cosine",
    "feat_net": "dinov2_vitb14",
    "cosine_n_filter": 10,
    "segswap_prefilter": True,
    "segswap_n": 10,
    "transpositions": ["none"],
    "source_type": SourceType.REGIONS,
}
