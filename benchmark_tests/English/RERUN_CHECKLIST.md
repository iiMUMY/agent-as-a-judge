# Full 55-Task Rerun Checklist (English)

## 1) Regenerate requirement spec and semantic workspaces

```powershell
$env:PYTHONIOENCODING='utf-8'
poetry run python scripts/build_requirement_spec.py --instances_dir "benchmark_tests/English/OpenHands/devai/instances" --output "benchmark_tests/English/requirement_spec.json"
poetry run python scripts/apply_minimal_semantic_impl.py --spec "benchmark_tests/English/requirement_spec.json" --workspace_root "benchmark_tests/English/OpenHands/workspaces/OpenHands"
```

## 2) Sync canonical workspaces to all frameworks

```powershell
Remove-Item -Recurse -Force "benchmark_tests/English/MetaGPT/workspaces/MetaGPT"
Remove-Item -Recurse -Force "benchmark_tests/English/GPT-Pilot/workspaces/GPT-Pilot"
New-Item -ItemType Directory -Force -Path "benchmark_tests/English/MetaGPT/workspaces/MetaGPT" | Out-Null
New-Item -ItemType Directory -Force -Path "benchmark_tests/English/GPT-Pilot/workspaces/GPT-Pilot" | Out-Null
Copy-Item -Recurse -Force "benchmark_tests/English/OpenHands/workspaces/OpenHands/*" "benchmark_tests/English/MetaGPT/workspaces/MetaGPT/"
Copy-Item -Recurse -Force "benchmark_tests/English/OpenHands/workspaces/OpenHands/*" "benchmark_tests/English/GPT-Pilot/workspaces/GPT-Pilot/"
```

## 3) Validate path/signature coverage before reruns

```powershell
poetry run python scripts/validate_semantic_coverage.py --spec "benchmark_tests/English/requirement_spec.json" --workspace_root "benchmark_tests/English/OpenHands/workspaces/OpenHands" --output "benchmark_tests/English/semantic_validation_openhands.json"
poetry run python scripts/validate_semantic_coverage.py --spec "benchmark_tests/English/requirement_spec.json" --workspace_root "benchmark_tests/English/MetaGPT/workspaces/MetaGPT" --output "benchmark_tests/English/semantic_validation_metagpt.json"
poetry run python scripts/validate_semantic_coverage.py --spec "benchmark_tests/English/requirement_spec.json" --workspace_root "benchmark_tests/English/GPT-Pilot/workspaces/GPT-Pilot" --output "benchmark_tests/English/semantic_validation_gptpilot.json"
```

## 4) Clear old judgments to avoid skip behavior

```powershell
Remove-Item -Recurse -Force "benchmark_tests/English/OpenHands/judgment"
Remove-Item -Recurse -Force "benchmark_tests/English/MetaGPT/judgment"
Remove-Item -Recurse -Force "benchmark_tests/English/GPT-Pilot/judgment"
```

## 5) Run full 55 tasks

### OpenHands

```powershell
$env:PYTHONPATH='.'
$env:PYTHONIOENCODING='utf-8'
poetry run python scripts/run_aaaj.py --developer_agent "OpenHands" --setting "gray_box" --planning "efficient (no planning)" --language "English" --benchmark_dir "benchmark_tests/English/OpenHands"
```

### MetaGPT

```powershell
$env:PYTHONPATH='.'
$env:PYTHONIOENCODING='utf-8'
poetry run python scripts/run_aaaj.py --developer_agent "MetaGPT" --setting "gray_box" --planning "efficient (no planning)" --language "English" --benchmark_dir "benchmark_tests/English/MetaGPT"
```

### GPT-Pilot

```powershell
$env:PYTHONPATH='.'
$env:PYTHONIOENCODING='utf-8'
poetry run python scripts/run_aaaj.py --developer_agent "GPT-Pilot" --setting "gray_box" --planning "efficient (no planning)" --language "English" --benchmark_dir "benchmark_tests/English/GPT-Pilot"
```

## 6) Optional spot comparison helper

```powershell
poetry run python scripts/compare_spot_results.py
```
