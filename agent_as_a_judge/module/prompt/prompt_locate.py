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

    if language == "Japanese":
        demonstration_japanese = """
例:
基準が次のとおりだとします:
'データベース機能は `src/db.py` に実装され、ロギングシステムは `src/logging.py` に定義されている。'

また、ワークスペース情報が次のとおりだとします:
/project
├── src
│   ├── db.py
│   ├── logging.py
│   ├── utils.py
└── tests
    ├── test_db.py
    └── test_logging.py

基準に基づき、以下のパス（5件以下）を返す必要があります。各パスはドル記号 (`$`) で囲んでください:
$/project/src/db.py$
$/project/src/logging.py$
    """
        return f"""
以下はワークスペース構造です:
{workspace_info}

以下がタスクに関連する要件です:
{criteria}

下の例と同じ形式に従い、要件に一致するファイルパスのみを返してください:
{demonstration_japanese}
    """

    if language == "Spanish":
        demonstration_spanish = """
Ejemplo:
Supón que el criterio es:
'La funcionalidad de base de datos está implementada en `src/db.py`, y el sistema de logging está definido en `src/logging.py`.'

Y que la información del workspace es:
/project
├── src
│   ├── db.py
│   ├── logging.py
│   ├── utils.py
└── tests
    ├── test_db.py
    └── test_logging.py

Con base en el criterio, deben devolverse las siguientes rutas (no más de 5), cada una envuelta entre signos de dólar (`$`):
$/project/src/db.py$
$/project/src/logging.py$
    """
        return f"""
Esta es la estructura del espacio de trabajo:
{workspace_info}

Este es el criterio relacionado con la tarea:
{criteria}

Sigue el formato del ejemplo y devuelve solo las rutas de archivo que coincidan con el criterio:
{demonstration_spanish}
    """

    if language == "Swahili":
        demonstration_swahili = """
Mfano:
Tuseme kigezo ni hiki:
'Utendaji wa database umetekelezwa katika `src/db.py`, na mfumo wa logging umefafanuliwa katika `src/logging.py`.'

Na taarifa ya workspace ni hii:
/project
├── src
│   ├── db.py
│   ├── logging.py
│   ├── utils.py
└── tests
    ├── test_db.py
    └── test_logging.py

Kwa kuzingatia kigezo hiki, njia zifuatazo (zisizozidi 5) zinapaswa kurejeshwa, kila moja ikiwa imezungushiwa alama za dola (`$`):
$/project/src/db.py$
$/project/src/logging.py$
    """
        return f"""
Huu ndio muundo wa workspace:
{workspace_info}

Hiki ndicho kigezo kinachohusiana na jukumu:
{criteria}

Fuata muundo wa mfano ulio hapa chini na urudishe njia za faili zinazolingana na kigezo tu:
{demonstration_swahili}
    """

    return f"""
Provided below is the structure of the workspace:
{workspace_info}

This is the criteria related to the task:
{criteria}

Follow the format in the example below and return only the file paths that match the criteria:
{demonstration}
    """
