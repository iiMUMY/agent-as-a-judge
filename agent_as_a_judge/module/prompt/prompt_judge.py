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

    if language == "Turkish":
        return f"""
Projeye ilişkin bilgiler:
{evidence}

Lütfen şu ölçütü değerlendir:
{criteria}

Yalnızca <SATISFIED> veya <UNSATISFIED> etiketi ve kısa gerekçe döndür.
    """

    if language == "Chinese":
        return f"""
以下是与项目相关的信息：
{evidence}

请评估以下标准：
{criteria}

请使用 <SATISFIED> 或 <UNSATISFIED>，并给出简要依据。
    """

    if language == "Hindi":
        return f"""
प्रोजेक्ट से संबंधित जानकारी:
{evidence}

कृपया निम्न मानदंड का मूल्यांकन करें:
{criteria}

केवल <SATISFIED> या <UNSATISFIED> टैग और संक्षिप्त कारण दें।
    """

    return f"""
Provided below is relevant information about the project:
{evidence}

Kindly perform an evaluation of the following criteria:
{criteria}

As per the guidelines, respond with either <SATISFIED> or <UNSATISFIED>, followed by a concise justification that references specific elements from the project information, such as code snippets, data samples, or output results.
    """
