def get_judge_prompt(criteria: str, evidence: str, language: str = "English") -> str:

    if language == "Arabic":
        return f"""
المعلومات التالية تتعلق بالمشروع:
{evidence}

يرجى تقييم المعيار التالي:
{criteria}

بحسب الإرشادات، استجب باستخدام <SATISFIED> أو <UNSATISFIED> ثم قدّم تبريرا مختصرا
يشير إلى أدلة محددة من المعلومات المتاحة.
    """

    return f"""
Provided below is relevant information about the project:
{evidence}

Kindly perform an evaluation of the following criteria:
{criteria}

As per the guidelines, respond with either <SATISFIED> or <UNSATISFIED>, followed by a concise justification that references specific elements from the project information, such as code snippets, data samples, or output results.
    """
