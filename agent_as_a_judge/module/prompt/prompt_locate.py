def get_prompt_locate(
    criteria: str, workspace_info: str, language: str = "English"
) -> str:

    demonstration = """
Example:
Suppose the criteria is:
'The database functionality is implemented in `src/db.py`, and the logging system is defined in `src/logging.py`.'

And the workspace information is:
/project
├── src
│   ├── db.py
│   ├── logging.py
│   ├── utils.py
└── tests
    ├── test_db.py
    └── test_logging.py

Based on the criteria, the following paths (no more than 5) should be returned, each wrapped in dollar signs (`$`):
$/project/src/db.py$
$/project/src/logging.py$
    """

    if language == "Arabic":
        return f"""
فيما يلي هيكل مساحة العمل:
{workspace_info}

وهذا هو المعيار المرتبط بالمهمة:
{criteria}

اتبع نفس صيغة المثال وأرجع فقط مسارات الملفات المطابقة للمعيار:
{demonstration}
    """

    if language == "Turkish":
        return f"""
Çalışma alanı yapısı:
{workspace_info}

Göreve ait ölçüt:
{criteria}

Örnekteki formatı takip et ve yalnızca ölçüte uyan dosya yollarını döndür:
{demonstration}
    """

    if language == "Chinese":
        return f"""
以下是工作区结构：
{workspace_info}

任务标准如下：
{criteria}

请按示例格式，仅返回符合标准的文件路径：
{demonstration}
    """

    if language == "Hindi":
        return f"""
वर्कस्पेस संरचना:
{workspace_info}

कार्य मानदंड:
{criteria}

उदाहरण के प्रारूप का पालन करें और केवल मेल खाने वाले फ़ाइल पथ लौटाएँ:
{demonstration}
    """

    return f"""
Provided below is the structure of the workspace:
{workspace_info}

This is the criteria related to the task:
{criteria}

Follow the format in the example below and return only the file paths that match the criteria:
{demonstration}
    """
