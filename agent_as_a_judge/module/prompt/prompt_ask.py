def get_ask_prompt(question: str, evidence: str, language: str = "English") -> str:

    if language == "Arabic":
        return f"""
فيما يلي معلومات مرتبطة بالمشروع أو بالسياق:
{evidence}

يرجى الإجابة على سؤال المستخدم التالي:
{question}

قدّم إجابة واضحة وشاملة مع الإشارة إلى الأدلة ذات الصلة عند الحاجة.
    """

    if language == "Turkish":
        return f"""
Proje/senaryo ile ilgili bilgiler:
{evidence}

Kullanıcı sorusu:
{question}

Gerekli yerlerde kanıta referans vererek net bir yanıt ver.
    """

    if language == "Chinese":
        return f"""
以下是项目或上下文信息：
{evidence}

用户问题：
{question}

请给出清晰完整的回答，并在适当处引用证据。
    """

    if language == "Hindi":
        return f"""
प्रोजेक्ट/संदर्भ की जानकारी:
{evidence}

उपयोगकर्ता प्रश्न:
{question}

जहाँ उचित हो, साक्ष्य का संदर्भ देते हुए स्पष्ट उत्तर दें।
    """

    return f"""
Provided below is relevant information about the project or context:
{evidence}

Kindly respond to the following user input:
{question}

As per the guidelines, provide a comprehensive answer referencing specific elements from the provided information where applicable.
    """
