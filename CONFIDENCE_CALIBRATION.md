# Confidence Calibration Feature

## Overview

The confidence calibration feature enhances the Agent-as-a-Judge evaluation system by adding **confidence scores** to each requirement judgment. This quantifies how certain the LLM judge is about its evaluation decisions, providing valuable insight into the reliability of each judgment.

## What is Confidence Calibration?

Confidence calibration assigns a numerical score (0.0 to 1.0) to each judgment that represents the judge's **certainty** in the evaluation, independent of whether the requirement is satisfied or unsatisfied.

- **High confidence (0.7-1.0)**: Strong evidence supports the judgment
- **Moderate confidence (0.4-0.6)**: Some evidence but with ambiguity
- **Low confidence (0.1-0.3)**: Weak or contradictory evidence
- **No confidence (0.0)**: Insufficient information to make a reliable judgment

## Key Distinction

**Confidence measures certainty, not outcome:**
- **1.0 confidence + UNSATISFIED** = "I'm certain this requirement is NOT met"
- **1.0 confidence + SATISFIED** = "I'm certain this requirement IS met"
- **0.0 confidence + UNSATISFIED** = "I don't have enough information to evaluate this"

## Implementation Details

### Modified Components

1. **Prompt Changes** (`module/prompt/prompt_judge.py`):
   - Requests confidence score alongside judgment
   - Specifies format: judgment followed by confidence (0.0-1.0)

2. **System Prompt Changes** (`module/prompt/system_prompt_judge.py`):
   - Provides confidence scale guidelines:
     - **1.0**: Certain (definitive evidence)
     - **0.7-0.9**: High confidence (strong evidence)
     - **0.4-0.6**: Moderate confidence (partial/ambiguous evidence)
     - **0.1-0.3**: Low confidence (weak indicators)
     - **0.0**: No confidence (insufficient information)

3. **Parsing Logic** (`module/ask.py`):
   - `_parse_confidence()`: Extracts confidence from LLM response
   - `_collect_judgments()`: Returns confidence scores alongside judgments
   - `check()`: Calculates average confidence and stores individual scores

### Output Format

Each requirement judgment now includes:

```json
{
  "requirement_index": 0,
  "criteria": "The dataset is loaded in src/data_loader.py",
  "satisfied": false,
  "llm_stats": {
    "cost": 0.0027,
    "inference_time": 4.08,
    "input_tokens": 697,
    "output_tokens": 93,
    "satisfied": false,
    "reason": ["<UNSATISFIED>\nConfidence: 1.0\nJustification: ..."],
    "confidence": 1.0,
    "confidence_scores": [1.0]
  }
}
```

**New fields:**
- `confidence`: Average confidence across all majority votes (0.0-1.0)
- `confidence_scores`: Individual confidence scores from each vote

## Usage Examples

### Example 1: High Confidence - File Definitely Missing

```json
{
  "criteria": "The SVM regressor is implemented in src/model.py",
  "satisfied": false,
  "confidence": 1.0,
  "confidence_scores": [1.0],
  "reason": ["The file src/model.py does not exist. Without this file, 
             it is impossible for the SVM regressor to be implemented."]
}
```

**Interpretation**: The judge is **certain** (1.0) the requirement is unsatisfied because there's definitive negative evidence (file doesn't exist).

### Example 2: No Confidence - Insufficient Information

```json
{
  "criteria": "Feature selection is performed in src/data_loader.py",
  "satisfied": false,
  "confidence": 0.0,
  "confidence_scores": [0.0],
  "reason": ["No details about src/data_loader.py are provided. 
             Without access to the code, it is impossible to determine 
             if feature selection is implemented."]
}
```

**Interpretation**: The judge has **no confidence** (0.0) in this judgment because there's no code to evaluate. The "unsatisfied" verdict is a default guess, not a reliable conclusion.

### Example 3: Mixed Confidence with Majority Voting

With `majority_vote=3`:

```json
{
  "confidence": 0.833,
  "confidence_scores": [1.0, 0.8, 0.7]
}
```

**Interpretation**: Three independent judgments were made with varying confidence levels, averaging to high confidence (0.833).

## Interpreting Confidence Scores

### High Confidence (0.7-1.0)
- **When satisfied**: Clear evidence of correct implementation
- **When unsatisfied**: Definitive proof of missing/incorrect implementation
- **Action**: Trust this judgment

### Moderate Confidence (0.4-0.6)
- **Scenario**: Partial implementation, ambiguous code, or edge cases
- **Action**: May require manual review for critical requirements

### Low/No Confidence (0.0-0.3)
- **Scenario**: Empty workspace, missing files, or insufficient code context
- **Action**: Judgment unreliable; human review strongly recommended

## Use Cases

### 1. Prioritizing Manual Review
Focus human effort on low-confidence judgments:
```python
low_confidence = [j for j in judgments if j['confidence'] < 0.5]
```

### 2. Quality Metrics
Calculate overall evaluation reliability:
```python
avg_confidence = sum(j['confidence'] for j in judgments) / len(judgments)
```

### 3. Filtering Reliable Results
Only consider high-confidence judgments for automated decisions:
```python
reliable = [j for j in judgments if j['confidence'] >= 0.7]
```

### 4. Identifying Problematic Requirements
Low confidence may indicate:
- Poor requirement specification
- Missing documentation
- Incomplete implementation

## Limitations

### Empty Workspaces
With no code to evaluate, only extreme scores appear:
- **1.0**: File definitively doesn't exist (certain negative)
- **0.0**: No information available (completely uncertain)

**No intermediate scores** (0.3-0.9) occur because there's no ambiguous evidence.

### Workspace with Actual Code
To see the full confidence range, evaluate workspaces with:
- Partial implementations
- Ambiguous code structure
- Mixed evidence (some requirements met, others not)

### Calibration Accuracy
Confidence reflects the LLM's self-assessment, which may not always align with ground truth. Consider:
- LLMs can be overconfident or underconfident
- Confidence is based on visible evidence, not hidden implementation details
- Use as a heuristic, not absolute certainty

## Running Evaluations with Confidence

```bash
# Standard evaluation (confidence automatically included)
poetry run python scripts/run_aaaj.py \
  --developer_agent "MetaGPT" \
  --setting "black_box" \
  --planning "efficient (no planning)" \
  --task_number 39
```

The output JSON will automatically include confidence scores in the `llm_stats` for each requirement.

## Technical Notes

### Regex Pattern
Confidence extraction uses: `[Cc]onfidence[:\s]+([0-9]*\.?[0-9]+)`

Matches formats like:
- `Confidence: 0.8`
- `confidence: 1.0`
- `Confidence 0.5`

### Default Behavior
If confidence is not found in response: defaults to **0.5** (moderate uncertainty).

### Validation
Extracted values are clamped to [0.0, 1.0] range:
```python
confidence = max(0.0, min(1.0, extracted_value))
```

## Future Enhancements

Potential improvements:
1. **Calibration metrics**: Compare confidence scores against ground truth to assess calibration accuracy
2. **Confidence-weighted scoring**: Weight judgments by confidence in aggregate metrics
3. **Adaptive thresholds**: Adjust confidence interpretation based on evaluation context
4. **Explanation quality**: Correlation between confidence and explanation detail

## References

- Modified files: `module/ask.py`, `module/prompt/prompt_judge.py`, `module/prompt/system_prompt_judge.py`
- Related concept: Uncertainty quantification in machine learning
- Inspired by: Human confidence calibration in decision-making research
