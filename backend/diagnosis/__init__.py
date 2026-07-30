"""Package initialization for diagnosis module."""

try:
    from diagnosis.llm import diagnose_with_llm
    from diagnosis.taxonomy import TAXONOMY_LIST, FailureCategory
    from diagnosis.validator import validate_groundedness
except ImportError:
    from backend.diagnosis.llm import diagnose_with_llm
    from backend.diagnosis.taxonomy import TAXONOMY_LIST, FailureCategory
    from backend.diagnosis.validator import validate_groundedness

__all__ = [
    "diagnose_with_llm",
    "validate_groundedness",
    "TAXONOMY_LIST",
    "FailureCategory",
]
