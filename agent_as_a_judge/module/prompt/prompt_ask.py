def get_ask_prompt(question: str, evidence: str, language: str = "English") -> str:

    if language == "Arabic":
        return f"""
فيما يلي معلومات مرتبطة بالمشروع أو بالسياق:
{evidence}

يرجى الإجابة على سؤال المستخدم التالي:
{question}

قدّم إجابة واضحة وشاملة مع الإشارة إلى الأدلة ذات الصلة عند الحاجة.
    """

    return f"""
Provided below is relevant information about the project or context:
{evidence}

Kindly respond to the following user input:
{question}

As per the guidelines, provide a comprehensive answer referencing specific elements from the provided information where applicable.
    """
