from typing import Dict, Any, List, Optional
import json
import google.generativeai as genai
from prompts import system_prompt
from prompts import field_contexts
# ============================================================================
# الجزء 1: Chat Agent - وكيل المحادثة باستخدام Gemini
# ============================================================================

class ChatAgent:
    """
    وكيل المحادثة المسؤول عن التفاعل مع الموظف الحكومي وجمع البيانات
    يستخدم Gemini 3.0 Flash للمحادثة الذكية
    """

    def __init__(self, service_form: Dict[str, Any], api_key: str):
        self.service_form = service_form
        self.conversation_history = []
        self.gathered_data = {}

        # إعداد Gemini
        genai.configure(api_key=api_key)

        # استخدام Gemini 2.0 Flash (أحدث نموذج متاح)
        self.model = genai.GenerativeModel('gemini-3-flash-preview')

        # بدء جلسة المحادثة
        self.chat = self.model.start_chat(history=[])

        # إرسال التعليمات الأولية للنموذج
        self._initialize_agent()

    def _initialize_agent(self):
        """
        يرسل التعليمات الأولية لـ Gemini لتهيئته كوكيل جمع متطلبات
        """

        response = self.chat.send_message(system_prompt)
        print(f"\n🤖 الوكيل: {response.text}\n")

    def get_missing_fields(self) -> List[tuple]:
        """
        يحدد الحقول الناقصة في النموذج
        Returns list of tuples: (section_name, field_name, field_path)
        """
        missing = []

        def check_section(section_name, section_data, parent_path=""):
            if isinstance(section_data, dict):
                for key, value in section_data.items():
                    current_path = f"{parent_path}.{key}" if parent_path else key

                    if isinstance(value, dict):
                        check_section(section_name, value, current_path)
                    elif isinstance(value, list) and len(value) == 0:
                        # قوائم فارغة تحتاج بيانات
                        if key in ["eligibility_conditions", "excluded_users", "external_systems"]:
                            missing.append((section_name, key, current_path))
                    elif value is None:
                        # حقول فارغة
                        missing.append((section_name, key, current_path))

        for section_name, section_data in self.service_form.items():
            if section_name != "meta":  # نتجاهل قسم Meta لأنه سيتم ملؤه تلقائياً
                # Pass section_name as the initial parent_path to include it in field_path
                check_section(section_name, section_data, parent_path=section_name)

        print("[DEBUG] Current state of service_form:", json.dumps(self.service_form, ensure_ascii=False, indent=2))
        print(f"[DEBUG] Missing fields: {missing}")

        return missing

    def get_field_context(self, section_name: str, field_name: str) -> str:
        """
        يوفر سياق وتوضيح لكل حقل لمساعدة Gemini في طرح السؤال المناسب
        """


        context = field_contexts.get(field_name, f"معلومات عن {field_name}")
        return f"المطلوب جمع معلومات عن: {field_name} - {context}"

    def ask_question(self, section_name: str, field_name: str, field_path: str) -> str:
        """
        يطلب من Gemini طرح سؤال للحقل المحدد
        """
        context = self.get_field_context(section_name, field_name)

        prompt = f"""الآن أحتاج أن تسأل الموظف عن المعلومة التالية:

القسم: {section_name}
الحقل: {field_name}
التوضيح: {context}

اطرح سؤالاً واضحاً ومباشراً باللغة العربية للحصول على هذه المعلومة.
السؤال فقط، بدون أي نص إضافي."""

        response = self.chat.send_message(prompt)
        return response.text.strip()

    def process_user_response(self, field_path: str, user_input: str, field_name: str) -> Any:
        """
        يستخدم Gemini لمعالجة إجابة المستخدم وتحويلها للصيغة المناسبة
        """
        # معالجة الإجابات البوليانية
        if "legal_validity" in field_path or "audit_required" in field_path or "requires_external_system" in field_path:
            prompt = f"""قم بتحليل الإجابة التالية وحدد إذا كانت تعني نعم أو لا:
الإجابة: "{user_input}"

أجب فقط بكلمة "نعم" أو "لا" بدون أي نص إضافي."""

            response = self.chat.send_message(prompt)
            answer = response.text.strip().lower()
            return "نعم" in answer or "yes" in answer

        # معالجة القوائم
        elif "eligibility_conditions" in field_path or "excluded_users" in field_path or "external_systems" in field_path:
            if "لا يوجد" in user_input or user_input.lower() in ["لا", "none", "لايوجد"]:
                return []

            prompt = f"""قم بتحليل النص التالي واستخرج القائمة كعناصر منفصلة:
النص: "{user_input}"

أعد القائمة بصيغة JSON array فقط، مثال: ["عنصر1", "عنصر2"]
فقط الـ JSON array بدون أي نص إضافي."""

            response = self.chat.send_message(prompt)
            try:
                # استخراج JSON من الإجابة
                text = response.text.strip()
                # إزالة أي markdown code blocks
                text = text.replace('```json', '').replace('```', '').strip()
                items = json.loads(text)
                return items if isinstance(items, list) else [text]
            except:
                # في حالة الفشل، نستخدم المعالجة البسيطة
                items = [item.strip() for item in user_input.replace('،', ',').split(',')]
                return [item for item in items if item]

        # النصوص العادية - نستخدم Gemini لتنقيح الإجابة
        else:
            prompt = f"""قم بتنقيح وتحسين الإجابة التالية لتكون واضحة ومختصرة:
الإجابة: "{user_input}"

أعد صياغتها بشكل احترافي ومختصر بدون تغيير المعنى."""

            response = self.chat.send_message(prompt)
            return response.text.strip()

    def update_service_form(self, field_path: str, value: Any):
        """
        يحدث النموذج بالقيمة الجديدة
        """
        path_parts = field_path.split('.')
        current = self.service_form

        for i, part in enumerate(path_parts[:-1]):
            if part not in current:
                current[part] = {}  # Ensure intermediate dictionaries exist
            current = current[part]

        current[path_parts[-1]] = value

        # Debugging statement to confirm the update
        print(f"[DEBUG] Updated {field_path} to {value}")

    def chat_turn(self, missing_fields: List[tuple]) -> Optional[tuple]:
        """
        دورة محادثة واحدة - يسأل سؤال واحد ويستقبل الإجابة
        Returns: (section, field, path) إذا كان هناك حقل تم ملؤه، أو None إذا انتهى
        """
        if not missing_fields:
            return None

        # اختيار الحقل التالي
        section, field, path = missing_fields[0]

        # طلب سؤال من Gemini
        question = self.ask_question(section, field, path)
        print(f"\n🤖 الوكيل: {question}")

        # استقبال الإجابة
        user_response = input("👤 أنت: ")

        # معالجة الإجابة باستخدام Gemini
        processed_value = self.process_user_response(path, user_response, field)

        # تحديث النموذج
        self.update_service_form(path, processed_value)

        # تأكيد للمستخدم
        confirmation_prompt = f"""قم بصياغة رسالة تأكيد قصيرة ومهنية تؤكد استلام المعلومة عن {field}.
الرسالة يجب أن تكون جملة واحدة فقط."""

        confirmation = self.chat.send_message(confirmation_prompt)
        print(f"✅ {confirmation.text}\n")

        return (section, field, path)
