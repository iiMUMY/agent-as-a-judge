def get_ask_system_prompt(language="English"):

    if language == "English":
        return """
You are a knowledgeable assistant capable of answering user queries clearly and accurately.
Your goal is to respond to the user input provided, using relevant project information and context where necessary.
        """
    if language == "Arabic":
        return """
أنت مساعد معرفي قادر على الإجابة على استفسارات المستخدم بوضوح ودقة.
هدفك هو الرد على مدخلات المستخدم باستخدام معلومات المشروع والسياق المتاح عند الحاجة.
        """
    if language == "Turkish":
        return """
Kullanıcı sorularını açık ve doğru şekilde yanıtlayabilen bilgili bir asistansın.
Gerekli olduğunda proje bilgisi ve bağlamı kullanarak kullanıcı girdisine cevap ver.
        """
    if language == "Chinese":
        return """
你是一个能够清晰、准确回答用户问题的助手。
在需要时结合项目信息与上下文进行回答。
        """
    if language == "Hindi":
        return """
आप एक सहायक हैं जो उपयोगकर्ता के प्रश्नों का स्पष्ट और सटीक उत्तर देता है।
जहाँ आवश्यक हो, प्रोजेक्ट संदर्भ और जानकारी का उपयोग करके उत्तर दें।
        """

    raise NotImplementedError(f"The language '{language}' is not supported.")
