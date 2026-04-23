import json
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from agent_as_a_judge.languages import (
    ALL_LANGUAGES,
    FRAMEWORKS as DEFAULT_FRAMEWORKS,
)


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_TESTS = ROOT / "benchmark_tests"
OUTPUT_DIR = ROOT / "figures"
LANGUAGES = list(ALL_LANGUAGES)
FRAMEWORKS = list(DEFAULT_FRAMEWORKS)
FRAMEWORK_COLORS = {
    "MetaGPT": "#4C72B0",
    "GPT-Pilot": "#55A868",
    "OpenHands": "#C44E52",
}
LANGUAGE_COLORS = {
    "English": "#4C72B0",
    "Arabic": "#DD8452",
    "Turkish": "#55A868",
    "Chinese": "#8172B3",
    "Hindi": "#C44E52",
    "Japanese": "#937860",
    "Spanish": "#DA8BC3",
    "Swahili": "#8C8C8C",
}
FRAMEWORK_MARKERS = {"MetaGPT": "o", "GPT-Pilot": "s", "OpenHands": "^"}


def task_key(name: str):
    prefix = name.split("_", 1)[0]
    try:
        return (int(prefix), name)
    except ValueError:
        return (9999, name)


def load_data():
    data = defaultdict(lambda: defaultdict(dict))
    all_tasks = defaultdict(set)

    for lang_dir in BENCHMARK_TESTS.iterdir():
        if not lang_dir.is_dir():
            continue
        lang = lang_dir.name
        for fw in FRAMEWORKS:
            gray_dir = (
                lang_dir / fw / "judgment" / fw / "agent_as_a_judge" / "gray_box"
            )
            if not gray_dir.exists():
                continue
            for file_path in sorted(gray_dir.glob("*.json")):
                try:
                    obj = json.loads(file_path.read_text(encoding="utf-8"))
                except Exception:
                    continue
                task = obj.get("name", file_path.stem)
                data[lang][fw][task] = obj
                all_tasks[lang].add(task)

    return data, {k: sorted(v, key=task_key) for k, v in all_tasks.items()}


def compute_task_metrics(obj):
    stats = obj.get("judge_stats", []) or []
    if not stats:
        return None

    satisfied = 0
    time_vals = []
    input_vals = []
    output_vals = []
    for stat in stats:
        if bool(stat.get("satisfied", False)):
            satisfied += 1
        llm = stat.get("llm_stats", {}) or {}
        time_vals.append(float(stat.get("total_time", 0.0)))
        input_vals.append(float(llm.get("input_tokens", 0)))
        output_vals.append(float(llm.get("output_tokens", 0)))

    n = len(stats)
    return {
        "num_requirements": n,
        "num_satisfied": satisfied,
        "task_satisfaction_rate": 100.0 * satisfied / n,
        "task_solved": 1 if satisfied == n else 0,
        "task_time_sum": sum(time_vals),
        "task_input_tokens_sum": sum(input_vals),
        "task_output_tokens_sum": sum(output_vals),
    }


def build_dataframes(data, all_tasks):
    combo_rows = []
    task_rows = []

    for lang in LANGUAGES:
        tasks = all_tasks.get(lang, [])
        for fw in FRAMEWORKS:
            task_metrics = []
            for task in tasks:
                obj = data.get(lang, {}).get(fw, {}).get(task)
                if not obj:
                    continue
                metrics = compute_task_metrics(obj)
                if not metrics:
                    continue
                task_rows.append(
                    {
                        "language": lang,
                        "framework": fw,
                        "task": task,
                        **metrics,
                    }
                )
                task_metrics.append(metrics)

            if not task_metrics:
                continue

            combo_rows.append(
                {
                    "language": lang,
                    "framework": fw,
                    "satisfaction_rate": 100.0
                    * sum(m["num_satisfied"] for m in task_metrics)
                    / sum(m["num_requirements"] for m in task_metrics),
                    "tsr": 100.0 * np.mean([m["task_solved"] for m in task_metrics]),
                    "avg_time": np.mean([m["task_time_sum"] for m in task_metrics]),
                    "avg_input_tokens": np.mean(
                        [m["task_input_tokens_sum"] for m in task_metrics]
                    ),
                    "avg_output_tokens": np.mean(
                        [m["task_output_tokens_sum"] for m in task_metrics]
                    ),
                    "median_task_satisfaction": np.median(
                        [m["task_satisfaction_rate"] for m in task_metrics]
                    ),
                    "task_satisfaction_std": np.std(
                        [m["task_satisfaction_rate"] for m in task_metrics]
                    ),
                }
            )

    combo_df = pd.DataFrame(combo_rows)
    task_df = pd.DataFrame(task_rows)
    return combo_df, task_df


def build_summary(combo_df, task_df):
    summary = {}

    best_sat = combo_df.loc[combo_df["satisfaction_rate"].idxmax()]
    worst_sat = combo_df.loc[combo_df["satisfaction_rate"].idxmin()]
    best_tsr = combo_df.loc[combo_df["tsr"].idxmax()]
    lightest = combo_df.loc[combo_df["avg_input_tokens"].idxmin()]
    heaviest = combo_df.loc[combo_df["avg_input_tokens"].idxmax()]
    fastest = combo_df.loc[combo_df["avg_time"].idxmin()]
    slowest = combo_df.loc[combo_df["avg_time"].idxmax()]

    framework_robustness = (
        combo_df.groupby("framework")["satisfaction_rate"]
        .agg(["mean", "std", "min", "max"])
        .reset_index()
        .sort_values("std")
    )
    language_means = (
        combo_df.groupby("language")["satisfaction_rate"].mean().sort_values(ascending=False)
    )

    task_distribution = (
        task_df.groupby(["language", "framework"])["task_satisfaction_rate"]
        .agg(["median", "std"])
        .reset_index()
    )

    summary["best_satisfaction"] = best_sat.to_dict()
    summary["worst_satisfaction"] = worst_sat.to_dict()
    summary["best_tsr"] = best_tsr.to_dict()
    summary["lightest_input_setting"] = lightest.to_dict()
    summary["heaviest_input_setting"] = heaviest.to_dict()
    summary["fastest_setting"] = fastest.to_dict()
    summary["slowest_setting"] = slowest.to_dict()
    summary["framework_robustness"] = framework_robustness.to_dict(orient="records")
    summary["language_mean_satisfaction"] = language_means.to_dict()
    summary["task_distribution"] = task_distribution.to_dict(orient="records")
    return summary


def plot_satisfaction_heatmap(combo_df):
    pivot = combo_df.pivot(index="language", columns="framework", values="satisfaction_rate")
    plt.figure(figsize=(6.4, 4.6))
    sns.heatmap(
        pivot.loc[LANGUAGES, FRAMEWORKS],
        annot=True,
        fmt=".2f",
        cmap="Blues",
        linewidths=0.7,
        cbar_kws={"label": "Requirement satisfaction (%)"},
    )
    plt.title("Requirement Satisfaction by Language and Framework")
    plt.xlabel("")
    plt.ylabel("")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "multilingual_satisfaction_heatmap.png", dpi=300, bbox_inches="tight")
    plt.close()


def plot_tsr_heatmap(combo_df):
    pivot = combo_df.pivot(index="language", columns="framework", values="tsr")
    plt.figure(figsize=(6.4, 4.6))
    sns.heatmap(
        pivot.loc[LANGUAGES, FRAMEWORKS],
        annot=True,
        fmt=".2f",
        cmap="Oranges",
        linewidths=0.7,
        cbar_kws={"label": "Task solve rate (%)"},
        vmin=0,
        vmax=max(4.0, float(combo_df["tsr"].max())),
    )
    plt.title("Task Solve Rate by Language and Framework")
    plt.xlabel("")
    plt.ylabel("")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "multilingual_tsr_heatmap.png", dpi=300, bbox_inches="tight")
    plt.close()


def plot_framework_robustness(combo_df):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), gridspec_kw={"width_ratios": [1.6, 1]})

    for fw in FRAMEWORKS:
        subset = combo_df[combo_df["framework"] == fw].set_index("language").loc[LANGUAGES]
        axes[0].plot(
            LANGUAGES,
            subset["satisfaction_rate"],
            marker=FRAMEWORK_MARKERS[fw],
            linewidth=2,
            markersize=7,
            color=FRAMEWORK_COLORS[fw],
            label=fw,
        )
    axes[0].set_title("Cross-Language Satisfaction Profiles")
    axes[0].set_ylabel("Requirement satisfaction (%)")
    axes[0].grid(axis="y", linestyle="--", alpha=0.35)
    axes[0].legend(frameon=False, loc="best")

    robustness = (
        combo_df.groupby("framework")["satisfaction_rate"].std().reindex(FRAMEWORKS)
    )
    axes[1].bar(
        robustness.index,
        robustness.values,
        color=[FRAMEWORK_COLORS[fw] for fw in robustness.index],
    )
    axes[1].set_title("Cross-Language Variability")
    axes[1].set_ylabel("Std. dev. across languages")
    axes[1].grid(axis="y", linestyle="--", alpha=0.35)
    axes[1].tick_params(axis="x", rotation=15)

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "multilingual_framework_robustness.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_task_distribution(task_df):
    plt.figure(figsize=(11.2, 4.8))
    sns.boxplot(
        data=task_df,
        x="language",
        y="task_satisfaction_rate",
        hue="framework",
        hue_order=FRAMEWORKS,
        order=LANGUAGES,
        palette=FRAMEWORK_COLORS,
        showfliers=False,
    )
    plt.title("Task-Level Satisfaction Distribution Across 55 Tasks")
    plt.xlabel("")
    plt.ylabel("Per-task requirement satisfaction (%)")
    plt.ylim(0, 105)
    plt.grid(axis="y", linestyle="--", alpha=0.3)
    plt.legend(title="", ncol=3, frameon=False, loc="upper center")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "multilingual_task_distribution_boxplot.png", dpi=300, bbox_inches="tight")
    plt.close()


def plot_runtime_token_panels(combo_df):
    fig, axes = plt.subplots(1, 3, figsize=(14.5, 4.3), sharex=True)
    metrics = [
        ("avg_time", "Avg. Time (s)"),
        ("avg_input_tokens", "Avg. Input Tokens"),
        ("avg_output_tokens", "Avg. Output Tokens"),
    ]
    x = np.arange(len(LANGUAGES))
    width = 0.23

    for ax, (metric, title) in zip(axes, metrics):
        for i, fw in enumerate(FRAMEWORKS):
            subset = combo_df[combo_df["framework"] == fw].set_index("language").loc[LANGUAGES]
            ax.bar(
                x + (i - 1) * width,
                subset[metric].values,
                width=width,
                color=FRAMEWORK_COLORS[fw],
                label=fw if ax is axes[0] else None,
            )
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels(LANGUAGES, rotation=20)
        ax.grid(axis="y", linestyle="--", alpha=0.3)

    axes[0].set_ylabel("Value")
    axes[0].legend(frameon=False, ncol=3, loc="upper left")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "multilingual_runtime_token_panels.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_efficiency_scatter(combo_df):
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.3))

    for lang in LANGUAGES:
        subset = combo_df[combo_df["language"] == lang]
        for _, row in subset.iterrows():
            axes[0].scatter(
                row["avg_input_tokens"],
                row["satisfaction_rate"],
                s=130,
                marker=FRAMEWORK_MARKERS[row["framework"]],
                color=LANGUAGE_COLORS[lang],
                edgecolor="black",
                linewidth=0.5,
                alpha=0.9,
            )
            axes[0].annotate(
                f"{lang[:2]}-{row['framework'][0]}",
                (row["avg_input_tokens"], row["satisfaction_rate"]),
                textcoords="offset points",
                xytext=(4, 4),
                fontsize=7,
            )

    for fw in FRAMEWORKS:
        subset = combo_df[combo_df["framework"] == fw]
        axes[1].plot(
            subset["avg_time"],
            subset["satisfaction_rate"],
            linestyle="",
            marker=FRAMEWORK_MARKERS[fw],
            markersize=8,
            color=FRAMEWORK_COLORS[fw],
            label=fw,
        )
        for _, row in subset.iterrows():
            axes[1].annotate(
                row["language"][:2],
                (row["avg_time"], row["satisfaction_rate"]),
                textcoords="offset points",
                xytext=(4, 4),
                fontsize=7,
            )

    axes[0].set_title("Input Tokens vs. Satisfaction")
    axes[0].set_xlabel("Avg. input tokens")
    axes[0].set_ylabel("Requirement satisfaction (%)")
    axes[0].grid(linestyle="--", alpha=0.3)

    axes[1].set_title("Runtime vs. Satisfaction")
    axes[1].set_xlabel("Avg. time (s)")
    axes[1].set_ylabel("Requirement satisfaction (%)")
    axes[1].grid(linestyle="--", alpha=0.3)
    axes[1].legend(frameon=False, loc="lower right")

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "multilingual_efficiency_scatter.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def main():
    sns.set_theme(style="whitegrid", context="paper")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    data, all_tasks = load_data()
    combo_df, task_df = build_dataframes(data, all_tasks)

    plot_satisfaction_heatmap(combo_df)
    plot_tsr_heatmap(combo_df)
    plot_framework_robustness(combo_df)
    plot_task_distribution(task_df)
    plot_runtime_token_panels(combo_df)
    plot_efficiency_scatter(combo_df)

    summary = build_summary(combo_df, task_df)
    (OUTPUT_DIR / "multilingual_plot_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    combo_df.to_csv(OUTPUT_DIR / "multilingual_plot_metrics.csv", index=False)
    task_df.to_csv(OUTPUT_DIR / "multilingual_task_metrics.csv", index=False)

    print(f"Wrote figures to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
