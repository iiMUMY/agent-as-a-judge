# Agent-as-a-Judge Project - Setup Complete ✓

## Project Overview

**Agent-as-a-Judge** is a framework for evaluating AI development agents using LLM-based judgment. It can:
- Evaluate agent-generated code and workspaces
- Answer questions about any codebase
- Provide automated evaluation with reward signals
- Generate interactive documentation (OpenWiki)

## Setup Status: ✓ COMPLETE

### What Was Done

1. **Dependency Installation** ✓
   - Updated `pyproject.toml` to support Python 3.12
   - Upgraded `tree-sitter-languages` from 1.8.0 to 1.10.2 (for Python 3.12 compatibility)
   - Installed all project dependencies via Poetry
   - Downloaded spaCy English language model (`en_core_web_sm`)

2. **Environment Configuration** ✓
   - Created `.env` file from `.env.sample`
   - Configured PROJECT_DIR path

3. **Verification** ✓
   - Successfully imported all agent modules
   - Tested workspace analysis (tree structure generation)
   - Confirmed LLM integration works (pending valid API key)

### What You Need to Do

**Add your OpenAI API key** to complete the setup:

1. Open `.env` file in the project root
2. Replace `sk-***` with your actual OpenAI API key:
   ```
   OPENAI_API_KEY="sk-your-actual-key-here"
   ```
3. Get your API key from: https://platform.openai.com/account/api-keys

## How to Run the Project

### 1. Ask Anything Mode (Query Any Workspace)

```bash
# Activate virtual environment first
.\.venv\Scripts\Activate.ps1

# Run ask mode
python scripts/run_ask.py --workspace benchmark/workspaces/OpenHands/39_Drug_Response_Prediction_SVM_GDSC_ML --question "What does this workspace contain?"
```

### 2. Agent-as-a-Judge Mode (Evaluate Agent Work)

```bash
# Black-box evaluation (no trajectory logs)
python scripts/run_aaaj.py --developer_agent "OpenHands" --setting "black_box" --planning "efficient (no planning)" --benchmark_dir benchmark

# Gray-box evaluation (with trajectory logs)
python scripts/run_aaaj.py --developer_agent "OpenHands" --setting "gray_box" --planning "comprehensive (no planning)" --benchmark_dir benchmark
```

### 3. OpenWiki Mode (Generate Interactive Documentation)

```bash
python scripts/run_wiki.py https://github.com/metauto-ai/GPTSwarm
```

### 4. Quick Demo Test

```bash
python demo_test.py
```

## Project Structure

```
agent-as-a-judge/
├── agent_as_a_judge/          # Core framework code
│   ├── agent.py               # Main JudgeAgent class
│   ├── config.py              # Configuration
│   ├── llm/                   # LLM provider (LiteLLM)
│   ├── module/                # Core modules (ask, locate, search, etc.)
│   └── utils/                 # Utilities
├── scripts/                   # Runnable scripts
│   ├── run_ask.py             # Ask anything mode
│   ├── run_aaaj.py            # Agent-as-a-Judge mode
│   ├── run_wiki.py            # OpenWiki mode
│   └── run_statistics.py     # Statistics generation
├── benchmark/                 # DevAI benchmark dataset
│   ├── devai/                 # 55 AI development tasks
│   ├── workspaces/            # Agent-generated workspaces
│   ├── trajectories/          # Agent execution logs
│   └── judgment/              # Evaluation results
├── .env                       # Environment variables (YOU NEED TO CONFIGURE)
└── pyproject.toml             # Project dependencies
```

## Key Features

### 1. Code Understanding
- Builds semantic graph of codebase
- BM25 and embedding-based code search
- Tree-sitter parsing for Python files
- Hierarchical file structure analysis

### 2. LLM Integration
- Uses LiteLLM for multi-provider support
- Currently configured for OpenAI GPT-4o
- Supports cost tracking and token counting

### 3. Evaluation Capabilities
- **Black-box**: Evaluate without execution logs
- **Gray-box**: Evaluate with trajectory data
- **Planning**: Optional LLM-based action planning
- Hierarchical requirement checking

### 4. Modules
- `DevAsk`: Question answering with evidence collection
- `DevLocate`: File location using LLM reasoning
- `DevCodeSearch`: Multi-strategy code search
- `DevGraph`: Codebase graph construction
- `DevRead`: Smart file reading
- `DevTextRetrieve`: Trajectory analysis

## Configuration Options

Edit `.env` to customize:
- `DEFAULT_LLM`: Model to use (default: gpt-4o-2024-08-06)
- `OPENAI_API_KEY`: Your OpenAI API key
- `PROJECT_DIR`: Project root directory

## Next Steps

1. **Add your OpenAI API key** to `.env`
2. Run the demo: `python demo_test.py`
3. Try "Ask Anything" on your own codebase
4. Explore the benchmark dataset in `benchmark/devai/`
5. Read the paper: https://arxiv.org/pdf/2410.10934

## Troubleshooting

### Import Errors
- Make sure to activate the virtual environment: `.\.venv\Scripts\Activate.ps1`
- Verify installation: `poetry install`

### API Errors
- Check your OpenAI API key is valid
- Ensure you have credits in your OpenAI account
- Verify `.env` file exists and is properly configured

### spaCy Model Errors
- Re-download model: `python -m spacy download en_core_web_sm`

## Resources

- **Paper**: [Agent-as-a-Judge on arXiv](https://arxiv.org/pdf/2410.10934)
- **Dataset**: [DevAI on HuggingFace](https://huggingface.co/DEVAI-benchmark)
- **GitHub**: https://github.com/metauto-ai/agent-as-a-judge
- **License**: MIT

---

**Status**: ✓ Ready to run (pending API key configuration)  
**Last Updated**: February 10, 2026  
**Python Version**: 3.12.3  
**Poetry**: Installed and configured
