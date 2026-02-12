from requirements_gathering import gather_service_requirements
from service_builder import ServiceBuildingAgent
from prompts import service_intake_form

print("=" * 60)
print("نظام جمع متطلبات الخدمات الحكومية")
print("=" * 60)

api_key = 'AIzaSyDsypEf_rGmTqqBmP2D3Zm7l0b3l5xjHJo'

# نموذج الخدمة

try:
    # المرحلة 1: جمع البيانات عبر المحادثة
    completed_form = gather_service_requirements(service_intake_form, api_key)

    # المرحلة 2: بناء وثيقة الخدمة
    print("\n" + "=" * 60)
    print("جاري بناء وثيقة الخدمة القياسية...")
    print("=" * 60)

    service_builder = ServiceBuildingAgent(completed_form, api_key)

    # عرض الوثيقة
    document = service_builder.build_service_document()
    print(document)

    # حفظ الوثيقة
    service_builder.save_to_file()

    print("\n✅ تم إتمام العملية بنجاح!")
    print("شكراً لاستخدامك نظام جمع متطلبات الخدمات الحكومية.")

except Exception as e:
    print(f"\n❌ حدث خطأ: {str(e)}")
    print("يرجى التحقق من API Key والاتصال بالإنترنت.")