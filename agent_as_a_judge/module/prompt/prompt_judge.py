def get_judge_prompt(criteria: str, evidence: str) -> str:

    return f"""
Provided below is relevant information about the project:
{evidence}

Kindly perform an evaluation of the following criteria:
{criteria}

As per the guidelines, respond with either <SATISFIED> or <UNSATISFIED>, followed by a confidence score (0.0 to 1.0) indicating your certainty level, and a detailed justification.

CONFIDENCE DETERMINATION PROCESS:
1. Identify what evidence you have (file names, code snippets, output files, or absence thereof)
2. Assess evidence strength (explicit implementation > indirect indicators > absence of evidence)
3. Consider workspace completeness (full project vs empty workspace affects certainty)
4. Map to confidence range based on evidence type and strength
5. Explain your confidence level in the justification

Format your response as:
<SATISFIED> or <UNSATISFIED>
Confidence: <score between 0.0 and 1.0>
Justification: <First state what evidence you found/didn't find, then explain why this leads to your judgment, finally justify your confidence level based on evidence strength>
    """
