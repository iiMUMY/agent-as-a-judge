"""
DevAsk: A development tool for asking questions and checking requirements using LLM.
"""

import os
import logging
import warnings
from pathlib import Path
from dotenv import load_dotenv
from rich.logging import RichHandler
from agent_as_a_judge.llm.provider import LLM
from agent_as_a_judge.module.prompt.system_prompt_judge import get_judge_system_prompt
from agent_as_a_judge.module.prompt.prompt_judge import get_judge_prompt
from agent_as_a_judge.module.prompt.system_prompt_ask import get_ask_system_prompt
from agent_as_a_judge.module.prompt.prompt_ask import get_ask_prompt

warnings.simplefilter("ignore", category=FutureWarning)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[RichHandler()],
)


class DevAsk:
    def __init__(self, workspace: Path, judge_dir: Path):
        self.workspace = workspace
        self.judge_dir = judge_dir
        self.llm = self._initialize_llm()

    def _initialize_llm(self) -> LLM:
        try:
            model = os.getenv("DEFAULT_LLM")
            api_key = os.getenv("OPENAI_API_KEY")
            return LLM(model=model, api_key=api_key)
        except KeyError as e:
            logging.error(f"Missing environment variable: {e}")
            raise

    def check(
        self,
        criteria: str,
        evidence: str,
        majority_vote: int = 1,
        critical_threshold: float = 0.5,
    ) -> dict:
        total_llm_stats = self._initialize_llm_stats()
        responses, judges, confidences = self._collect_judgments(
            criteria, evidence, majority_vote, total_llm_stats
        )

        satisfied_count = judges.count("<SATISFIED>")
        total_judges = len(judges)
        majority_judge = (satisfied_count / total_judges) >= critical_threshold

        # Calculate average confidence
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5

        total_llm_stats.update({
            "satisfied": majority_judge,
            "reason": responses,
            "confidence": round(avg_confidence, 3),
            "confidence_scores": [round(c, 3) for c in confidences],
        })
        return total_llm_stats

    def _collect_judgments(
        self, criteria: str, evidence: str, majority_vote: int, llm_stats: dict
    ) -> tuple:
        system_prompt = get_judge_system_prompt(language="English")
        prompt = get_judge_prompt(criteria=criteria, evidence=evidence)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        responses = []
        judges = []
        confidences = []

        for _ in range(majority_vote):
            result = self.llm._llm_inference(messages)
            response_text = result["llm_response"].strip()
            responses.append(response_text)
            judges.append(self._parse_judge(response_text))
            confidences.append(self._parse_confidence(response_text))

            self._update_llm_stats(llm_stats, result)

        return responses, judges, confidences

    @staticmethod
    def _parse_judge(response: str) -> str:
        if "<SATISFIED>" in response:
            return "<SATISFIED>"
        return "<UNSATISFIED>"
    
    @staticmethod
    def _parse_confidence(response: str) -> float:
        """Extract confidence score from the response."""
        import re
        # Look for patterns like "Confidence: 0.8" or "confidence: 0.95" or "Confidence of 0.75"
        patterns = [
            r'[Cc]onfidence[:\s]+([0-9]*\.?[0-9]+)',
            r'[Cc]onfidence\s+of\s+([0-9]*\.?[0-9]+)',
            r'[Cc]ertainty[:\s]+([0-9]*\.?[0-9]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response)
            if match:
                try:
                    confidence = float(match.group(1))
                    # Ensure confidence is in valid range
                    return max(0.0, min(1.0, confidence))
                except ValueError:
                    continue
        
        # Default based on judgment type
        if "<SATISFIED>" in response:
            # If satisfied but no confidence given, assume moderate-high (likely found something)
            return 0.65
        else:
            # If unsatisfied but no confidence given, assume moderate (absence of evidence)
            return 0.55

    @staticmethod
    def _initialize_llm_stats() -> dict:
        return {
            "cost": 0.0,
            "inference_time": 0.0,
            "input_tokens": 0,
            "output_tokens": 0,
        }

    @staticmethod
    def _update_llm_stats(stats: dict, result: dict):
        stats["cost"] += result.get("cost", 0)
        stats["inference_time"] += result.get("inference_time", 0)
        stats["input_tokens"] += result.get("input_tokens", 0)
        stats["output_tokens"] += result.get("output_tokens", 0)

    def ask(self, question: str, evidence: str) -> str:
        if not evidence:
            raise ValueError("Evidence must be provided.")

        system_prompt = get_ask_system_prompt(language="English")
        prompt = get_ask_prompt(evidence=evidence, question=question)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        result = self.llm._llm_inference(messages)
        return result["llm_response"]


if __name__ == "__main__":
    load_dotenv()
    workspace_path = (
        Path(os.getenv("PROJECT_DIR"))
        / "benchmark/workspace/OpenHands/39_Drug_Response_Prediction_SVM_GDSC_ML"
    )
    judge_dir = (
        Path(os.getenv("PROJECT_DIR"))
        + "/benchmark/judgement/OpenHands/39_Drug_Response_Prediction_SVM_GDSC_ML"
    )
    judge_dir.mkdir(parents=True, exist_ok=True)
    dev_ask = DevAsk(workspace=workspace_path, judge_dir=judge_dir)

    while True:
        user_query = input("Ask your question: ")
        if user_query.lower() in ["exit", "quit"]:
            break
        try:
            response = dev_ask.ask(question="This is a test.", evidence=user_query)
            print(response)
        except Exception as e:
            logging.error(f"An error occurred: {e}")
