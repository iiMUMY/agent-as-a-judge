import argparse
import os
from dotenv import load_dotenv

from agent_as_a_judge.llm.provider import LLM


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        required=True,
        help="Model name passed to LiteLLM (e.g., openrouter/openai/gpt-5.4).",
    )
    return parser.parse_args()


def main():
    load_dotenv()
    args = parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    if not api_key or not base_url:
        raise RuntimeError("OPENAI_API_KEY and OPENAI_BASE_URL must be set.")

    llm = LLM(model=args.model, api_key=api_key, base_url=base_url, llm_timeout=60)
    result = llm._llm_inference(
        [
            {"role": "system", "content": "You are a concise assistant."},
            {
                "role": "user",
                "content": "Reply with exactly: OPENROUTER_OK",
            },
        ]
    )
    print(f"model={args.model}")
    print(f"response={result['llm_response']}")
    print(f"tokens_in={result['input_tokens']} tokens_out={result['output_tokens']}")
    print(f"cost={result['cost']}")


if __name__ == "__main__":
    main()
