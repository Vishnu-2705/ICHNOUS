"""Package initialization for models."""

try:
    from models.trace import (
        NodeType,
        TraceNode,
        Trace,
        TraceSummary,
        AnomalyFlag,
        RootCauseCandidate,
        SuggestedFix,
        DiagnosisResult,
        FullDiagnosisResponse,
        RegressionAssertion,
        RegressionTest,
    )
except ImportError:
    from backend.models.trace import (
        NodeType,
        TraceNode,
        Trace,
        TraceSummary,
        AnomalyFlag,
        RootCauseCandidate,
        SuggestedFix,
        DiagnosisResult,
        FullDiagnosisResponse,
        RegressionAssertion,
        RegressionTest,
    )

__all__ = [
    "NodeType",
    "TraceNode",
    "Trace",
    "TraceSummary",
    "AnomalyFlag",
    "RootCauseCandidate",
    "SuggestedFix",
    "DiagnosisResult",
    "FullDiagnosisResponse",
    "RegressionAssertion",
    "RegressionTest",
]
