from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kendalltau


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = (
    ROOT
    / "Project-2"
    / "paper_acl"
    / "analysis"
    / "external_validation"
    / "mrewardbench_en_ar_100_exact_ids"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help="Directory containing per-model M-REWARDBENCH pilot outputs.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory to store merged pilot analysis outputs. Defaults to <input-dir>/analysis.",
    )
    parser.add_argument(
        "--bootstrap-reps",
        type=int,
        default=1000,
        help="Number of bootstrap train/OOB replicates.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=7,
        help="Random seed for bootstrap resampling.",
    )
    return parser.parse_args()


def bootstrap_task_split(tasks: list[str], rng: np.random.Generator) -> tuple[dict[str, int], list[str]]:
    sampled = rng.choice(tasks, size=len(tasks), replace=True)
    train_weights = {task: 0 for task in tasks}
    for task in sampled:
        train_weights[str(task)] += 1
    eval_tasks = [task for task in tasks if train_weights[task] == 0]
    return train_weights, eval_tasks


def summarize_metric(values: np.ndarray) -> dict[str, float | int]:
    return {
        "mean": float(np.mean(values)),
        "ci_low": float(np.percentile(values, 2.5)),
        "ci_high": float(np.percentile(values, 97.5)),
        "n_replicates": int(len(values)),
    }


def mean_pairwise_kendall_tau(score_matrix: pd.DataFrame) -> float:
    taus: list[float] = []
    for left, right in combinations(list(score_matrix.index), 2):
        tau, _ = kendalltau(score_matrix.loc[left].to_numpy(), score_matrix.loc[right].to_numpy())
        if not np.isnan(tau):
            taus.append(float(tau))
    if not taus:
        return 0.0
    return float(np.mean(taus))


def build_score_matrix(
    task_df: pd.DataFrame,
    languages: list[str],
    backbones: list[str],
    task_weights: dict[str, int] | None = None,
) -> pd.DataFrame:
    matrix_df = task_df.copy()
    if task_weights is None:
        grouped = matrix_df.groupby(["language", "backbone"], as_index=False)["score"].mean()
    else:
        matrix_df["weight"] = matrix_df["task"].map(task_weights).fillna(0).astype(int)
        matrix_df = matrix_df[matrix_df["weight"] > 0].copy()
        matrix_df["weighted_score"] = matrix_df["score"] * matrix_df["weight"]
        grouped = (
            matrix_df.groupby(["language", "backbone"], as_index=False)[["weighted_score", "weight"]].sum()
        )
        grouped["score"] = grouped["weighted_score"] / grouped["weight"]
        grouped = grouped[["language", "backbone", "score"]]

    matrix = grouped.pivot(index="language", columns="backbone", values="score").reindex(
        index=languages,
        columns=backbones,
    )
    if matrix.isna().any().any():
        raise ValueError("Score matrix contains missing values after complete-case filtering.")
    return matrix


def compute_beta_from_matrix(score_means: pd.DataFrame) -> pd.DataFrame:
    row_means = score_means.mean(axis=1)
    col_means = score_means.mean(axis=0)
    grand_mean = float(score_means.to_numpy(dtype=float).mean())
    return score_means.sub(row_means, axis=0).sub(col_means, axis=1) + grand_mean


def load_model_outputs(input_dir: Path) -> tuple[pd.DataFrame, list[str], list[str]]:
    metadata_paths = sorted(input_dir.glob("*/run_metadata.json"))
    if not metadata_paths:
        raise FileNotFoundError(f"No run_metadata.json files found under {input_dir}")

    margin_frames: list[pd.DataFrame] = []
    languages: list[str] | None = None
    model_order: list[str] = []

    for meta_path in metadata_paths:
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        if languages is None:
            languages = list(metadata["languages"])
        elif list(metadata["languages"]) != languages:
            raise ValueError(f"Language mismatch in {meta_path}")

        model_name = str(metadata["models"][0])
        model_order.append(model_name)

        margin_path = meta_path.with_name("run_pair_margins.csv")
        margin_df = pd.read_csv(margin_path)
        margin_df["evaluator_model"] = margin_df["evaluator_model"].astype(str)
        margin_df["language"] = margin_df["language"].astype(str)
        margin_df["item_id"] = margin_df["item_id"].astype(str)
        margin_df["margin"] = margin_df["margin"].astype(float)
        margin_frames.append(margin_df)

    assert languages is not None
    merged = pd.concat(margin_frames, ignore_index=True)
    return merged, languages, model_order


def restrict_to_complete_tasks(
    merged_df: pd.DataFrame,
    languages: list[str],
    backbones: list[str],
) -> pd.DataFrame:
    expected = len(languages) * len(backbones)
    per_task = (
        merged_df.groupby("item_id")
        .agg(
            n_rows=("margin", "size"),
            n_languages=("language", "nunique"),
            n_backbones=("evaluator_model", "nunique"),
        )
        .reset_index()
    )
    keep_tasks = per_task[
        (per_task["n_rows"] == expected)
        & (per_task["n_languages"] == len(languages))
        & (per_task["n_backbones"] == len(backbones))
    ]["item_id"]

    filtered = merged_df[merged_df["item_id"].isin(set(keep_tasks))].copy()
    dupes = filtered.duplicated(subset=["item_id", "language", "evaluator_model"])
    if dupes.any():
        raise ValueError("Duplicate item/language/model rows found after merging.")
    return filtered


def run_bootstrap_comparison(
    task_df: pd.DataFrame,
    languages: list[str],
    backbones: list[str],
    bootstrap_reps: int,
    seed: int,
) -> tuple[pd.DataFrame, dict]:
    tasks = sorted(task_df["task"].unique())
    rng = np.random.default_rng(seed)
    replicate_rows: list[dict] = []
    skipped = 0

    for replicate in range(bootstrap_reps):
        train_weights, eval_tasks = bootstrap_task_split(tasks, rng)
        if not eval_tasks:
            skipped += 1
            continue

        eval_df = task_df[task_df["task"].isin(eval_tasks)].copy()
        eval_matrix = build_score_matrix(eval_df, languages=languages, backbones=backbones)
        beta_hat = compute_beta_from_matrix(
            build_score_matrix(task_df, languages=languages, backbones=backbones, task_weights=train_weights)
        )
        cbc_matrix = eval_matrix - beta_hat

        raw_tau = mean_pairwise_kendall_tau(eval_matrix)
        cbc_tau = mean_pairwise_kendall_tau(cbc_matrix)
        replicate_rows.append(
            {
                "replicate": replicate,
                "raw_tau": raw_tau,
                "cbc_tau": cbc_tau,
                "tau_gain": cbc_tau - raw_tau,
                "n_eval_tasks": len(eval_tasks),
            }
        )

    replicate_df = pd.DataFrame(replicate_rows)
    raw_summary = summarize_metric(replicate_df["raw_tau"].to_numpy(dtype=float))
    cbc_summary = summarize_metric(replicate_df["cbc_tau"].to_numpy(dtype=float))
    gain_summary = summarize_metric(replicate_df["tau_gain"].to_numpy(dtype=float))

    payload = {
        "protocol": {
            "resampling": "bootstrap_train_oob_eval",
            "bootstrap_reps": bootstrap_reps,
            "seed": seed,
            "skipped_replicates": skipped,
            "metric": "mean_pairwise_kendall_tau_across_languages",
            "n_tasks_complete_panel": int(len(tasks)),
            "n_languages": len(languages),
            "n_backbones": len(backbones),
        },
        "results": {
            "Raw": raw_summary,
            "CBC": cbc_summary,
            "CBC_minus_Raw": gain_summary,
        },
    }
    return replicate_df, payload


def rank_backbones(matrix: pd.DataFrame) -> dict[str, list[str]]:
    ranking = {}
    for language in matrix.index:
        order = matrix.loc[language].sort_values(ascending=False, kind="stable").index.tolist()
        ranking[str(language)] = [str(backbone) for backbone in order]
    return ranking


def main() -> None:
    args = parse_args()
    input_dir = args.input_dir.resolve()
    output_dir = (args.output_dir or (input_dir / "analysis")).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    merged_df, languages, backbones = load_model_outputs(input_dir)
    complete_df = restrict_to_complete_tasks(merged_df, languages=languages, backbones=backbones)
    task_df = complete_df.rename(columns={"item_id": "task", "evaluator_model": "backbone", "margin": "score"})[
        ["task", "language", "backbone", "score", "subset", "chosen_model", "rejected_model", "pref_correct"]
    ].copy()

    full_raw_matrix = build_score_matrix(task_df, languages=languages, backbones=backbones)
    beta_hat = compute_beta_from_matrix(full_raw_matrix)
    full_cbc_matrix = full_raw_matrix - beta_hat
    replicate_df, payload = run_bootstrap_comparison(
        task_df=task_df,
        languages=languages,
        backbones=backbones,
        bootstrap_reps=args.bootstrap_reps,
        seed=args.seed,
    )

    merged_path = output_dir / "pilot_complete_panel.csv"
    raw_matrix_path = output_dir / "raw_mean_matrix.csv"
    beta_path = output_dir / "beta_hat.csv"
    cbc_matrix_path = output_dir / "cbc_mean_matrix.csv"
    replicate_path = output_dir / "raw_vs_cbc_bootstrap_replicates.csv"
    summary_path = output_dir / "raw_vs_cbc_summary.json"

    complete_df.to_csv(merged_path, index=False)
    full_raw_matrix.to_csv(raw_matrix_path)
    beta_hat.to_csv(beta_path)
    full_cbc_matrix.to_csv(cbc_matrix_path)
    replicate_df.to_csv(replicate_path, index=False)

    summary_payload = {
        **payload,
        "full_panel": {
            "languages": languages,
            "backbones": backbones,
            "n_complete_tasks": int(task_df["task"].nunique()),
            "raw_tau_full_panel": mean_pairwise_kendall_tau(full_raw_matrix),
            "cbc_tau_full_panel": mean_pairwise_kendall_tau(full_cbc_matrix),
            "backbone_rankings_raw": rank_backbones(full_raw_matrix),
            "backbone_rankings_cbc": rank_backbones(full_cbc_matrix),
        },
        "outputs": {
            "complete_panel_csv": str(merged_path),
            "raw_mean_matrix_csv": str(raw_matrix_path),
            "beta_hat_csv": str(beta_path),
            "cbc_mean_matrix_csv": str(cbc_matrix_path),
            "replicates_csv": str(replicate_path),
        },
    }
    summary_path.write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")
    print(json.dumps(summary_payload, indent=2))


if __name__ == "__main__":
    main()
