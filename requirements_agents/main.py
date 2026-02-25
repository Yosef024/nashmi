import json
from chat_agent import ChatAgent
from service_builder import ServiceBuildingAgent
from prompts import service_intake_form
from agents.main import run_pipeline

print("=" * 60)
print("نظام جمع متطلبات الخدمات الحكومية")
print("=" * 60)

# لا تضع المفتاح مباشرة في الكود في الإنتاج – استخدم متغيرات بيئية
api_key = 'Your_Api_key'

try:
    # المرحلة 1: جمع البيانات عبر المحادثة باستخدام ChatAgent الجديد
    print("\nمرحباً بك! سنبدأ الآن بجمع متطلبات الخدمة خطوة بخطوة.\n")

    agent = ChatAgent(service_form=service_intake_form.copy(), api_key=api_key)

    while True:
        missing = agent.get_missing_fields()
        if not missing:
            print("\n🎉 تم جمع جميع البيانات المطلوبة بنجاح!")
            completed_form = agent.service_form
            break
        agent.chat_turn(missing)

    # المرحلة 2: بناء وثيقة الخدمة القياسية
    print("\n" + "=" * 60)
    print("جاري بناء وثيقة الخدمة القياسية...")
    print("=" * 60)

    service_builder = ServiceBuildingAgent(completed_form, api_key)
    document = service_builder.build_service_document()

    # عرض الوثيقة (اختياري – يمكن تعديل حسب الحاجة)
    print("\n📄 الوثيقة المبنية:")
    print(document)

    # حفظ الوثيقة
    service_builder.save_to_file()
    print(f"\n💾 تم حفظ الوثيقة في: {service_builder.get_json_path()}")

    # تشغيل الـ pipeline الإضافي
    with open(service_builder.get_json_path(), 'r', encoding='utf-8') as f:
        data = json.load(f)

    run_pipeline(service_builder.service_data)

    print("\n✅ تم إتمام العملية بنجاح!")
    print("شكراً لاستخدامك نظام جمع متطلبات الخدمات الحكومية.")

except Exception as e:
    print(f"\n❌ حدث خطأ: {str(e)}")
    print("يرجى التحقق من API Key والاتصال بالإنترنت، أو مراجعة الكود.")
