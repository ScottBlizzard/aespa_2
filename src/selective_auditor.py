"""Finite-rule selective auditor for local certification toys.

The auditor estimates false certification among issued claims directly:

    rho(h) = E[F_h] / E[I_h]

It is intentionally simple. The point of ACCS-v0 is to create a concrete
selection-aware baseline before any server-scale safe-RL engineering.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable, List, Optional

import numpy as np

from eval_metrics import summarize_issued_claims


@dataclass(frozen=True)
class ThresholdRuleResult:
    """Audit result for a threshold rule h_tau."""

    tau: float
    n_blocks: int
    issued: int
    failures: int
    claim_yield: float
    selective_risk: float
    mean_reward: float
    mean_reward_issued: float
    risk_ucb: float
    yield_lcb: float
    feasible: bool

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class SelectedRule:
    """Selected finite-rule auditor result."""

    alpha: float
    gamma: float
    delta: float
    epsilon: float
    n_rules: int
    selected_tau: Optional[float]
    selected: Optional[ThresholdRuleResult]
    rules: List[ThresholdRuleResult]

    def to_dict(self) -> dict:
        return {
            "alpha": self.alpha,
            "gamma": self.gamma,
            "delta": self.delta,
            "epsilon": self.epsilon,
            "n_rules": self.n_rules,
            "selected_tau": self.selected_tau,
            "selected": None if self.selected is None else self.selected.to_dict(),
            "rules": [rule.to_dict() for rule in self.rules],
        }


def hoeffding_epsilon(n_blocks: int, n_rules: int, delta: float) -> float:
    """Uniform Hoeffding radius for local finite-rule selection."""

    if n_blocks <= 0:
        raise ValueError("n_blocks must be positive")
    if n_rules <= 0:
        raise ValueError("n_rules must be positive")
    if not 0.0 < delta < 1.0:
        raise ValueError("delta must be in (0, 1)")
    return float(np.sqrt(np.log(4.0 * n_rules / delta) / (2.0 * n_blocks)))


def evaluate_threshold_rule(
    x_blocks: np.ndarray,
    tau: float,
    violation_threshold: float,
    fallback_reward: float = 0.0,
) -> dict:
    """Evaluate h_tau: issue highest-reward action with x <= tau."""

    x_blocks = np.asarray(x_blocks, dtype=float)
    if x_blocks.ndim != 2:
        raise ValueError("x_blocks must have shape [n_blocks, k]")
    eligible = x_blocks <= tau
    issued = eligible.any(axis=1)
    selected_x = np.zeros(x_blocks.shape[0], dtype=float)
    if issued.any():
        masked = np.where(eligible, x_blocks, -np.inf)
        selected_x[issued] = masked[issued].max(axis=1)
    failure = issued & (selected_x > violation_threshold)
    summary = summarize_issued_claims(
        issued=issued,
        failure=failure,
        reward=selected_x,
        fallback_reward=fallback_reward,
    )
    return {
        "issued": issued,
        "failure": failure,
        "reward": selected_x,
        "summary": summary,
    }


def evaluate_accept_all(
    x_blocks: np.ndarray,
    violation_threshold: float,
    fallback_reward: float = 0.0,
) -> dict:
    """Evaluate a marginal/global rule that certifies every candidate."""

    x_blocks = np.asarray(x_blocks, dtype=float)
    if x_blocks.ndim != 2:
        raise ValueError("x_blocks must have shape [n_blocks, k]")
    issued = np.ones(x_blocks.shape[0], dtype=bool)
    selected_x = x_blocks.max(axis=1)
    failure = selected_x > violation_threshold
    summary = summarize_issued_claims(
        issued=issued,
        failure=failure,
        reward=selected_x,
        fallback_reward=fallback_reward,
    )
    return {
        "issued": issued,
        "failure": failure,
        "reward": selected_x,
        "summary": summary,
    }


def evaluate_abstain_all(
    x_blocks: np.ndarray,
    fallback_reward: float = 0.0,
) -> dict:
    """Evaluate a rule that issues no claims."""

    x_blocks = np.asarray(x_blocks, dtype=float)
    issued = np.zeros(x_blocks.shape[0], dtype=bool)
    failure = np.zeros(x_blocks.shape[0], dtype=bool)
    reward = np.zeros(x_blocks.shape[0], dtype=float)
    summary = summarize_issued_claims(
        issued=issued,
        failure=failure,
        reward=reward,
        fallback_reward=fallback_reward,
    )
    return {
        "issued": issued,
        "failure": failure,
        "reward": reward,
        "summary": summary,
    }


def audit_threshold_family(
    audit_blocks: np.ndarray,
    thresholds: Iterable[float],
    violation_threshold: float,
    alpha: float,
    gamma: float,
    delta: float,
    fallback_reward: float = 0.0,
) -> SelectedRule:
    """Select the highest-reward feasible threshold rule."""

    thresholds = sorted(float(t) for t in thresholds)
    if not thresholds:
        raise ValueError("thresholds must be nonempty")
    n_blocks = int(np.asarray(audit_blocks).shape[0])
    eps = hoeffding_epsilon(n_blocks, len(thresholds), delta)
    results: List[ThresholdRuleResult] = []

    for tau in thresholds:
        evaluated = evaluate_threshold_rule(
            audit_blocks,
            tau=tau,
            violation_threshold=violation_threshold,
            fallback_reward=fallback_reward,
        )
        summary = evaluated["summary"]
        fhat = summary.failures / n_blocks
        ihat = summary.issued / n_blocks
        denominator = ihat - eps
        risk_ucb = float("inf") if denominator <= 0.0 else (fhat + eps) / denominator
        yield_lcb = max(0.0, ihat - eps)
        feasible = bool(risk_ucb <= alpha and yield_lcb >= gamma)
        results.append(
            ThresholdRuleResult(
                tau=tau,
                n_blocks=summary.n_blocks,
                issued=summary.issued,
                failures=summary.failures,
                claim_yield=summary.claim_yield,
                selective_risk=summary.selective_risk,
                mean_reward=summary.mean_reward,
                mean_reward_issued=summary.mean_reward_issued,
                risk_ucb=risk_ucb,
                yield_lcb=yield_lcb,
                feasible=feasible,
            )
        )

    feasible_rules = [rule for rule in results if rule.feasible]
    selected = max(feasible_rules, key=lambda r: (r.mean_reward, r.tau)) if feasible_rules else None
    return SelectedRule(
        alpha=alpha,
        gamma=gamma,
        delta=delta,
        epsilon=eps,
        n_rules=len(thresholds),
        selected_tau=None if selected is None else selected.tau,
        selected=selected,
        rules=results,
    )
