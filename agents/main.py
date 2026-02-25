import os
import json
import re
from google import genai
from agents.orchestrator import service_orchestrator
from agents.backend import backend_developer_agent
from agents.frontend import frontend_developer_agent

# --- المعلومات التي يجب تعبئتها يدوياً ---
API_KEY = "Your_Api_key"  # ضع مفتاحك هنا
client = genai.Client(api_key=API_KEY)


def clean_markdown_code(code: str) -> str:
    """
    إزالة علامات Markdown من الكود
    يزيل ```python, ```jsx, ```javascript و ``` من البداية والنهاية
    """
    code = re.sub(r'^```[\w]*\n?', '', code)
    code = re.sub(r'\n?```$', '', code)
    return code.strip()


def sanitize_folder_name(name: str) -> str:
    """تحويل اسم الخدمة إلى اسم مجلد صالح"""
    name = re.sub(r'[^\w\s-]', '', name)  # إزالة الرموز الغريبة
    name = re.sub(r'\s+', '_', name.strip())  # المسافات → _
    name = name.lower()
    return name


# # عينة الخدمة (يمكنك استبدالها بأي JSON لخدمة أخرى)
# service_sample = {
#     "general_information": {
#         "service_name": "خدمة إصدار جواز السفر.",
#         "service_description": "طلب إصدار جواز سفر لأول مرة لأردنيين.",
#         "providing_entity": "دائرة الأحوال المدنية."
#     },
#     "target_audience": {
#         "eligibility_conditions": ["أكبر من 10 سنوات", "غير محكوم بجناية", "أردني الجنسية"],
#         "required_user_information": ["الرقم الوطني", "الاسم الكامل", "تاريخ الميلاد"]
#     },
#     "sla_and_fees": {
#         "processing_time": "أسبوع عمل واحد",
#         "service_fees": "50 ديناراً"
#     }
# }
import json

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


# service_sample = load_json(r'D:\d\nashmi\requirements_agents\service2.json')
# print(service_sample)
def run_pipeline(service_sample):
    print("🚦 البدء في تنفيذ الـ Pipeline...")

    # استخراج اسم الخدمة
    # service_name = service_sample["general_information"].get("service_name", "unnamed_service")
    # folder_name = sanitize_folder_name(service_name)
    #
    # # المسار النهائي للمجلد
    # base_dir = "generated_services"
    # service_dir = os.path.join(base_dir, f"service_{folder_name}")
    current_script_path = os.path.abspath(__file__)
    project_root = os.path.dirname(current_script_path)

    # 2. بناء المسار ليكون داخل مجلد agents/generated_services
    # سيقوم os.path.join بدمج المسارات بشكل صحيح حسب نظام التشغيل
    base_dir = os.path.join(project_root, "agents", "generated_services")

    # استخراج اسم الخدمة وتجهيز اسم المجلد
    service_name = service_sample["general_information"].get("service_name", "unnamed_service")
    folder_name = sanitize_folder_name(service_name)
    service_dir = os.path.join(r'D:\d\nashmi\agents\generated_services', f"service_{folder_name}")

    print(f"→ سيتم الحفظ في مسار مطلق: {service_dir}")
    print(f"→ سيتم الحفظ في: {service_dir}")

    # تحويل الخدمة إلى JSON
    service_json = json.dumps(service_sample, ensure_ascii=False, indent=2)
    print('done 1')

    # 1. تشغيل المنظم
    b_specs, f_specs = service_orchestrator(client, service_json)
    print('orchestration done')

    # 2. توليد الباك إند
    backend_code = backend_developer_agent(client, b_specs)
    backend_code = clean_markdown_code(backend_code)
    print('backend done')

    # 3. توليد الفرونت إند
    frontend_code = frontend_developer_agent(client, f_specs)
    frontend_code = clean_markdown_code(frontend_code)
    print('frontend done')

    # 4. إنشاء المجلد وحفظ الملفات
    os.makedirs(service_dir, exist_ok=True)

    backend_path = os.path.join(service_dir, "backend.py")
    frontend_path = os.path.join(service_dir, "app.html")

    with open(backend_path, "w", encoding="utf-8") as f:
        f.write(backend_code)

    with open(frontend_path, "w", encoding="utf-8") as f:
        f.write(frontend_code)

    print("\n" + "═" * 50)
    print("✅ تم توليد الخدمة بنجاح!")
    print(f"   المجلد: {service_dir}")
    print(f"   • {backend_path}")
    print(f"   • {frontend_path}")
    print("═" * 50 + "\n")


# if __name__ == "__main__":
#     service_sample = load_json(r'D:\d\nashmi\requirements_agents\service4.json')
#     run_pipeline(service_sample)
