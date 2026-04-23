def get_text_retrieve_prompt(
    criteria: str, long_context: str, language: str = "English"
) -> str:

    if language == "Arabic":
        return f"""
        فيما يلي سجل الإجراءات والخطوات وعمليات الملفات:
        {long_context}

        لخّص أدلة موجزة مرتبطة مباشرة بالمعيار التالي:
        {criteria}

        ركّز على آخر ذكر أو ذكرين للملفات أو الإجراءات ذات الصلة.
        يمكنني فحص الملفات محليا، لذلك لا تذكر تفاصيل الوجود أو المحتوى إلا عند الضرورة.
        قدّم تحليلا مختصرا لآخر حالة للملفات أو الدوال ذات الصلة، واستبعد المعلومات غير المرتبطة.
        """

    if language == "Turkish":
        return f"""
        Aşağıda eylem/işlem günlüğü bulunmaktadır:
        {long_context}

        Şu ölçütle doğrudan ilgili kanıtları kısa biçimde özetle:
        {criteria}

        İlgili dosya veya eylemlerin son bir ya da iki geçtiği yere odaklan.
        Dosyaları yerelde kontrol edebildiğim için dosya varlığı ve içerik ayrıntılarını verme.
        İlgili dosya veya fonksiyonların en güncel durumuna dair kısa bir analiz sun ve ilgisiz bilgileri dışarıda bırak.
        """

    if language == "Chinese":
        return f"""
        以下是操作与步骤日志：
        {long_context}

        请简要总结与下列标准直接相关的证据：
        {criteria}

        请重点关注相关文件或动作最后一到两次出现的位置。
        由于我可以在本地检查文件，请省略文件是否存在及文件内容细节。
        请简要分析相关文件或函数的最新状态，并排除无关信息。
        """

    if language == "Hindi":
        return f"""
        नीचे क्रियाओं और फ़ाइल ऑपरेशनों का लॉग है:
        {long_context}

        निम्न मानदंड से सीधे संबंधित साक्ष्य का संक्षिप्त सार दें:
        {criteria}

        संबंधित फ़ाइलों या actions के अंतिम एक-दो उल्लेखों पर ध्यान दें।
        चूंकि मैं फ़ाइलों को लोकली जांच सकता हूँ, इसलिए फ़ाइल के अस्तित्व और कंटेंट की अनावश्यक जानकारी छोड़ दें।
        संबंधित फ़ाइलों/फ़ंक्शनों की नवीनतम स्थिति का संक्षिप्त विश्लेषण दें और अप्रासंगिक जानकारी हटाएँ।
        """

    if language == "Japanese":
        return f"""
        以下は操作、手順、およびファイル処理のログです:
        {long_context}

        次の基準に直接関係する証拠を簡潔に要約してください:
        {criteria}

        関連するファイルや操作が最後に1回または2回登場した箇所に注目してください。
        私はローカルでファイルを確認できるため、ファイルの存在や内容の詳細は省略してください。
        関連するファイルや関数の最新状態を簡潔に分析し、無関係な情報は除外してください。
        """

    if language == "Spanish":
        return f"""
        A continuación se muestra un registro de acciones, pasos y operaciones sobre archivos:
        {long_context}

        Resume de forma concisa la evidencia directamente relacionada con el siguiente criterio:
        {criteria}

        Concéntrate en la última o las dos últimas menciones de archivos o acciones relevantes.
        Como puedo revisar los archivos localmente, omite detalles sobre existencia de archivos y contenido.
        Proporciona un análisis breve del estado más reciente de los archivos o funciones relevantes y excluye la información irrelevante.
        """

    if language == "Swahili":
        return f"""
        Hapa chini kuna kumbukumbu ya vitendo, hatua, na operesheni za faili:
        {long_context}

        Fupisha ushahidi unaohusiana moja kwa moja na kigezo hiki:
        {criteria}

        Zingatia kutajwa kwa mwisho au kwa mwisho wa pili kwa faili au vitendo husika.
        Kwa kuwa ninaweza kukagua faili ndani ya mazingira ya ndani, acha maelezo ya uwepo wa faili au yaliyomo ndani yake.
        Toa uchambuzi mfupi wa hali ya hivi karibuni ya faili au kazi husika, na uondoe taarifa zisizohusika.
        """

    return f"""
        Below is a log of actions, steps, and file operations:
        {long_context}

        Summarize concise evidence directly related to the following criteria:
        {criteria}

        Focus on the last one or two mentions of relevant files or actions. Since I can check the files locally, omit file existence and content details. Provide a brief analysis of the latest status of relevant files or functions. Exclude irrelevant information.
        """
