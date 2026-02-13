# Agent-as-a-Judge Framework — Comprehensive Technical Report

This document provides a detailed explanation of the Agent-as-a-Judge framework, its architecture, the repository structure, and identified limitations and gaps. It is intended to support understanding the system for future extensions and improvements.

---

## Part 1: Paper Overview & Methodology

### 1.1 Core Idea

**Agent-as-a-Judge** (Zhuge et al., 2024) extends the **LLM-as-a-Judge** paradigm by using an **agentic system** to evaluate agentic systems. Instead of a single LLM call that compares outputs, the Judge is an agent that can:

- **Search** the workspace
- **Read** files (code, PDFs, images, etc.)
- **Locate** relevant files from criteria
- **Retrieve** and summarize trajectory logs
- **Ask** for clarification (in “Ask Anything” mode)
- **Reason** over evidence to produce pass/fail judgments

### 1.2 Motivation

- **Traditional evaluation** (e.g., SWE-Bench): Binary pass/fail on final outcome; no feedback on intermediate steps.
- **Human evaluation**: Expensive (58+ hours for initial round, 28.5 hours for consensus), high variance (10–30% disagreement between evaluators).
- **LLM-as-a-Judge**: Cheaper but limited (~70% agreement with human consensus) because it only sees final outputs, not the full trajectory.

Agent-as-a-Judge achieves **~90% agreement** with human consensus while saving **97.72% time** and **97.64% cost** compared to three human experts.

### 1.3 DevAI Benchmark

- **55 tasks** with **365 hierarchical requirements** organized as a DAG.
- **125 preferences** (softer criteria).
- Each task has: `query`, `requirements[]` (with `prerequisites`), `preferences[]`.
- Requirements are evaluated as **pass/fail** with evidence.

### 1.4 Evaluation Settings

- **Gray-box**: Judge has access to workspace + trajectory logs.
- **Black-box**: Judge only has access to workspace (no trajectory).

---

## Part 2: Repository Structure — Complete File-by-File Reference

```
agent-as-a-judge/
├── agent_as_a_judge/           # Core framework package
│   ├── __init__.py
│   ├── agent.py                # JudgeAgent orchestration
│   ├── config.py               # AgentConfig dataclass
│   ├── llm/                    # LLM provider & cost tracking
│   │   ├── __init__.py
│   │   ├── provider.py         # LiteLLM wrapper (OpenAI, Anthropic, etc.)
│   │   └── cost.py             # Accumulated cost tracking
│   ├── module/                 # Eight modular components
│   │   ├── __init__.py
│   │   ├── ask.py              # DevAsk: check requirements, ask questions
│   │   ├── code_search.py      # DevCodeSearch: semantic/fuzzy/BM25 search over code
│   │   ├── graph.py            # DevGraph: code graph construction (AST, tree-sitter)
│   │   ├── locate.py           # DevLocate: LLM-based file location from criteria
│   │   ├── memory.py           # Memory: historical judgments
│   │   ├── planning.py         # Planning: LLM-based evidence-gathering plan
│   │   ├── read.py             # DevRead: multimodal file reader (33+ formats)
│   │   ├── text_retrieve.py    # DevTextRetrieve: trajectory search & LLM summary
│   │   ├── statistics.py       # (if present) statistics utilities
│   │   └── prompt/             # All prompt templates
│   │       ├── prompt_ask.py, prompt_judge.py, prompt_locate.py,
│   │       ├── prompt_planning.py, prompt_retrieve.py
│   │       ├── system_prompt_ask.py, system_prompt_judge.py,
│   │       ├── system_prompt_locate.py, system_prompt_planning.py,
│   │       └── system_prompt_retrieve.py
│   └── utils/
│       ├── __init__.py
│       ├── truncate.py         # Token-aware truncation (head/middle/tail)
│       └── count_lines.py      # (if present) LOC utilities
├── benchmark/                  # DevAI benchmark data
│   ├── devai/                  # Instance definitions, schema, constraints
│   │   ├── instances/         # 55 task JSON files (query, requirements, preferences)
│   │   ├── trajectory-schema.json
│   │   ├── constraints.json
│   │   ├── validate_trajectory.py
│   │   └── README.md
│   ├── workspaces/            # Output from developer agents
│   │   └── {agent_name}/{task_name}/  # Files produced by the agent
│   ├── trajectories/          # Step-by-step logs (gray-box only)
│   │   └── {agent_name}/{task_name}.json
│   └── judgment/              # Judge outputs
│       └── {agent_name}/agent_as_a_judge/{setting}/*.json
├── scripts/
│   ├── run_aaaj.py            # Main: Agent-as-a-Judge batch evaluation
│   ├── run_ask.py             # Ask Anything: interactive Q&A over workspace
│   ├── run_statistics.py      # Statistics over judgment results
│   ├── run_wiki.py            # OpenWiki: generate docs from repo
│   └── templates/             # HTML templates for run_wiki
├── assets/                    # Images, logos, sample outputs
├── .env.sample                 # Env template (DEFAULT_LLM, OPENAI_API_KEY, PROJECT_DIR)
├── pyproject.toml             # Poetry dependencies
└── README.md
```

---

## Part 3: Core Components — Detailed Explanation

### 3.1 JudgeAgent (`agent_as_a_judge/agent.py`)

**Role**: Orchestrates the evaluation pipeline for a single task instance.

**Inputs**:
- `workspace`: Path to the developer agent’s output folder
- `instance`: Path to the DevAI instance JSON (query, requirements, preferences)
- `judge_dir`: Where to save judgments and cached graph/tags
- `config`: `AgentConfig` (setting, planning, include/exclude dirs)
- `trajectory_file`: Optional path to trajectory JSON (gray-box)

**Execution flow**:
1. **Graph construction** (if not cached): `construct_graph()` → `DevGraph.build()` → saves `graph.pkl`, `tags.json`, `tree_structure.json` in `judge_dir`.
2. **Per requirement**: `check_requirement(criteria, workflow, user_query)`:
   - `workflow` is fixed or from `Planning.generate_plan()`: `["workspace", "locate", "read", "trajectory"]` etc.
   - For each step: gather evidence (workspace tree, located files, file contents, search results, trajectory summary).
   - `DevAsk.check(criteria, combined_evidence)` → binary pass/fail + reason.
3. **Output**: Appends to `judge_stats`, saves to `judge_dir/{instance_name}.json`.

**Key methods**:
- `judge_anything()`: Batch evaluate all requirements for the instance.
- `ask_anything(question)`: Interactive Q&A over the workspace (no instance).
- `display_tree()`, `display_judgment()`: Rich console output.

### 3.2 LLM Provider (`agent_as_a_judge/llm/provider.py`)

**Role**: Wraps LiteLLM for completion, cost tracking, retries.

**Behavior**:
- Uses `DEFAULT_LLM` and `OPENAI_API_KEY` from env.
- Supports any LiteLLM-compatible model (OpenAI, Anthropic, etc.).
- Retries on `RateLimitError`, `APIConnectionError`, `ServiceUnavailableError`.
- Aggregates cost via `Cost` class.
- `_llm_inference(messages)` returns `{llm_response, input_tokens, output_tokens, cost, inference_time}`.

**Note**: The Judge and all modules (Ask, Locate, Retrieve, Planning) use this same LLM instance.

### 3.3 Eight Modules — One-by-One

| Module | File | Purpose |
|--------|------|---------|
| **Graph** | `graph.py` | Builds a code graph from `.py` files: parses AST, tree-sitter captures for classes/functions, creates `tags` (name, line, category, details) and `networkx` graph. Cached as `graph.pkl`, `tags.json`. |
| **Code Search** | `code_search.py` | Loads graph/tags from `judge_dir`. Supports `accurate`, `fuzzy`, `bm25`, `embedding` search over code tags. Returns relevant snippets for display. |
| **Locate** | `locate.py` | LLM-based: given `criteria` + `workspace_info` (tree), returns list of file paths (up to 5) that are relevant to the requirement. |
| **Read** | `read.py` | Reads 33+ file types: `.txt`, `.pdf`, `.docx`, `.json`, `.yaml`, `.md`, `.py`, `.png`, `.mp4`, etc. Returns string content; some use LLM for extraction (e.g., images). |
| **Text Retrieve** | `text_retrieve.py` | Loads trajectory JSON. Supports `accurate`, `fuzzy`, `bm25`, `embedding` search, and `llm_summary`: LLM summarizes trajectory w.r.t. criteria. Used for gray-box evidence. |
| **Ask** | `ask.py` | **Check**: Given criteria + evidence, runs LLM judge (default 1 vote) and parses `<SATISFIED>` / `<UNSATISFIED>`. **Ask**: Given question + evidence, returns LLM answer (for interactive Q&A). |
| **Memory** | `memory.py` | Stores/retrieves historical judgments from a JSON file. Used in `history` workflow step to provide context from prior requirements. |
| **Planning** | `planning.py` | LLM-based: given criteria, generates a plan as a list of actions (`[User Query]`, `[Workspace]`, `[Locate]`, etc.). Parsed via regex. |

### 3.4 Workflows

**Efficient (no planning)**:
```
["workspace", "locate", "read", "trajectory"]
```
- Always gathers: tree, located files, file contents, trajectory summary.
- `trajectory` omitted in black-box.

**Comprehensive (no planning)**:
```
["user_query", "workspace", "locate", "read", "search", "history", "trajectory"]
```
- Adds user query, code search, and historical judgments.

**Planning**:
- LLM generates the workflow per requirement.

### 3.5 Prompts

All prompts live in `agent_as_a_judge/module/prompt/`:

- **Judge**: System prompt defines judge role; user prompt provides evidence + criteria. Output must contain `<SATISFIED>` or `<UNSATISFIED>`.
- **Locate**: Asks LLM to pick file paths from workspace tree given criteria.
- **Retrieve**: Asks LLM to summarize trajectory given criteria.
- **Planning**: Asks LLM to output a sequence of `[Action]` steps.
- **Ask**: General Q&A over workspace evidence.

### 3.6 Utils

- **truncate.py**: `truncate_string(text, model, max_tokens, drop_mode)` — token-aware truncation (head/middle/tail) to fit context window.

---

## Part 4: Scripts — Entry Points

### 4.1 `run_aaaj.py` — Batch Agent-as-a-Judge

**Usage**:
```bash
PYTHONPATH=. python scripts/run_aaaj.py \
  --developer_agent "OpenHands" \
  --setting "black_box" | "gray_box" \
  --planning "efficient (no planning)" | "comprehensive (no planning)" | "planning" \
  --benchmark_dir $(pwd)/benchmark
```

**Logic**:
- Resolves paths: `instance_dir`, `workspace_dir`, `judge_dir`, `trajectory_file`.
- Iterates over `instance_dir/*.json` (sorted by task number).
- Skips if `judge_dir/{instance}.json` already exists.
- For each instance: instantiates `JudgeAgent`, calls `judge_anything()`.

### 4.2 `run_ask.py` — Ask Anything

**Usage**:
```bash
PYTHONPATH=. python scripts/run_ask.py \
  --workspace <path_to_workspace> \
  --question "What does this workspace contain?"
```

**Logic**:
- Uses `JudgeAgent` with `instance=None`, `trajectory_file=None`.
- `ask_anything(question)` → gathers evidence → `DevAsk.ask()`.
- Interactive loop for follow-up questions.

### 4.3 `run_statistics.py`

Generates aggregate statistics over judgment results (e.g., pass rates per agent).

### 4.4 `run_wiki.py`

Generates OpenWiki documentation for a given repository (separate from evaluation).

---

## Part 5: Benchmark Data Layout

### 5.1 `benchmark/devai/instances/*.json`

Each file defines one task:
- `name`: Task identifier
- `query`: User request
- `requirements`: List of `{requirement_id, prerequisites, criteria, category, satisfied}`
- `preferences`: Soft criteria
- `is_kaggle_api_needed`, `is_training_needed`, etc.

### 5.2 `benchmark/workspaces/{agent}/{task_name}/`

Directory produced by the developer agent (e.g., `src/`, `results/`, `models/`).

### 5.3 `benchmark/trajectories/{agent}/{task_name}.json`

JSON array of steps: `step`, `user_message`, `agent` (action, thought), `environment`, etc. Used only in gray-box.

### 5.4 `benchmark/judgment/{agent}/agent_as_a_judge/{setting}/*.json`

Output: Same structure as instance, with `judge_stats` added (per-requirement `satisfied`, `reason`, `llm_stats`).

---

## Part 6: Data Flow — End-to-End

```
Instance JSON (query, requirements)
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│  JudgeAgent.check_requirement(criteria, workflow)            │
│                                                              │
│  1. Workspace: display_tree() → truncated tree               │
│  2. Locate:   DevLocate.locate_file(criteria, tree) → paths  │
│  3. Read:     DevRead.read(path) for each path               │
│  4. Search:   DevCodeSearch.search(criteria) → code snippets │
│  5. History:  Memory.get_historical_evidence()               │
│  6. Trajectory: DevTextRetrieve.llm_summary(criteria)        │
│                                                              │
│  combined_evidence = concat all (truncated)                  │
│  7. Ask: DevAsk.check(criteria, combined_evidence)           │
│         → satisfied (bool), reason (str)                     │
└──────────────────────────────────────────────────────────────┘
         │
         ▼
  Judgment saved to judge_dir/{instance}.json
```

---

## Part 7: Limitations & Gaps

### 7.1 Judge Hallucinations

- The Judge can claim a requirement is satisfied when it is not (or vice versa).
- No verification layer (e.g., code execution, unit tests) to ground judgments.
- **Gap**: Add executable checks or external validators for code-related requirements.

### 7.2 No Social/Ethical Safety

- Evaluation is purely **functional** (code correctness, outputs).
- No checks for: harmful code, privacy violations, bias, security issues.
- **Gap**: Integrate safety/ethics evaluators (e.g., AgentHarm, ASB) as additional dimensions.

### 7.3 Stability / Reproducibility

- LLM sampling (temperature > 0) causes variance across runs.
  - Temperature > 0 in LLM sampling is a hyperparameter that controls the randomness, creativity, and diversity of generated text by modifying token probability distributions. It acts as a scaling factor on the logits before the softmax function, where higher values (> 1.0) increase variability by making lower-probability tokens more likely, while values below 1.0 produce more focused, conservative, and consistent output. 
- Paper notes "stability across reruns" as a gap.
- **Gap**: Use temperature=0 for judgments, and/or majority voting over multiple runs; report variance metrics.

### 7.4 Cost & Latency

- Agent-as-a-Judge is cheaper than humans but more expensive than a single LLM-as-a-Judge call.
- Many LLM calls per requirement (locate, read, retrieve, check, optionally planning).
- **Gap**: Caching, batching, or lighter workflows for low-resource settings.

### 7.5 Trajectory Format Coupling

- `DevTextRetrieve` expects a specific trajectory schema (`step`, `user_message`, `agent`, `environment`).
- Other agents may use different formats.
- **Gap**: Adapters or configurable schema for different trajectory formats.

### 7.6 Single-Language Focus (Programming)

- `DevGraph` and code search are optimized for **Python** (AST, tree-sitter).
- Limited support for other languages.
- **Gap**: Multi-language parsers or language-agnostic search strategies.

### 7.7 English-Only Prompts (Natural Language)

- All system prompts (`system_prompt_judge.py`, `system_prompt_ask.py`, `system_prompt_locate.py`, `system_prompt_planning.py`, `system_prompt_retrieve.py`) accept `language="English"` and raise `NotImplementedError` for any other value (e.g., `"Arabic"`).
- The Judge’s instructions, reasoning, and justifications are thus English-only. Users whose task queries, requirements, or preferred evaluation language are in Arabic or other languages cannot use localized prompts.
- **Gap**: Add multi-lingual prompt support (e.g., Arabic, French) so the Judge can operate in the user’s language for requirements, criteria, and justifications.

### 7.8 No Partial Credit

- Requirements are binary (satisfied/unsatisfied).
- No granular scoring (e.g., 0–1) for partial completion.
- **Gap**: Introduce scalar scores or partial credit for richer reward signals.

### 7.9 Ask Module Underused in Batch

- **DevAsk** exposes two capabilities: (1) `check(criteria, evidence)` → binary SATISFIED/UNSATISFIED; (2) `ask(question, evidence)` → free-form answer to a user question (clarification, explanation).
- **Batch workflow** (`run_aaaj.py` → `judge_anything()` → `check_requirement()`): The Judge gathers evidence (workspace, locate, read, search, history, trajectory) and then invokes **only** `DevAsk.check()` to produce a pass/fail. The `ask()` method is **never** called in this flow.
- **Interactive mode** (`run_ask.py`): Users can ask questions via `ask_anything()` → `DevAsk.ask()`. This is the **only** place where `ask()` is used.
- **Gap**: The paper envisions the Judge "asking" for clarification when evidence is insufficient or ambiguous (e.g., contradictory signals, missing context). Currently, the Judge always proceeds to `check()` without seeking clarification, even when uncertain. Integrating Ask into the batch workflow—e.g., a decision step: "if evidence ambiguous → ask for clarification → then decide"—would align the implementation with the paper's vision.

### 7.10 Memory / History Scope

- `Memory` stores judgments for the **current instance** only.
- No cross-instance or cross-task memory.
- **Gap**: Persistent memory for calibration or transfer across tasks.

### 7.11 No Confidence Calibration

- Judge outputs pass/fail but no confidence score.
- Cannot prioritize human review for low-confidence cases.
- **Gap**: Add confidence output (e.g., from logprobs or self-consistency) and flag uncertain cases.

---

## Part 8: Summary Table

| Component | Location | Key Dependencies |
|-----------|----------|------------------|
| JudgeAgent | `agent.py` | All modules, LLM, config |
| LLM | `llm/provider.py` | litellm, tenacity |
| Graph | `module/graph.py` | tree-sitter, grep_ast, networkx |
| Code Search | `module/code_search.py` | sentence-transformers, BM25, spacy |
| Locate | `module/locate.py` | LLM |
| Read | `module/read.py` | PyPDF2, docx, openpyxl, cv2, etc. |
| Text Retrieve | `module/text_retrieve.py` | sentence-transformers, rapidfuzz, BM25 |
| Ask | `module/ask.py` | LLM, prompts |
| Memory | `module/memory.py` | JSON file |
| Planning | `module/planning.py` | LLM |
| Truncate | `utils/truncate.py` | tiktoken |

---

## References

- Paper: [Agent-as-a-Judge: Evaluate Agents with Agents](https://arxiv.org/abs/2410.10934) (Zhuge et al., 2024)
- Dataset: [DevAI on Hugging Face](https://huggingface.co/DEVAI-benchmark)
- Repo: [metauto-ai/agent-as-a-judge](https://github.com/metauto-ai/agent-as-a-judge)
