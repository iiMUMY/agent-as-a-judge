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

    raise NotImplementedError(f"The language '{language}' is not supported.")
