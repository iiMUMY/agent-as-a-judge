def get_planning_prompt(criteria: str, language: str = "English") -> str:
    """
    Returns the LLM prompt to generate a step-by-step plan for evaluating or resolving the given criteria.
    The prompt includes demonstrations to guide the LLM in creating effective plans without repeating the action descriptions.
    """
    if language == "Arabic":
        return f"""
    مطلوب منك إنشاء قائمة إجراءات لتقييم أو حل المتطلب التالي.
    اختر فقط الإجراءات الضرورية ورتبها منطقيا لجمع الأدلة والتحقق من تحقق المتطلب.

    المتطلب: "{criteria}"

    أمثلة:

    مثال 1:
    المتطلب: "يجب إنشاء تقرير ملخص وحفظه في `output/report.txt`."
    الخطة:
    - [Locate]: تحديد ملف `output/report.txt` في مساحة العمل.
    - [Read]: قراءة محتوى الملف للتحقق من وجود التقرير.
    - [Search]: البحث عن الدوال المسؤولة عن إنشاء `report.txt`.

    مثال 2:
    المتطلب: "يجب تدريب نموذج تعلم آلي وحفظه باسم `results/model.pkl`."
    الخطة:
    - [Locate]: تحديد `results/model.pkl`.
    - [Search]: البحث عن شيفرة تدريب النموذج.
    - [Read]: قراءة شيفرة التدريب للتحقق من مطابقة المتطلب.
    - [Trajectory]: تحليل مسار التطوير لفهم التعديلات السابقة.

    الآن أنشئ خطة خطوة بخطوة للمتطلب التالي:

    المتطلب: "{criteria}"

    الرد:
    """

    if language == "Turkish":
        return f"""
    Aşağıdaki gereksinimi değerlendirmek için bir eylem planı üret.
    Sadece gerekli adımları seç ve mantıklı sırada ver.

    Gereksinim: "{criteria}"

    Örnekler:

    Example 1:
    Gereksinim: "Sistem `output/report.txt` dosyasına bir özet rapor kaydetmelidir."
    Plan:
    - [Locate]: Çalışma alanında `output/report.txt` dosyasını bul.
    - [Read]: Özet rapor içeriğini doğrulamak için `report.txt` içeriğini oku.
    - [Search]: `report.txt` üreten fonksiyonları/metotları kod tabanında ara.

    Example 2:
    Gereksinim: "Makine öğrenmesi modeli eğitilmeli ve `results/model.pkl` olarak kaydedilmelidir."
    Plan:
    - [Locate]: Çalışma alanında `results/model.pkl` dosyasını bul.
    - [Search]: Kaynak dosyalarda model eğitim kodunu ara.
    - [Read]: Eğitim kodunu okuyup gereksinimle uyumunu doğrula.
    - [Trajectory]: Geçmiş geliştirme adımlarını inceleyerek önceki değişiklikleri anla.

    Şimdi aşağıdaki gereksinim için adım adım plan üret:

    Gereksinim: "{criteria}"

    Yanıt:
    """

    if language == "Chinese":
        return f"""
    请为以下要求生成评估行动计划。
    仅选择必要步骤并按合理顺序排列。

    要求: "{criteria}"

    示例：

    Example 1:
    要求: "系统必须生成摘要报告并保存为 `output/report.txt`。"
    Plan:
    - [Locate]: 在工作区中定位 `output/report.txt`。
    - [Read]: 读取 `report.txt` 内容以验证其包含摘要报告。
    - [Search]: 在代码库中搜索负责生成 `report.txt` 的函数/方法。

    Example 2:
    要求: "机器学习模型必须训练并保存为 `results/model.pkl`。"
    Plan:
    - [Locate]: 在工作区中定位 `results/model.pkl`。
    - [Search]: 在源码中搜索模型训练相关代码。
    - [Read]: 阅读训练代码以验证其符合要求。
    - [Trajectory]: 分析模型训练过程的历史轨迹以理解先前修改。

    现在，请针对以下要求生成分步骤计划：

    要求: "{criteria}"

    回复：
    """

    if language == "Hindi":
        return f"""
    निम्न आवश्यकता के मूल्यांकन हेतु एक कार्य-योजना बनाएँ।
    केवल आवश्यक चरण चुनें और तार्किक क्रम में दें।

    आवश्यकता: "{criteria}"

    उदाहरण:

    Example 1:
    आवश्यकता: "सिस्टम को सारांश रिपोर्ट बनाकर `output/report.txt` में सहेजना चाहिए।"
    Plan:
    - [Locate]: वर्कस्पेस में `output/report.txt` फ़ाइल खोजें।
    - [Read]: `report.txt` की सामग्री पढ़कर सत्यापित करें कि उसमें सारांश रिपोर्ट है।
    - [Search]: कोडबेस में `report.txt` बनाने वाले फ़ंक्शन/मेथड खोजें।

    Example 2:
    आवश्यकता: "मशीन लर्निंग मॉडल को प्रशिक्षित करके `results/model.pkl` के रूप में सहेजना चाहिए।"
    Plan:
    - [Locate]: वर्कस्पेस में `results/model.pkl` खोजें।
    - [Search]: स्रोत फ़ाइलों में मॉडल ट्रेनिंग कोड खोजें।
    - [Read]: ट्रेनिंग कोड पढ़कर जाँचें कि वह आवश्यकता से मेल खाता है।
    - [Trajectory]: मॉडल ट्रेनिंग के ऐतिहासिक विकास/परिवर्तनों का विश्लेषण करें।

    अब निम्न आवश्यकता के लिए चरण-दर-चरण योजना बनाएँ:

    आवश्यकता: "{criteria}"

    उत्तर:
    """

    return f"""
    You are tasked with generating a list of actions to evaluate or resolve the following requirement. 
    Select only the necessary actions and arrange them in a logical order to systematically collect evidence and verify whether the requirement is satisfied.

    Requirement: "{criteria}"

    Here are some examples of how to create a plan:

    Example 1:
    Requirement: "The system must generate a summary report saved as `output/report.txt`."
    Plan:
    - [Locate]: Locate the `output/report.txt` file in the workspace.
    - [Read]: Read the contents of the `report.txt` file to verify it contains the summary report.
    - [Search]: Search the codebase for any functions or methods responsible for generating `report.txt`.

    Example 2:
    Requirement: "The machine learning model must be trained and saved as `results/model.pkl`."
    Plan:
    - [Locate]: Locate `results/model.pkl` in the workspace.
    - [Search]: Search for the model training code in the source files.
    - [Read]: Read the model training code to verify it aligns with the specified requirement.
    - [Trajectory]: Analyze the historical development of the model training process to understand any prior modifications.

    Now, generate a step-by-step plan for the following requirement:

    Requirement: "{criteria}"

    Response:
    """
