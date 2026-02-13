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

    return f"""
        Below is a log of actions, steps, and file operations:
        {long_context}

        Summarize concise evidence directly related to the following criteria:
        {criteria}

        Focus on the last one or two mentions of relevant files or actions. Since I can check the files locally, omit file existence and content details. Provide a brief analysis of the latest status of relevant files or functions. Exclude irrelevant information.
        """
