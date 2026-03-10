import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_TESTS = ROOT / "benchmark_tests"
LANGUAGES = ["English", "Arabic", "Turkish", "Chinese", "Hindi"]
FRAMEWORKS = ["MetaGPT", "GPT-Pilot", "OpenHands"]


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

    for lang, tasks in all_tasks.items():
        all_tasks[lang] = sorted(tasks, key=task_key)

    return data, all_tasks


def build_paper_markdown(all_tasks):
    lines = []
    lines.append(
        "# Agent-as-a-Judge Beyond English: Multilingual Prompt Localization for Requirement-Level Evaluation"
    )
    lines.append("")
    lines.append("## Abstract")
    lines.append(
        "We extend Agent-as-a-Judge to support multilingual judging prompts beyond English, targeting a key deployment limitation identified in prior analyses: all system prompts were English-only and raised `NotImplementedError` for non-English languages. We provide localized prompting for English, Arabic, Turkish, Chinese, and Hindi. Our evaluation uses the DevAI benchmark (55 tasks, requirement-level judging) and compares three developer-agent frameworks (MetaGPT, GPT-Pilot, OpenHands). We report per-requirement and task-level judge statistics including satisfaction, total time, and token usage. To ensure full transparency, we provide exhaustive task-level tables for all supported languages."
    )
    lines.append("")
    lines.append("## 1. Introduction")
    lines.append(
        "Agent-as-a-Judge (AAAJ) improves over single-shot LLM judging by collecting and reasoning over richer evidence (workspace structure, file contents, and trajectories), producing requirement-level pass/fail decisions. This design is especially important for long-horizon software tasks where final-output-only metrics hide intermediate failures. However, existing AAAJ deployments have a practical usability gap: core system prompts are English-only. In multilingual settings, this forces users to translate requirements into English or prevents execution entirely when the prompt stack throws language-related exceptions."
    )
    lines.append("")
    lines.append(
        "This work addresses that limitation through multilingual prompt localization. We adapt judge-side prompts so the system can consume and produce evidence-grounded decisions in the user's preferred language. Concretely, we evaluate five languages end-to-end on DevAI: English, Arabic, Turkish, Chinese, and Hindi."
    )
    lines.append("")
    lines.append(
        "Our contribution is practical and evaluation-centric: (1) a multilingual prompt layer for AAAJ modules previously restricted to English, (2) a reproducible multilingual evaluation protocol over 55 development tasks and 3 developer-agent frameworks, and (3) comprehensive per-task/per-requirement judge-stat tables that expose satisfaction, latency, and token consumption outcomes for each language setting. This artifact is intended both as an ICML-style report draft and as an auditable benchmark appendix for future multilingual judge research."
    )
    lines.append("")
    lines.append("## 2. Experimental Setup")
    lines.append(
        "- **Benchmark**: DevAI-style task suite with 55 tasks and requirement-level judgments."
    )
    lines.append(
        "- **Developer agents under evaluation**: `MetaGPT`, `GPT-Pilot`, and `OpenHands`."
    )
    lines.append(
        "- **Languages**: `English`, `Arabic`, `Turkish`, `Chinese`, `Hindi`."
    )
    lines.append(
        "- **Granularity**: requirement-level records from each task JSON `judge_stats` entry."
    )
    lines.append(
        "- **Reported metrics**: requirement-level `satisfied`; task-level averages over `total_time`, `input_tokens`, and `output_tokens`."
    )
    lines.append("")
    lines.append("## 3. Experiments")
    lines.append(
        "The full experiments are reported in `ICML_multilingual_experiments_tables.md`, organized as language-specific sections. Each language section includes all 55 tasks on the y-axis (task names), framework columns on the x-axis (`MetaGPT`, `GPT-Pilot`, `OpenHands`), and requirement-split rows (`R0`, `R1`, ... as needed). Each framework cell contains:"
    )
    lines.append("")
    lines.append("- `Sat` (Y/N),")
    lines.append("- `Time` (seconds),")
    lines.append("- `Input Tokens` (input tokens),")
    lines.append("- `Output Tokens` (output tokens).")
    lines.append("")
    lines.append(
        "For readability, each language section provides two complementary tables: (1) requirement-level SATISFIED/UNSATISFIED outcomes, and (2) task-level averaged runtime/token metrics."
    )
    lines.append("")
    lines.append("### 3.1 Language Coverage Status")
    for lang in LANGUAGES:
        n_tasks = len(all_tasks.get(lang, []))
        status = (
            "complete"
            if n_tasks == 55
            else ("partial" if n_tasks > 0 else "not yet available")
        )
        lines.append(f"- `{lang}`: {status} ({n_tasks}/55 tasks found).")
    lines.append("")
    lines.append("### 3.2 Reproducibility Note")
    lines.append(
        "All tables are auto-generated directly from benchmark result JSON files under `benchmark_tests/<Language>/<Framework>/judgment/<Framework>/agent_as_a_judge/gray_box/`. This prevents transcription errors and keeps the paper appendix synchronized with benchmark outputs."
    )
    lines.append("")
    lines.append("## 4. Limitations and Next Steps")
    lines.append(
        "- This draft focuses on requirement-level judge statistics rather than aggregate significance tests; future versions can add per-language aggregate deltas and confidence intervals."
    )
    lines.append(
        "- Current comparisons are framework-consistent but model/backend settings should be explicitly normalized and logged in the camera-ready version."
    )
    lines.append("")
    return "\n".join(lines)


def fmt_cell(entry):
    if not entry:
        return "N/A"
    sat = "Y" if bool(entry.get("satisfied", False)) else "N"
    llm = entry.get("llm_stats", {}) or {}
    time_s = llm.get("inference_time", 0.0)
    input_tokens = llm.get("input_tokens", 0)
    output_tokens = llm.get("output_tokens", 0)
    return (
        f"Sat={sat}; Time={time_s:.2f}s; "
        f"Input Tokens={input_tokens}; Output Tokens={output_tokens}"
    )


def latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    out = []
    for ch in text:
        out.append(replacements.get(ch, ch))
    return "".join(out)


def fmt_cell_latex(entry):
    if not entry:
        return r"\textit{N/A}"
    sat = "Y" if bool(entry.get("satisfied", False)) else "N"
    llm = entry.get("llm_stats", {}) or {}
    time_s = llm.get("inference_time", 0.0)
    input_tokens = llm.get("input_tokens", 0)
    output_tokens = llm.get("output_tokens", 0)
    text = (
        f"Sat={sat}; "
        f"Time={time_s:.2f}s; Input Tokens={input_tokens}; Output Tokens={output_tokens}"
    )
    return latex_escape(text)


def build_tables_markdown(data, all_tasks):
    out = []
    out.append("# Comprehensive Multilingual Experiments Tables")
    out.append("")
    out.append("For each language, two tables are provided:")
    out.append("1. Requirement-level `SATISFIED`/`UNSATISFIED` outcomes.")
    out.append(
        "2. Task-level averaged metrics over requirements: `Time` (from `total_time`), `Input Tokens`, `Output Tokens`."
    )
    out.append("")

    for lang in LANGUAGES:
        tasks = all_tasks.get(lang, [])
        out.append(f"## {lang}")
        if not tasks:
            out.append("No complete gray-box judgment files found yet for this language.")
            out.append("")
            continue

        # Table 1: Requirement-level satisfaction.
        out.append("### Requirement-Level Satisfaction")
        out.append("")
        out.append("| Task | Req | MetaGPT | GPT-Pilot | OpenHands |")
        out.append("|---|---:|---|---|---|")

        for task in tasks:
            fw_stats = {}
            req_set = set()
            for fw in FRAMEWORKS:
                obj = data.get(lang, {}).get(fw, {}).get(task)
                stats = {}
                if obj:
                    for stat in obj.get("judge_stats", []) or []:
                        req_idx = stat.get("requirement_index")
                        if isinstance(req_idx, int):
                            stats[req_idx] = stat
                            req_set.add(req_idx)
                fw_stats[fw] = stats

            req_indices = sorted(req_set)
            task_label = task.split("_", 1)[0]
            if not req_indices:
                out.append(f"| {task_label} | - | N/A | N/A | N/A |")
                continue

            for idx, req_idx in enumerate(req_indices):
                task_cell = task_label if idx == 0 else ""
                row = []
                for fw in FRAMEWORKS:
                    stat = fw_stats[fw].get(req_idx)
                    if not stat:
                        row.append("N/A")
                    else:
                        row.append(
                            "SATISFIED"
                            if bool(stat.get("satisfied", False))
                            else "UNSATISFIED"
                        )
                out.append(
                    f"| {task_cell} | R{req_idx} | {row[0]} | {row[1]} | {row[2]} |"
                )
            out.append("|  |  |  |  |  |")

        out.append("")

        # Table 2: Task-level averaged metrics.
        out.append("### Task-Level Averaged Metrics")
        out.append("")
        out.append(
            "| Task | MetaGPT Time | MetaGPT Input Tokens | MetaGPT Output Tokens | GPT-Pilot Time | GPT-Pilot Input Tokens | GPT-Pilot Output Tokens | OpenHands Time | OpenHands Input Tokens | OpenHands Output Tokens |"
        )
        out.append(
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
        )

        for task in tasks:
            task_label = task.split("_", 1)[0]
            metric_cells = []
            for fw in FRAMEWORKS:
                obj = data.get(lang, {}).get(fw, {}).get(task)
                if not obj:
                    metric_cells.extend(["N/A", "N/A", "N/A"])
                    continue
                stats = obj.get("judge_stats", []) or []
                if not stats:
                    metric_cells.extend(["N/A", "N/A", "N/A"])
                    continue

                time_vals = []
                input_vals = []
                output_vals = []
                for stat in stats:
                    llm = stat.get("llm_stats", {}) or {}
                    time_vals.append(float(stat.get("total_time", 0.0)))
                    input_vals.append(float(llm.get("input_tokens", 0)))
                    output_vals.append(float(llm.get("output_tokens", 0)))

                n = len(stats)
                avg_time = sum(time_vals) / n
                avg_in = sum(input_vals) / n
                avg_out = sum(output_vals) / n
                metric_cells.extend(
                    [
                        f"{avg_time:.2f}",
                        str(int(round(avg_in))),
                        str(int(round(avg_out))),
                    ]
                )

            out.append(
                f"| {task_label} | "
                + " | ".join(metric_cells)
                + " |"
            )
        out.append("")

    return "\n".join(out) + "\n"


def build_tables_latex(data, all_tasks):
    lines = []
    lines.append("% Auto-generated by scripts/generate_multilingual_icml_draft.py")
    lines.append("% Required packages in preamble:")
    lines.append("% \\usepackage{longtable}")
    lines.append("% \\usepackage{booktabs}")
    lines.append("% \\usepackage{array}")
    lines.append("")
    lines.append(r"\section{Comprehensive Multilingual Experiments Tables}")
    lines.append(r"\noindent We report all implemented languages with complete runs.")
    lines.append(r"\noindent Satisfaction tables report per-requirement \texttt{SATISFIED}/\texttt{UNSATISFIED}.")
    lines.append(r"\noindent Metrics tables report task-level means over requirements using \texttt{total\_time}, \texttt{input\_tokens}, and \texttt{output\_tokens}.")
    lines.append("")

    implemented_languages = [
        lang for lang in LANGUAGES if len(all_tasks.get(lang, [])) == 55
    ]

    for lang in implemented_languages:
        tasks = all_tasks.get(lang, [])
        lines.append(rf"\subsection{{{latex_escape(lang)}}}")
        lines.append("")

        # Table A: Satisfaction-only table with task/requirement rows (all 55 tasks in one table).
        lines.append(r"{\scriptsize")
        lines.append(
            r"\begin{longtable}{c|cccc}"
        )
        lines.append(
            rf"\caption{{{latex_escape(lang)}: Requirement-level satisfaction across all 55 tasks.}}\\"
        )
        lines.append(r"\toprule")
        lines.append(r"Task & Req & MetaGPT & GPT-Pilot & OpenHands \\")
        lines.append(r"\midrule")
        lines.append(r"\endfirsthead")
        lines.append(r"\toprule")
        lines.append(r"Task & Req & MetaGPT & GPT-Pilot & OpenHands \\")
        lines.append(r"\midrule")
        lines.append(r"\endhead")
        lines.append(r"\midrule")
        lines.append(r"\multicolumn{5}{r}{\footnotesize Continued on next page} \\")
        lines.append(r"\midrule")
        lines.append(r"\endfoot")
        lines.append(r"\bottomrule")
        lines.append(r"\endlastfoot")

        for task in tasks:
            fw_stats = {}
            req_set = set()
            for fw in FRAMEWORKS:
                obj = data.get(lang, {}).get(fw, {}).get(task)
                stats = {}
                if obj:
                    for stat in obj.get("judge_stats", []) or []:
                        req_idx = stat.get("requirement_index")
                        if isinstance(req_idx, int):
                            stats[req_idx] = stat
                            req_set.add(req_idx)
                fw_stats[fw] = stats

            req_indices = sorted(req_set)
            if not req_indices:
                lines.append(
                    rf"\texttt{{{latex_escape(task)}}} & - & \textit{{N/A}} & \textit{{N/A}} & \textit{{N/A}} \\"
                )
                continue

            task_label = task.split("_", 1)[0]
            middle_idx = len(req_indices) // 2
            for idx, req_idx in enumerate(req_indices):
                task_cell = task_label if idx == middle_idx else ""
                row_cells = []
                for fw in FRAMEWORKS:
                    stat = fw_stats[fw].get(req_idx)
                    if not stat:
                        row_cells.append(r"\textit{N/A}")
                    else:
                        row_cells.append(
                            "SATISFIED"
                            if bool(stat.get("satisfied", False))
                            else "UNSATISFIED"
                        )
                lines.append(
                    f"{latex_escape(task_cell)} & R{req_idx} & {row_cells[0]} & {row_cells[1]} & {row_cells[2]} \\\\"
                )
            # Add a separator between tasks for readability.
            lines.append(r"\midrule")

        lines.append(r"\end{longtable}")
        lines.append("}")
        lines.append("")

        # Table B: Task-level average metrics (all 55 tasks in one table).
        lines.append(r"{\scriptsize")
        lines.append(
            r"\begin{longtable}{c|rrr|rrr|rrr}"
        )
        lines.append(
            rf"\caption{{{latex_escape(lang)}: Task-level average judge metrics across requirements.}}\\"
        )
        lines.append(r"\hline")
        lines.append(
            r"& \multicolumn{3}{c|}{MetaGPT} & \multicolumn{3}{c|}{GPT-Pilot} & \multicolumn{3}{c|}{OpenHands} \\"
        )
        lines.append(r"\cline{2-4}\cline{5-7}\cline{8-10}")
        lines.append(
            r"Task & Time & Input Tokens & Output Tokens & Time & Input Tokens & Output Tokens & Time & Input Tokens & Output Tokens \\"
        )
        lines.append(r"\hline")
        lines.append(r"\endfirsthead")
        lines.append(r"\hline")
        lines.append(
            r"& \multicolumn{3}{c|}{MetaGPT} & \multicolumn{3}{c|}{GPT-Pilot} & \multicolumn{3}{c|}{OpenHands} \\"
        )
        lines.append(r"\cline{2-4}\cline{5-7}\cline{8-10}")
        lines.append(
            r"Task & Time & Input Tokens & Output Tokens & Time & Input Tokens & Output Tokens & Time & Input Tokens & Output Tokens \\"
        )
        lines.append(r"\hline")
        lines.append(r"\endhead")
        lines.append(r"\hline")
        lines.append(r"\multicolumn{10}{r|}{Continued on next page} \\")
        lines.append(r"\hline")
        lines.append(r"\endfoot")
        lines.append(r"\hline")
        lines.append(r"\endlastfoot")

        for task in tasks:
            metric_cells = []
            task_label = task.split("_", 1)[0]
            for fw in FRAMEWORKS:
                obj = data.get(lang, {}).get(fw, {}).get(task)
                if not obj:
                    metric_cells.extend([r"\textit{--}"] * 3)
                    continue

                stats = obj.get("judge_stats", []) or []
                if not stats:
                    metric_cells.extend([r"\textit{--}"] * 3)
                    continue

                time_vals = []
                input_vals = []
                output_vals = []
                for stat in stats:
                    llm = stat.get("llm_stats", {}) or {}
                    time_vals.append(float(stat.get("total_time", 0.0)))
                    input_vals.append(float(llm.get("input_tokens", 0)))
                    output_vals.append(float(llm.get("output_tokens", 0)))

                n = len(stats)
                avg_time = sum(time_vals) / n
                avg_in = sum(input_vals) / n
                avg_out = sum(output_vals) / n
                metric_cells.extend(
                    [
                        f"{avg_time:.2f}",
                        str(int(round(avg_in))),
                        str(int(round(avg_out))),
                    ]
                )

            lines.append(
                rf"{latex_escape(task_label)} & "
                + " & ".join(metric_cells)
                + r" \\"
            )

        lines.append(r"\end{longtable}")
        lines.append("}")
        lines.append("")

    return "\n".join(lines) + "\n"


def main():
    data, all_tasks = load_data()
    paper_md = build_paper_markdown(all_tasks)
    tables_md = build_tables_markdown(data, all_tasks)
    tables_tex = build_tables_latex(data, all_tasks)

    paper_path = ROOT / "ICML_multilingual_prompt_extension.md"
    tables_path = ROOT / "ICML_multilingual_experiments_tables.md"
    tables_tex_path = ROOT / "ICML_multilingual_experiments_tables.tex"
    paper_path.write_text(paper_md, encoding="utf-8")
    tables_path.write_text(tables_md, encoding="utf-8")
    tables_tex_path.write_text(tables_tex, encoding="utf-8")

    print(f"Wrote {paper_path}")
    print(f"Wrote {tables_path}")
    print(f"Wrote {tables_tex_path}")


if __name__ == "__main__":
    main()
