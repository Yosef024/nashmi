# main_pipeline.py
import os
import json
import re
from google import genai
from orchestrator import service_orchestrator
from backend import backend_developer_agent
from frontend import frontend_developer_agent

# --- المعلومات التي يجب تعبئتها يدوياً ---
API_KEY = "AIzaSyDsypEf_rGmTqqBmP2D3Zm7l0b3l5xjHJo"  # ضع مفتاحك هنا
client = genai.Client(api_key=API_KEY)

def clean_markdown_code(code: str) -> str:
    """
    إزالة علامات Markdown من الكود
    يزيل ```python, ```jsx, ```javascript و ``` من البداية والنهاية
    """
    # إزالة علامات البداية (```python, ```jsx, ```javascript, إلخ)
    code = re.sub(r'^```[\w]*\n?', '', code)
    # إزالة علامات النهاية (```)
    code = re.sub(r'\n?```$', '', code)
    return code.strip()

# عينة الخدمة (يمكنك استبدالها بأي JSON لخدمة أخرى)
service_sample = {
    "general_information": {
        "service_name": "خدمة إصدار جواز السفر.",
        "service_description": "طلب إصدار جواز سفر لأول مرة لأردنيين.",
        "providing_entity": "دائرة الأحوال المدنية."
    },
    "target_audience": {
        "eligibility_conditions": ["أكبر من 10 سنوات", "غير محكوم بجناية", "أردني الجنسية"],
        "required_user_information": ["الرقم الوطني", "الاسم الكامل", "تاريخ الميلاد"]
    },
    "sla_and_fees": {
        "processing_time": "أسبوع عمل واحد",
        "service_fees": "50 ديناراً"
    }
}


def run_pipeline():
    print("🚦 البدء في تنفيذ الـ Pipeline...")

    # تحويل الخدمة إلى JSON
    service_json = json.dumps(service_sample, ensure_ascii=False, indent=2)
    print('done 1')

    # 1. تشغيل المنظم
    b_specs, f_specs = service_orchestrator(client, service_json)
    print('orchestration done')

    # 2. توليد الباك إند
    backend_code = backend_developer_agent(client, b_specs)
    backend_code = clean_markdown_code(backend_code)  # تنظيف الكود
    print('backend done')

    # 3. توليد الفرونت إند
    frontend_code = frontend_developer_agent(client, f_specs)
    frontend_code = clean_markdown_code(frontend_code)  # تنظيف الكود
    print('frontend done')


    # 4. حفظ الكود في ملفات حقيقية
    os.makedirs("generated_service", exist_ok=True)

    with open("generated_service/main.py", "w", encoding="utf-8") as f:
        f.write(backend_code)

    with open("generated_service/App.html", "w", encoding="utf-8") as f:
        f.write(frontend_code)

    print("\n✅ تم توليد الخدمة بنجاح!")
    print("📁 الملفات موجودة في مجلد: generated_service")


if __name__ == "__main__":
    run_pipeline()