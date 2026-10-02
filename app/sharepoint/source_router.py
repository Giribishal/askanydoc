"""Explicit source routing and feature-flag boundary."""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class SourcePlan:
    sources: tuple[str, ...]
    reason: str
    aws_signals: tuple[str, ...] = ()
    sharepoint_signals: tuple[str, ...] = ()


def plan_sources(question: str, sharepoint_enabled: bool) -> SourcePlan:
    """Return only high-confidence source routes; ambiguous requests remain model-led."""
    lowered = " ".join(question.lower().replace("_", " ").split())
    sharepoint_terms = (
        "sharepoint",
        "microsoft 365",
        "power automate",
        "approval flow",
        "hybrid-cloud",
        "hybrid cloud",
        "site permission",
        "restricted site",
    )
    aws_terms = (
        "aws",
        "amazon s3",
        "s3",
        "lambda",
        "bedrock",
        "aurora",
        "sqs",
        "partial batch",
        "reportbatchitemfailures",
        "dead-letter queue",
        "disaster recovery",
        "disaster-recovery",
    )
    def contains_term(term: str) -> bool:
        return re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", lowered) is not None

    matched_sp_terms = tuple(term for term in sharepoint_terms if contains_term(term))
    matched_aws_terms = tuple(term for term in aws_terms if contains_term(term))
    wants_sp = sharepoint_enabled and bool(matched_sp_terms)
    wants_aws = bool(matched_aws_terms)
    if wants_sp and wants_aws:
        return SourcePlan(
            ("aws", "sharepoint"),
            "high-confidence signals matched both sources",
            aws_signals=matched_aws_terms,
            sharepoint_signals=matched_sp_terms,
        )
    if wants_sp:
        return SourcePlan(
            ("sharepoint",),
            "high-confidence Microsoft 365 signal matched",
            sharepoint_signals=matched_sp_terms,
        )
    if wants_aws:
        return SourcePlan(
            ("aws",),
            "high-confidence AWS-library signal matched",
            aws_signals=matched_aws_terms,
        )
    return SourcePlan((), "no high-confidence source signal; keep model-led routing")
