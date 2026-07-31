"""
filters.py — builds Qdrant filter objects for state / government_level,
passed into QdrantVectorStore's search via search_kwargs={"filter": ...}.
"""

from typing import Optional
from qdrant_client import models


def build_filter(
    government_level: Optional[str] = None,
    state: Optional[str] = None,
) -> Optional[models.Filter]:
    conditions = []

    if government_level:
        conditions.append(
            models.FieldCondition(
                key="metadata.government_level",
                match=models.MatchValue(value=government_level),
            )
        )

    if state:
        conditions.append(
            models.FieldCondition(
                key="metadata.target_state",
                match=models.MatchValue(value=state),
            )
        )

    if not conditions:
        return None

    return models.Filter(must=conditions)