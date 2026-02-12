from typing import Any, Dict
from datetime import datetime
from chat_agent import ChatAgent


def gather_service_requirements(service_form: Dict[str, Any], api_key: str) -> Dict[str, Any]:
    """
    الدالة الرئيسية التي تدير عملية جمع المتطلبات باستخدام Gemini
    """
    print("=" * 60)
    print("مرحباً بك في نظام جمع متطلبات الخدمات الحكومية")
    print("مدعوم بتقنية Gemini 3.0 Flash")
    print("=" * 60)

    # إنشاء وكيل المحادثة
    chat_agent = ChatAgent(service_form, api_key)

    # الحلقة الرئيسية لجمع البيانات
    while True:
        # الحصول على الحقول الناقصة
        missing_fields = chat_agent.get_missing_fields()

        if not missing_fields:
            # إرسال رسالة ختامية من Gemini
            final_prompt = "قم بصياغة رسالة ختامية قصيرة تشكر فيها الموظف على تعاونه وتخبره أنه تم جمع كل المعلومات بنجاح."
            final_message = chat_agent.chat.send_message(final_prompt)
            print(f"\n🤖 الوكيل: {final_message.text}\n")
            break

        # تنفيذ دورة محادثة واحدة
        result = chat_agent.chat_turn(missing_fields)

        if result is None:
            break

    # تحديث البيانات الوصفية (Meta)
    service_form["meta"]["created_at"] = datetime.now().isoformat()
    service_form["meta"]["last_updated_at"] = datetime.now().isoformat()
    service_form["meta"]["completion_status"] = "completed"

    # طلب اسم المستخدم
    print("\n" + "=" * 60)
    creator_name = input("👤 من فضلك أدخل اسمك (منشئ الخدمة): ")
    service_form["meta"]["created_by"] = creator_name

    return service_form