from __future__ import annotations

import importlib.util
import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kendalltau
from agent_as_a_judge.languages import (
    ALL_LANGUAGES,
    FRAMEWORKS as DEFAULT_FRAMEWORKS,
)


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_TESTS = ROOT / "benchmark_tests"
OUTPUT_DIR = ROOT / "Project-2" / "paper_acl" / "analysis"

BACKBONES = {
    "gpt-4o": "GPT-4o",
    "gpt-5.4": "GPT-5.4",
    "claude-sonnet-4.6": "Sonnet",
    "gemini-3-flash-preview": "Gemini",
    "deepseek-v3.2": "DeepSeek",
    "qwen3.5-9b": "Qwen",
}
BACKBONE_ORDER = list(BACKBONES.values())
LANGUAGES = list(ALL_LANGUAGES)
FRAMEWORKS = list(DEFAULT_FRAMEWORKS)
BOOTSTRAP_REPS = 1000
BOOTSTRAP_SEED = 7
ABLATION_BOOTSTRAP_REPS = 100
TASK_SUBSAMPLE_REPS = 100
REQUIREMENT_BOOTSTRAP_REPS = 200
TASK_ABLATION_SIZES = [10, 20, 30, 40, 55]
TABLE2_METHODS = [
    "Raw (no calibration)",
    "Random control",
    "Per-language norm.",
    "Backbone-only norm.",
    "Z-score",
    "Quantile normalization",
    "ComBat-EB",
    "Dawid-Skene EM",
    "Ensemble",
    "CBC",
    "CBC-Weighted",
    "Oracle (eval-task beta)",
]


def task_key(name: str) -> tuple[int, str]:
    prefix = name.split("_", 1)[0]
    try:
        return (int(prefix), name)
    except ValueError:
        return (9999, name)


def compute_task_satisfaction_rate(obj: dict) -> float:
    stats = obj.get("judge_stats") or []
    if not stats:
        raise ValueError("Missing judge_stats")
    num_satisfied = sum(1 for stat in stats if bool(stat.get("satisfied", False)))
    return 100.0 * num_satisfied / len(stats)


def load_run_level_scores() -> pd.DataFrame:
    rows: list[dict] = []
    for model_dir, backbone in BACKBONES.items():
        for language in LANGUAGES:
            for framework in FRAMEWORKS:
                gray_dir = (
                    BENCHMARK_TESTS
                    / model_dir
                    / language
                    / framework
                    / "judgment"
                    / framework
                    / "agent_as_a_judge"
                    / "gray_box"
                )
                if not gray_dir.exists():
                    continue
                for path in sorted(gray_dir.glob("*.json"), key=lambda p: task_key(p.stem)):
                    obj = json.loads(path.read_text(encoding="utf-8"))
                    score = compute_task_satisfaction_rate(obj)
                    rows.append(
                        {
                            "backbone": backbone,
                            "language": language,
                            "framework": framework,
                            "task": obj.get("name", path.stem),
                            "score": score,
                            "task_solved": int(score == 100.0),
                        }
                    )
    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError("No benchmark rows were loaded.")
    return df


def aggregate_task_level(df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        df.groupby(["task", "language", "backbone"], as_index=False)["score"]
        .mean()
        .rename(columns={"score": "score"})
    )
    return grouped


def expand_rows_by_task_weights(
    df: pd.DataFrame,
    task_weights: dict[str, int],
) -> pd.DataFrame:
    weighted = df.copy()
    weighted["weight"] = weighted["task"].map(task_weights).fillna(0).astype(int)
    weighted = weighted[weighted["weight"] > 0].copy()
    if weighted.empty:
        raise ValueError("No rows remain after applying task weights.")
    return weighted.loc[weighted.index.repeat(weighted["weight"])].drop(columns=["weight"]).reset_index(drop=True)


def build_score_matrix(
    task_df: pd.DataFrame,
    task_weights: dict[str, int] | None = None,
    backbones: list[str] | None = None,
) -> pd.DataFrame:
    backbone_order = BACKBONE_ORDER if backbones is None else list(backbones)
    matrix_df = task_df.copy()
    if task_weights is None:
        grouped = matrix_df.groupby(["language", "backbone"], as_index=False)["score"].mean()
    else:
        matrix_df["weight"] = matrix_df["task"].map(task_weights).fillna(0).astype(int)
        matrix_df = matrix_df[matrix_df["weight"] > 0].copy()
        if matrix_df.empty:
            raise ValueError("No rows remain after applying task weights.")
        matrix_df["weighted_score"] = matrix_df["score"] * matrix_df["weight"]
        grouped = (
            matrix_df.groupby(["language", "backbone"], as_index=False)[["weighted_score", "weight"]]
            .sum()
        )
        grouped["score"] = grouped["weighted_score"] / grouped["weight"]
        grouped = grouped[["language", "backbone", "score"]]

    return (
        grouped.pivot(index="language", columns="backbone", values="score")
        .reindex(index=LANGUAGES, columns=backbone_order)
    )


def compute_beta_from_matrix(score_means: pd.DataFrame) -> pd.DataFrame:
    row_means = score_means.mean(axis=1)
    col_means = score_means.mean(axis=0)
    grand_mean = float(score_means.values.mean())
    return score_means.sub(row_means, axis=0).sub(col_means, axis=1) + grand_mean


def compute_beta(
    task_df: pd.DataFrame,
    task_weights: dict[str, int] | None = None,
    backbones: list[str] | None = None,
) -> pd.DataFrame:
    score_means = build_score_matrix(task_df, task_weights=task_weights, backbones=backbones)
    return compute_beta_from_matrix(score_means)


def compute_weighted_backbone_weights(score_means: pd.DataFrame) -> pd.Series:
    variances = score_means.var(axis=0, ddof=0)
    variances = variances.replace(0.0, 1e-8)
    weights = 1.0 / variances
    weights = weights / weights.sum()
    return weights.reindex(BACKBONE_ORDER)


def compute_weighted_beta(
    task_df: pd.DataFrame,
    task_weights: dict[str, int] | None = None,
    backbones: list[str] | None = None,
) -> tuple[pd.DataFrame, pd.Series]:
    score_means = build_score_matrix(task_df, task_weights=task_weights, backbones=backbones)
    weights = compute_weighted_backbone_weights(score_means)
    language_weighted = score_means.mul(weights, axis=1).sum(axis=1)
    backbone_means = score_means.mean(axis=0)
    grand_weighted = float((backbone_means * weights).sum())
    beta = score_means.sub(language_weighted, axis=0).sub(backbone_means, axis=1) + grand_weighted
    return beta, weights


def compute_rank_reversal(task_df: pd.DataFrame) -> pd.DataFrame:
    score_means = build_score_matrix(task_df)
    rows: list[dict] = []
    for left, right in combinations(BACKBONE_ORDER, 2):
        diffs = {language: float(score_means.loc[language, left] - score_means.loc[language, right]) for language in LANGUAGES}
        best = None
        for lang_a, lang_b in combinations(LANGUAGES, 2):
            product = diffs[lang_a] * diffs[lang_b]
            if best is None or product < best["product"]:
                best = {
                    "backbone_i": left,
                    "backbone_j": right,
                    "language_a": lang_a,
                    "language_b": lang_b,
                    "d_a": diffs[lang_a],
                    "d_b": diffs[lang_b],
                    "product": product,
                    "delta": max(0.0, -product),
                }
        assert best is not None
        best["rank_reversal"] = bool(best["delta"] > 0.0)
        rows.append(best)
    return pd.DataFrame(rows)


def dummy_block(df: pd.DataFrame, column: str, prefix: str) -> pd.DataFrame:
    return pd.get_dummies(df[column].astype(str), prefix=prefix, dtype=float)


def interaction_block(df: pd.DataFrame, left: str, right: str, prefix: str) -> pd.DataFrame:
    combo = df[left].astype(str) + "__" + df[right].astype(str)
    return pd.get_dummies(combo, prefix=prefix, dtype=float)


def fit_ols_r2(
    df: pd.DataFrame,
    include_framework: bool,
    include_backbone_language: bool,
    include_task_language: bool,
) -> dict:
    blocks = [pd.DataFrame({"intercept": np.ones(len(df), dtype=float)})]
    blocks.append(dummy_block(df, "task", "task"))
    blocks.append(dummy_block(df, "backbone", "backbone"))
    blocks.append(dummy_block(df, "language", "language"))
    if include_framework:
        blocks.append(dummy_block(df, "framework", "framework"))
    if include_backbone_language:
        blocks.append(interaction_block(df, "backbone", "language", "bl"))
    if include_task_language:
        blocks.append(interaction_block(df, "task", "language", "tl"))

    X = pd.concat(blocks, axis=1).to_numpy(dtype=float)
    y = df["score"].to_numpy(dtype=float)
    coef, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    y_hat = X @ coef
    sse = float(np.sum((y - y_hat) ** 2))
    sst = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - sse / sst
    return {
        "n_obs": int(len(y)),
        "n_params": int(X.shape[1]),
        "sse": sse,
        "sst": sst,
        "r2": r2,
    }


def save_heatmap(beta_df: pd.DataFrame) -> None:
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8.5, 3.6))
    vmax = float(np.abs(beta_df.to_numpy()).max())
    image = ax.imshow(beta_df.to_numpy(dtype=float), cmap="RdBu", vmin=-vmax, vmax=vmax, aspect="auto")
    ax.set_xticks(np.arange(len(beta_df.columns)), labels=list(beta_df.columns), rotation=45, ha="right")
    ax.set_yticks(np.arange(len(beta_df.index)), labels=list(beta_df.index))
    for row_idx, language in enumerate(beta_df.index):
        for col_idx, backbone in enumerate(beta_df.columns):
            value = float(beta_df.loc[language, backbone])
            ax.text(col_idx, row_idx, f"{value:.2f}", ha="center", va="center", fontsize=8)
    cbar = fig.colorbar(image, ax=ax)
    cbar.set_label(r"$\hat{\beta}(\ell,b)$")
    ax.set_xlabel("Backbone")
    ax.set_ylabel("Language")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "beta_heatmap.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def bootstrap_task_split(
    tasks: list[str],
    rng: np.random.Generator,
) -> tuple[dict[str, int], list[str]]:
    sampled = rng.choice(tasks, size=len(tasks), replace=True)
    train_weights = {task: 0 for task in tasks}
    for task in sampled:
        train_weights[str(task)] += 1
    eval_tasks = [task for task in tasks if train_weights[task] == 0]
    return train_weights, eval_tasks


def mean_pairwise_kendall_tau(score_matrix: pd.DataFrame) -> float:
    taus: list[float] = []
    language_order = list(score_matrix.index)
    for left, right in combinations(language_order, 2):
        tau, _ = kendalltau(score_matrix.loc[left].to_numpy(), score_matrix.loc[right].to_numpy())
        if not np.isnan(tau):
            taus.append(float(tau))
    if not taus:
        return 0.0
    return float(np.mean(taus))


def row_zscore(matrix: pd.DataFrame) -> pd.DataFrame:
    row_std = matrix.std(axis=1, ddof=0).replace(0.0, 1.0)
    return matrix.sub(matrix.mean(axis=1), axis=0).div(row_std, axis=0)


def col_center(matrix: pd.DataFrame, train_matrix: pd.DataFrame) -> pd.DataFrame:
    return matrix.sub(train_matrix.mean(axis=0), axis=1)


def col_zscore(matrix: pd.DataFrame, train_matrix: pd.DataFrame) -> pd.DataFrame:
    col_std = train_matrix.std(axis=0, ddof=0).replace(0.0, 1.0)
    return matrix.sub(train_matrix.mean(axis=0), axis=1).div(col_std, axis=1)


def col_quantile(matrix: pd.DataFrame, train_matrix: pd.DataFrame) -> pd.DataFrame:
    quantile_df = matrix.copy()
    for backbone in matrix.columns:
        train_vals = np.sort(train_matrix[backbone].to_numpy(dtype=float))
        quantile_df[backbone] = [
            np.searchsorted(train_vals, value, side="right") / len(train_vals)
            for value in matrix[backbone].to_numpy(dtype=float)
        ]
    return quantile_df


def combat_eb_adjust(
    eval_matrix: pd.DataFrame,
    train_task_df: pd.DataFrame,
) -> pd.DataFrame:
    train_df = train_task_df.copy()
    global_mean = float(train_df["score"].mean())
    backbone_effect = train_df.groupby("backbone")["score"].mean().reindex(eval_matrix.columns) - global_mean
    train_df["residual"] = train_df.apply(
        lambda row: row["score"] - global_mean - float(backbone_effect[row["backbone"]]),
        axis=1,
    )
    language_mean = train_df.groupby("language")["residual"].mean().reindex(eval_matrix.index).fillna(0.0)
    centered = train_df["residual"] - train_df["language"].map(language_mean)
    pooled_var = float(np.var(centered.to_numpy(dtype=float), ddof=0))
    pooled_std = float(np.sqrt(pooled_var)) if pooled_var > 0 else 1.0
    language_counts = train_df.groupby("language").size().reindex(eval_matrix.index).fillna(0.0)
    tau2 = float(np.var(language_mean.to_numpy(dtype=float), ddof=0))
    gamma_shrunk = {}
    delta_shrunk = {}
    lang_scale = {}
    for language in eval_matrix.index:
        n_l = float(language_counts[language])
        gamma_l = float(language_mean[language])
        if n_l <= 0:
            gamma_shrunk[language] = 0.0
            delta_shrunk[language] = 1.0
            continue
        lambda_mean = tau2 / (tau2 + pooled_var / n_l) if (tau2 + pooled_var / n_l) > 0 else 0.0
        gamma_shrunk[language] = lambda_mean * gamma_l
        lang_resid = train_df.loc[train_df["language"] == language, "residual"].to_numpy(dtype=float) - gamma_l
        if len(lang_resid) > 1:
            delta_l = float(np.std(lang_resid, ddof=0) / pooled_std) if pooled_std > 0 else 1.0
        else:
            delta_l = 1.0
        lang_scale[language] = delta_l
    scale_values = np.array(list(lang_scale.values()), dtype=float)
    scale_var = float(np.var(scale_values, ddof=0))
    for language in eval_matrix.index:
        n_l = float(language_counts[language])
        delta_l = float(lang_scale.get(language, 1.0))
        lambda_scale = scale_var / (scale_var + 1.0 / max(n_l, 1.0)) if (scale_var + 1.0 / max(n_l, 1.0)) > 0 else 0.0
        delta_shrunk[language] = max(1e-6, 1.0 + lambda_scale * (delta_l - 1.0))

    adjusted = eval_matrix.copy()
    for language in adjusted.index:
        for backbone in adjusted.columns:
            alpha_b = float(backbone_effect[backbone])
            gamma_l = float(gamma_shrunk[language])
            delta_l = float(delta_shrunk[language])
            value = float(adjusted.loc[language, backbone])
            adjusted.loc[language, backbone] = global_mean + alpha_b + (value - global_mean - alpha_b - gamma_l) / delta_l
    return adjusted


def fit_dawid_skene(
    train_run_df: pd.DataFrame,
    task_weights: dict[str, int],
    max_iter: int = 25,
    smoothing: float = 1.0,
) -> dict:
    train_df = expand_rows_by_task_weights(train_run_df, task_weights)
    train_df = train_df.copy()
    train_df["item_id"] = train_df["task"] + "::" + train_df["framework"]
    train_df["annotator_id"] = train_df["language"] + "::" + train_df["backbone"]
    pivot = (
        train_df.pivot_table(index="item_id", columns="annotator_id", values="task_solved", aggfunc="mean")
        .sort_index(axis=1)
    )
    annotations = pivot.to_numpy(dtype=float)
    posterior = np.clip(np.nanmean(annotations, axis=1), 1e-3, 1 - 1e-3)
    prior = float(np.mean(posterior))
    annotators = list(pivot.columns)
    confusion = {annotator: {"sens": 0.7, "spec": 0.7} for annotator in annotators}

    for _ in range(max_iter):
        prior = float(np.clip(np.mean(posterior), 1e-3, 1 - 1e-3))
        for j, annotator in enumerate(annotators):
            obs = annotations[:, j]
            tp = float(np.sum(posterior * (obs == 1.0)))
            fn = float(np.sum(posterior * (obs == 0.0)))
            fp = float(np.sum((1.0 - posterior) * (obs == 1.0)))
            tn = float(np.sum((1.0 - posterior) * (obs == 0.0)))
            sens = (tp + smoothing) / (tp + fn + 2 * smoothing)
            spec = (tn + smoothing) / (tn + fp + 2 * smoothing)
            confusion[annotator] = {"sens": float(np.clip(sens, 1e-4, 1 - 1e-4)), "spec": float(np.clip(spec, 1e-4, 1 - 1e-4))}

        new_posterior = np.zeros_like(posterior)
        for i in range(len(posterior)):
            log_p1 = np.log(prior)
            log_p0 = np.log(1.0 - prior)
            for j, annotator in enumerate(annotators):
                obs = annotations[i, j]
                sens = confusion[annotator]["sens"]
                spec = confusion[annotator]["spec"]
                if obs == 1.0:
                    log_p1 += np.log(sens)
                    log_p0 += np.log(1.0 - spec)
                else:
                    log_p1 += np.log(1.0 - sens)
                    log_p0 += np.log(spec)
            max_log = max(log_p1, log_p0)
            p1 = np.exp(log_p1 - max_log)
            p0 = np.exp(log_p0 - max_log)
            new_posterior[i] = p1 / (p1 + p0)
        if np.max(np.abs(new_posterior - posterior)) < 1e-6:
            posterior = new_posterior
            break
        posterior = new_posterior

    return {"prior": prior, "confusion": confusion}


def dawid_skene_eval_matrix(
    eval_run_df: pd.DataFrame,
    ds_params: dict,
    backbones: list[str],
) -> pd.DataFrame:
    eval_df = eval_run_df.copy()
    eval_df["item_id"] = eval_df["task"] + "::" + eval_df["framework"]
    eval_df["annotator_id"] = eval_df["language"] + "::" + eval_df["backbone"]
    pivot = eval_df.pivot_table(index="item_id", columns="annotator_id", values="task_solved", aggfunc="mean")
    annotators = list(pivot.columns)
    posterior = {}
    prior = float(ds_params["prior"])
    confusion = ds_params["confusion"]
    for item_id, row in pivot.iterrows():
        log_p1 = np.log(np.clip(prior, 1e-4, 1 - 1e-4))
        log_p0 = np.log(np.clip(1.0 - prior, 1e-4, 1 - 1e-4))
        for annotator in annotators:
            obs = float(row[annotator])
            params = confusion[annotator]
            sens = params["sens"]
            spec = params["spec"]
            if obs == 1.0:
                log_p1 += np.log(sens)
                log_p0 += np.log(1.0 - spec)
            else:
                log_p1 += np.log(1.0 - sens)
                log_p0 += np.log(spec)
        max_log = max(log_p1, log_p0)
        p1 = np.exp(log_p1 - max_log)
        p0 = np.exp(log_p0 - max_log)
        posterior[item_id] = p1 / (p1 + p0)

    rows = []
    for annotator in annotators:
        language, backbone = annotator.split("::")
        obs = pivot[annotator].to_numpy(dtype=float)
        item_ids = list(pivot.index)
        accuracy = float(
            np.mean([
                posterior[item_id] if obs_val == 1.0 else 1.0 - posterior[item_id]
                for item_id, obs_val in zip(item_ids, obs)
            ])
        )
        rows.append({"language": language, "backbone": backbone, "score": 100.0 * accuracy})
    matrix_df = pd.DataFrame(rows)
    return matrix_df.pivot(index="language", columns="backbone", values="score").reindex(index=LANGUAGES, columns=backbones)


def random_control(matrix: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    shuffled = matrix.copy()
    for language in shuffled.index:
        shuffled.loc[language] = rng.permutation(shuffled.loc[language].to_numpy(dtype=float))
    return shuffled


def ensemble_baseline(matrix: pd.DataFrame, train_matrix: pd.DataFrame) -> pd.DataFrame:
    centered_rank = col_center(matrix, train_matrix).rank(axis=1, method="average", pct=True)
    z_rank = col_zscore(matrix, train_matrix).rank(axis=1, method="average", pct=True)
    q_rank = col_quantile(matrix, train_matrix).rank(axis=1, method="average", pct=True)
    return (centered_rank + z_rank + q_rank) / 3.0


def evaluate_method_matrix(
    method: str,
    full_task_df: pd.DataFrame,
    full_run_df: pd.DataFrame,
    eval_df: pd.DataFrame,
    eval_run_df: pd.DataFrame,
    eval_matrix: pd.DataFrame,
    train_matrix: pd.DataFrame,
    train_weights: dict[str, int],
    backbones: list[str],
    rng: np.random.Generator,
) -> pd.DataFrame:
    if method == "Raw (no calibration)":
        return eval_matrix
    if method == "Random control":
        return random_control(eval_matrix, rng)
    if method == "Per-language norm.":
        return row_zscore(eval_matrix)
    if method == "Backbone-only norm.":
        return col_center(eval_matrix, train_matrix)
    if method == "Z-score":
        return col_zscore(eval_matrix, train_matrix)
    if method == "Quantile normalization":
        return col_quantile(eval_matrix, train_matrix)
    if method == "ComBat-EB":
        train_task_df = expand_rows_by_task_weights(full_task_df, train_weights)
        return combat_eb_adjust(eval_matrix, train_task_df)
    if method == "Dawid-Skene EM":
        ds_params = fit_dawid_skene(
            full_run_df[full_run_df["backbone"].isin(backbones)].copy(),
            task_weights=train_weights,
        )
        return dawid_skene_eval_matrix(eval_run_df[eval_run_df["backbone"].isin(backbones)].copy(), ds_params, backbones)
    if method == "Ensemble":
        return ensemble_baseline(eval_matrix, train_matrix)
    if method == "CBC":
        return eval_matrix - compute_beta(full_task_df, task_weights=train_weights, backbones=backbones)
    if method == "CBC-Weighted":
        beta_weighted, _ = compute_weighted_beta(
            full_task_df,
            task_weights=train_weights,
            backbones=backbones,
        )
        return eval_matrix - beta_weighted
    if method == "Oracle (eval-task beta)":
        return eval_matrix - compute_beta(eval_df, backbones=backbones)
    raise ValueError(f"Unknown method: {method}")


def summarize_replicates(replicate_df: pd.DataFrame) -> pd.DataFrame:
    summary_rows = []
    for method, method_df in replicate_df.groupby("method"):
        taus = method_df["mean_pairwise_tau"].to_numpy(dtype=float)
        summary_rows.append(
            {
                "method": method,
                "mean_pairwise_tau": float(np.mean(taus)),
                "ci_low": float(np.percentile(taus, 2.5)),
                "ci_high": float(np.percentile(taus, 97.5)),
                "n_replicates": int(len(taus)),
            }
        )
    return pd.DataFrame(summary_rows).sort_values("mean_pairwise_tau", ascending=False)


def evaluate_calibration_methods(
    task_df: pd.DataFrame,
    run_df: pd.DataFrame,
    methods: list[str] | None = None,
    bootstrap_reps: int = BOOTSTRAP_REPS,
    seed: int = BOOTSTRAP_SEED,
    backbones: list[str] | None = None,
) -> tuple[pd.DataFrame, dict]:
    methods = TABLE2_METHODS if methods is None else list(methods)
    backbone_order = BACKBONE_ORDER if backbones is None else list(backbones)
    subset_df = task_df[task_df["backbone"].isin(backbone_order)].copy()
    subset_run_df = run_df[run_df["backbone"].isin(backbone_order)].copy()
    tasks = sorted(subset_df["task"].unique(), key=task_key)
    rng = np.random.default_rng(seed)
    replicate_rows: list[dict] = []
    skipped = 0

    for replicate in range(bootstrap_reps):
        train_weights, eval_tasks = bootstrap_task_split(tasks, rng)
        if not eval_tasks:
            skipped += 1
            continue

        eval_df = subset_df[subset_df["task"].isin(eval_tasks)].copy()
        eval_run_df = subset_run_df[subset_run_df["task"].isin(eval_tasks)].copy()
        eval_matrix = build_score_matrix(eval_df, backbones=backbone_order)
        train_matrix = build_score_matrix(subset_df, task_weights=train_weights, backbones=backbone_order)

        for method in methods:
            method_matrix = evaluate_method_matrix(
                method=method,
                full_task_df=subset_df,
                full_run_df=subset_run_df,
                eval_df=eval_df,
                eval_run_df=eval_run_df,
                eval_matrix=eval_matrix,
                train_matrix=train_matrix,
                train_weights=train_weights,
                backbones=backbone_order,
                rng=rng,
            )
            replicate_rows.append(
                {
                    "replicate": replicate,
                    "method": method,
                    "mean_pairwise_tau": mean_pairwise_kendall_tau(method_matrix),
                    "n_eval_tasks": len(eval_tasks),
                    "n_backbones": len(backbone_order),
                }
            )

    replicate_df = pd.DataFrame(replicate_rows)
    summary_df = summarize_replicates(replicate_df)
    payload = {
        "protocol": {
            "resampling": "bootstrap_train_oob_eval",
            "bootstrap_reps": bootstrap_reps,
            "seed": seed,
            "metric": "mean_pairwise_kendall_tau_across_languages",
            "skipped_replicates": skipped,
            "n_backbones": len(backbone_order),
        },
        "results": [
            {
                "method": row["method"],
                "mean_pairwise_tau": round(float(row["mean_pairwise_tau"]), 6),
                "ci_low": round(float(row["ci_low"]), 6),
                "ci_high": round(float(row["ci_high"]), 6),
                "n_replicates": int(row["n_replicates"]),
            }
            for row in summary_df.to_dict("records")
        ],
    }
    return replicate_df, payload


def run_backbone_ablation(task_df: pd.DataFrame, run_df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    subset_rows: list[dict] = []
    for m_size in range(2, len(BACKBONE_ORDER) + 1):
        for subset in combinations(BACKBONE_ORDER, m_size):
            _, payload = evaluate_calibration_methods(
                task_df,
                run_df,
                methods=["CBC"],
                bootstrap_reps=ABLATION_BOOTSTRAP_REPS,
                seed=BOOTSTRAP_SEED + m_size,
                backbones=list(subset),
            )
            tau = payload["results"][0]["mean_pairwise_tau"]
            subset_rows.append(
                {
                    "m": m_size,
                    "backbones": ",".join(subset),
                    "mean_pairwise_tau": tau,
                }
            )
    subset_df = pd.DataFrame(subset_rows)
    summary_rows = []
    for m_size, group_df in subset_df.groupby("m"):
        taus = group_df["mean_pairwise_tau"].to_numpy(dtype=float)
        summary_rows.append(
            {
                "m": int(m_size),
                "mean_pairwise_tau": float(np.mean(taus)),
                "std": float(np.std(taus, ddof=0)) if len(taus) > 1 else 0.0,
                "n_subsets": int(len(taus)),
            }
        )
    summary_df = pd.DataFrame(summary_rows).sort_values("m")
    payload = {
        "protocol": {
            "bootstrap_reps_per_subset": ABLATION_BOOTSTRAP_REPS,
            "metric": "mean_pairwise_kendall_tau_across_languages",
        },
        "summary": [
            {
                "m": int(row["m"]),
                "mean_pairwise_tau": round(float(row["mean_pairwise_tau"]), 6),
                "std": round(float(row["std"]), 6),
                "n_subsets": int(row["n_subsets"]),
            }
            for row in summary_df.to_dict("records")
        ],
    }
    return subset_df, payload


def run_task_ablation(task_df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    full_beta = compute_beta(task_df)
    rng = np.random.default_rng(BOOTSTRAP_SEED + 100)
    rows: list[dict] = []
    tasks = sorted(task_df["task"].unique(), key=task_key)
    for n_tasks in TASK_ABLATION_SIZES:
        for replicate in range(TASK_SUBSAMPLE_REPS):
            sampled_tasks = rng.choice(tasks, size=n_tasks, replace=False)
            subset_df = task_df[task_df["task"].isin(sampled_tasks)].copy()
            train_weights, eval_tasks = bootstrap_task_split(list(sampled_tasks), rng)
            if not eval_tasks:
                continue
            eval_df = subset_df[subset_df["task"].isin(eval_tasks)].copy()
            eval_matrix = build_score_matrix(eval_df)
            beta_hat = compute_beta(subset_df, task_weights=train_weights)
            calibrated = eval_matrix - beta_hat
            rows.append(
                {
                    "n_tasks": n_tasks,
                    "replicate": replicate,
                    "mean_pairwise_tau": mean_pairwise_kendall_tau(calibrated),
                    "mean_abs_beta_error": float((beta_hat - full_beta).abs().to_numpy().mean()),
                }
            )
    ablation_df = pd.DataFrame(rows)
    sigma_hat = float(np.sqrt(np.var(task_df["score"].to_numpy(dtype=float), ddof=0)))
    summary_rows = []
    for n_tasks, group_df in ablation_df.groupby("n_tasks"):
        summary_rows.append(
            {
                "n_tasks": int(n_tasks),
                "mean_pairwise_tau": float(group_df["mean_pairwise_tau"].mean()),
                "tau_std": float(group_df["mean_pairwise_tau"].std(ddof=0)),
                "mean_abs_beta_error": float(group_df["mean_abs_beta_error"].mean()),
                "error_std": float(group_df["mean_abs_beta_error"].std(ddof=0)),
                "theoretical_bound": float(
                    sigma_hat * np.sqrt(4.0 * np.log(60.0 / 0.05) / (9.0 * float(n_tasks)))
                ),
            }
        )
    summary_df = pd.DataFrame(summary_rows).sort_values("n_tasks")
    payload = {
        "protocol": {
            "task_subsample_reps": TASK_SUBSAMPLE_REPS,
            "metric": "mean_pairwise_kendall_tau_across_languages",
            "error_metric": "mean_abs_beta_error_vs_full_data_beta",
            "sigma_hat": round(sigma_hat, 6),
        },
        "summary": [
            {
                "n_tasks": int(row["n_tasks"]),
                "mean_pairwise_tau": round(float(row["mean_pairwise_tau"]), 6),
                "tau_std": round(float(row["tau_std"]), 6),
                "mean_abs_beta_error": round(float(row["mean_abs_beta_error"]), 6),
                "error_std": round(float(row["error_std"]), 6),
                "theoretical_bound": round(float(row["theoretical_bound"]), 6),
            }
            for row in summary_df.to_dict("records")
        ],
    }
    return ablation_df, payload


def load_requirement_type_module():
    module_path = ROOT / "scripts" / "generate_requirement_type_sensitivity.py"
    spec = importlib.util.spec_from_file_location("req_type_module", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_requirement_level_scores() -> pd.DataFrame:
    req_mod = load_requirement_type_module()
    requirement_type, _, _ = req_mod.build_requirement_type_map()
    rows: list[dict] = []
    for model_dir, backbone in BACKBONES.items():
        for language in LANGUAGES:
            for framework in FRAMEWORKS:
                gray_dir = (
                    BENCHMARK_TESTS
                    / model_dir
                    / language
                    / framework
                    / "judgment"
                    / framework
                    / "agent_as_a_judge"
                    / "gray_box"
                )
                if not gray_dir.exists():
                    continue
                for path in sorted(gray_dir.glob("*.json"), key=lambda p: task_key(p.stem)):
                    obj = json.loads(path.read_text(encoding="utf-8"))
                    task = obj.get("name", path.stem)
                    for stat in obj.get("judge_stats", []):
                        req_id = int(stat["requirement_index"])
                        rows.append(
                            {
                                "backbone": backbone,
                                "language": language,
                                "framework": framework,
                                "task": task,
                                "requirement_type": requirement_type[(task, req_id)],
                                "score": 100.0 * float(bool(stat.get("satisfied", False))),
                            }
                        )
    return pd.DataFrame(rows)


def aggregate_requirement_task_level(
    req_df: pd.DataFrame,
    included_types: set[str],
) -> pd.DataFrame:
    filtered = req_df[req_df["requirement_type"].isin(included_types)].copy()
    return (
        filtered.groupby(["task", "language", "backbone"], as_index=False)["score"]
        .mean()
        .rename(columns={"score": "score"})
    )


def run_requirement_type_decomposition(run_df: pd.DataFrame) -> dict:
    req_df = load_requirement_level_scores()
    type_sets = {
        "operational": {"Data Loading", "Training"},
        "semantic": {"Model Construction", "Evaluation Metrics"},
    }
    payload = {"protocol": {"bootstrap_reps": REQUIREMENT_BOOTSTRAP_REPS}, "splits": {}}
    for split_name, included_types in type_sets.items():
        split_task_df = aggregate_requirement_task_level(req_df, included_types)
        _, split_payload = evaluate_calibration_methods(
            split_task_df,
            run_df,
            methods=["Raw (no calibration)", "CBC", "CBC-Weighted"],
            bootstrap_reps=REQUIREMENT_BOOTSTRAP_REPS,
            seed=BOOTSTRAP_SEED + len(included_types),
        )
        payload["splits"][split_name] = {
            "included_types": sorted(included_types),
            "n_tasks": int(split_task_df["task"].nunique()),
            "results": split_payload["results"],
        }
    return payload


def classify_cbc_status(
    calibration_payload: dict,
    backbone_payload: dict,
    task_payload: dict,
    requirement_payload: dict,
) -> dict:
    result_map = {
        row["method"]: row["mean_pairwise_tau"]
        for row in calibration_payload["results"]
    }
    simple_baselines = [
        "Random control",
        "Per-language norm.",
        "Backbone-only norm.",
        "Z-score",
        "Quantile normalization",
        "ComBat-EB",
        "Dawid-Skene EM",
        "Ensemble",
    ]
    cbc_tau = float(result_map["CBC"])
    raw_tau = float(result_map["Raw (no calibration)"])
    baseline_best = max(float(result_map[method]) for method in simple_baselines)
    m_summary = {row["m"]: row["mean_pairwise_tau"] for row in backbone_payload["summary"]}
    n_summary = {row["n_tasks"]: row["mean_pairwise_tau"] for row in task_payload["summary"]}
    split_map = {
        split: {
            row["method"]: row["mean_pairwise_tau"]
            for row in split_payload["results"]
        }
        for split, split_payload in requirement_payload["splits"].items()
    }
    strong = (
        cbc_tau >= 0.8
        and cbc_tau - raw_tau >= 0.1
        and cbc_tau - baseline_best >= 0.05
        and m_summary.get(3, 0.0) >= 0.7
        and n_summary.get(20, 0.0) >= 0.7
    )
    partial = (
        cbc_tau > raw_tau
        and cbc_tau > baseline_best
    )
    if strong:
        verdict = "strong_success"
        rationale = "CBC clearly beats raw scores and simple baselines, and the gain persists under backbone and task ablations."
    elif partial:
        verdict = "partial_success"
        rationale = "CBC helps relative to raw scores, but the improvement is limited or brittle under at least one ablation."
    else:
        verdict = "failure"
        rationale = "CBC does not consistently outperform the strongest simple baselines or remain stable under ablation."
    return {
        "verdict": verdict,
        "rationale": rationale,
        "cbc_tau": round(cbc_tau, 6),
        "raw_tau": round(raw_tau, 6),
        "best_simple_baseline_tau": round(baseline_best, 6),
        "backbone_m3_tau": round(float(m_summary.get(3, float("nan"))), 6),
        "task_n20_tau": round(float(n_summary.get(20, float("nan"))), 6),
        "requirement_splits": split_map,
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    run_df = load_run_level_scores()
    task_df = aggregate_task_level(run_df)
    beta_df = compute_beta(task_df)
    delta_df = compute_rank_reversal(task_df)
    calibration_replicates_df, calibration_payload = evaluate_calibration_methods(task_df, run_df)
    backbone_ablation_df, backbone_ablation_payload = run_backbone_ablation(task_df, run_df)
    task_ablation_df, task_ablation_payload = run_task_ablation(task_df)
    requirement_payload = run_requirement_type_decomposition(run_df)
    cbc_status_payload = classify_cbc_status(
        calibration_payload,
        backbone_ablation_payload,
        task_ablation_payload,
        requirement_payload,
    )

    simplified = fit_ols_r2(
        run_df,
        include_framework=True,
        include_backbone_language=True,
        include_task_language=False,
    )
    full = fit_ols_r2(
        run_df,
        include_framework=True,
        include_backbone_language=True,
        include_task_language=True,
    )

    run_df.to_csv(OUTPUT_DIR / "run_level_scores.csv", index=False)
    task_df.to_csv(OUTPUT_DIR / "task_level_scores.csv", index=False)
    beta_df.to_csv(OUTPUT_DIR / "beta_hat.csv")
    delta_df.to_csv(OUTPUT_DIR / "rank_reversal_delta.csv", index=False)
    calibration_replicates_df.to_csv(OUTPUT_DIR / "calibration_bootstrap_replicates.csv", index=False)
    backbone_ablation_df.to_csv(OUTPUT_DIR / "ablation_backbones.csv", index=False)
    task_ablation_df.to_csv(OUTPUT_DIR / "ablation_tasks.csv", index=False)
    save_heatmap(beta_df)

    payload = {
        "dataset": {
            "n_run_rows": int(len(run_df)),
            "n_task_rows": int(len(task_df)),
            "languages": LANGUAGES,
            "backbones": BACKBONE_ORDER,
            "frameworks": FRAMEWORKS,
        },
        "beta_hat": {
            language: {
                backbone: round(float(beta_df.loc[language, backbone]), 6)
                for backbone in BACKBONE_ORDER
            }
            for language in LANGUAGES
        },
        "rank_reversal_delta": [
            {
                "backbone_i": row["backbone_i"],
                "backbone_j": row["backbone_j"],
                "language_a": row["language_a"],
                "language_b": row["language_b"],
                "d_a": round(float(row["d_a"]), 6),
                "d_b": round(float(row["d_b"]), 6),
                "product": round(float(row["product"]), 6),
                "delta": round(float(row["delta"]), 6),
                "rank_reversal": bool(row["rank_reversal"]),
            }
            for row in delta_df.to_dict("records")
        ],
        "ols": {
            "simplified": {k: (round(v, 6) if isinstance(v, float) else v) for k, v in simplified.items()},
            "full": {k: (round(v, 6) if isinstance(v, float) else v) for k, v in full.items()},
        },
        "calibration": calibration_payload,
        "ablation_backbones": backbone_ablation_payload,
        "ablation_tasks": task_ablation_payload,
        "requirement_type_decomposition": requirement_payload,
        "cbc_status": cbc_status_payload,
    }
    (OUTPUT_DIR / "meb_foundations.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
    (OUTPUT_DIR / "calibration_results.json").write_text(
        json.dumps(calibration_payload, indent=2),
        encoding="utf-8",
    )
    (OUTPUT_DIR / "ablation_backbones.json").write_text(
        json.dumps(backbone_ablation_payload, indent=2),
        encoding="utf-8",
    )
    (OUTPUT_DIR / "ablation_tasks.json").write_text(
        json.dumps(task_ablation_payload, indent=2),
        encoding="utf-8",
    )
    (OUTPUT_DIR / "requirement_type_cbc.json").write_text(
        json.dumps(requirement_payload, indent=2),
        encoding="utf-8",
    )
    (OUTPUT_DIR / "cbc_status.json").write_text(
        json.dumps(cbc_status_payload, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(payload["ols"], indent=2))
    print(json.dumps(calibration_payload, indent=2))
    print(json.dumps(cbc_status_payload, indent=2))
    print(f"Wrote outputs to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
