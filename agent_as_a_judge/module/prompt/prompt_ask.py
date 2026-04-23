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

Yönergelere uygun olarak, verilen bilgilerden uygun olan belirli unsurlara atıfta bulunarak kapsamlı bir yanıt verin.
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

    if language == "Japanese":
        return f"""
以下はプロジェクトまたはコンテキストに関する情報です:
{evidence}

ユーザーの質問:
{question}

必要に応じて関連する根拠を参照しながら、明確で完全な回答をしてください。
    """

    if language == "Spanish":
        return f"""
Información del proyecto o del contexto:
{evidence}

Pregunta del usuario:
{question}

Responde de forma clara y completa, citando la evidencia pertinente cuando corresponda.
    """

    if language == "Swahili":
        return f"""
Hapa chini kuna taarifa kuhusu mradi au muktadha:
{evidence}

Swali la mtumiaji:
{question}

Toa jibu lililo wazi na kamili, ukirejelea ushahidi husika inapofaa.
    """

    return f"""
Provided below is relevant information about the project or context:
{evidence}

Kindly respond to the following user input:
{question}

As per the guidelines, provide a comprehensive answer referencing specific elements from the provided information where applicable.
    """
