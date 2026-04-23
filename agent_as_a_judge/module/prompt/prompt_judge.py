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

Yönergelere göre, <SATISFIED> veya <UNSATISFIED> ifadelerinden birini seçin ve ardından proje bilgilerindeki belirli unsurlara (kod parçacıkları, veri örnekleri veya çıktı sonuçları gibi) atıfta bulunan kısa bir gerekçe sunun.
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

    if language == "Japanese":
        return f"""
以下はプロジェクトに関する情報です:
{evidence}

次の基準を評価してください:
{criteria}

ガイドラインに従い、<SATISFIED> または <UNSATISFIED> のいずれかを用い、その後に簡潔な根拠を示してください。
    """

    if language == "Spanish":
        return f"""
La siguiente información está relacionada con el proyecto:
{evidence}

Evalúa los siguientes criterios:
{criteria}

De acuerdo con las directrices, responde con <SATISFIED> o <UNSATISFIED> y luego proporciona una justificación breve que haga referencia a elementos específicos de la información del proyecto, como fragmentos de código, muestras de datos o resultados de salida.
    """

    if language == "Swahili":
        return f"""
Taarifa zifuatazo zinahusiana na mradi:
{evidence}

Tafadhali tathmini vigezo vifuatavyo:
{criteria}

Kulingana na mwongozo, jibu kwa <SATISFIED> au <UNSATISFIED>, kisha utoe sababu fupi inayorejelea vipengele maalum vya taarifa ya mradi, kama vipande vya msimbo, sampuli za data, au matokeo ya utekelezaji.
    """

    return f"""
Provided below is relevant information about the project:
{evidence}

Kindly perform an evaluation of the following criteria:
{criteria}

As per the guidelines, respond with either <SATISFIED> or <UNSATISFIED>, followed by a concise justification that references specific elements from the project information, such as code snippets, data samples, or output results.
    """
