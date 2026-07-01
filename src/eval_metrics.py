"""Metrics for local selective-certification toys."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict

import numpy as np


@dataclass(frozen=True)
class MetricSummary:
    """Aggregate issued-claim metrics for one method."""

    n_blocks: int
    issued: int
    failures: int
    claim_yield: float
    selective_risk: float
    mean_reward: float
    mean_reward_issued: float
    fallback_rate: float

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)


def summarize_issued_claims(
    issued: np.ndarray,
    failure: np.ndarray,
    reward: np.ndarray,
    fallback_reward: float = 0.0,
) -> MetricSummary:
    """Summarize false certification, yield, and reward.

    Args:
        issued: Boolean indicator for whether a block receives a claim.
        failure: Boolean indicator for whether the issued claim is false.
        reward: Selected reward for issued blocks. Values on non-issued blocks are ignored.
        fallback_reward: Reward assigned to abstentions/fallbacks for aggregate reward.
    """

    issued = np.asarray(issued, dtype=bool)
    failure = np.asarray(failure, dtype=bool)
    reward = np.asarray(reward, dtype=float)
    if issued.shape != failure.shape or issued.shape != reward.shape:
        raise ValueError("issued, failure, and reward must have the same shape")

    n_blocks = int(issued.size)
    issued_count = int(issued.sum())
    failures = int((issued & failure).sum())
    claim_yield = issued_count / n_blocks if n_blocks else 0.0
    selective_risk = failures / issued_count if issued_count else 0.0
    realized_reward = np.where(issued, reward, fallback_reward)
    mean_reward = float(realized_reward.mean()) if n_blocks else 0.0
    mean_reward_issued = float(reward[issued].mean()) if issued_count else 0.0
    fallback_rate = 1.0 - claim_yield

    return MetricSummary(
        n_blocks=n_blocks,
        issued=issued_count,
        failures=failures,
        claim_yield=claim_yield,
        selective_risk=selective_risk,
        mean_reward=mean_reward,
        mean_reward_issued=mean_reward_issued,
        fallback_rate=fallback_rate,
    )


def closed_form_selection_risk(per_action_failure: float, k: int) -> float:
    """Selected-action failure when at least one of K candidates is failing."""

    if not 0.0 <= per_action_failure <= 1.0:
        raise ValueError("per_action_failure must be in [0, 1]")
    if k <= 0:
        raise ValueError("k must be positive")
    return 1.0 - (1.0 - per_action_failure) ** k


def binomial_standard_error(p_hat: float, n: int) -> float:
    """Wald standard error used only for descriptive local tables."""

    if n <= 0:
        return 0.0
    p_hat = min(max(float(p_hat), 0.0), 1.0)
    return float(np.sqrt(p_hat * (1.0 - p_hat) / n))
