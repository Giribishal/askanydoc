"""Explicit source routing and feature-flag boundary."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourcePlan:
    sources: tuple[str, ...]
    reason: str


def plan_sources(question: str, sharepoint_enabled: bool) -> SourcePlan:
    """Choose sources conservatively; callers may still request an explicit cross-source plan."""
    lowered = question.lower()
    sharepoint_terms = ("sharepoint", "teams", "power automate", "microsoft 365", "approval flow")
    aws_terms = ("s3", "lambda", "bedrock", "aurora", "aws")
    wants_sp = sharepoint_enabled and any(term in lowered for term in sharepoint_terms)
    wants_aws = any(term in lowered for term in aws_terms)
    if wants_sp and wants_aws:
        return SourcePlan(("aws", "sharepoint"), "question names both source domains")
    if wants_sp:
        return SourcePlan(("sharepoint",), "Microsoft 365 terminology matched")
    if wants_aws:
        return SourcePlan(("aws",), "AWS terminology matched")
    return SourcePlan(("aws",), "preserve existing AWS default when no route is explicit")
