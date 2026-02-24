import json
import os
from typing import Dict, Any, List, Tuple, Optional
from google import genai
from prompts import system_prompt, field_contexts, service_intake_form


class ValidatorAgent:
    """وكيل تحقق مرن يقبل الإجابات المنطقية"""

    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.0-flash"

    def validate(self, field_name: str, context: str, user_input: str) -> int:
        prompt = f"""
        أنت مدقق بيانات دقيق. قيم إجابة المستخدم التالية:
        الحقل: {field_name}
        السياق: {context}
        إجابة المستخدم: "{user_input}"

        أجب بـ "1" إذا كانت الإجابة مقبولة وتحتوي على معلومة مفيدة ومرتبطة بالسؤال.
        أجب بـ "0" إذا كانت الإجابة لا علاقة لها بالسؤال وعشوائية تماماً فقط مثل تقثىىلتثىهلى, و حاول تجنب استخدامها اذا ادخل المستخدم اي بيانات مفهومة.
        الرد يجب أن يكون 0 أو 1 فقط.
        """
        response = self.client.models.generate_content(model=self.model_name, contents=prompt)
        text = response.text.strip()
        return 1 if "1" in text else 0


class ChatAgent:
    def __init__(self, service_form: Dict[str, Any], api_key: str):
        self.service_form = service_form
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.0-flash"
        self.validator = ValidatorAgent(api_key)
        self.chat = self.client.chats.create(model=self.model_name)
        self.first_question = None  # لتخزين السؤال الأول
        self._initialize_agent()

    def _initialize_agent(self):
        """تهيئة الوكيل وطرح السؤال الأول"""
        # إرسال system prompt
        response = self.chat.send_message(system_prompt)

        # طباعة الترحيب في حالة CLI
        print(f"\n🤖 الوكيل: {response.text}\n")

        # جلب السؤال الأول مباشرة
        missing = self.get_missing_fields()
        if missing:
            section, field, path = missing[0]
            self.first_question = self.ask_question(section, field)
            # طباعة السؤال الأول في حالة CLI
            print(f"🤖 الوكيل: {self.first_question}\n")

    def get_initial_greeting(self) -> str:
        """يعيد رسالة الترحيب مع السؤال الأول للواجهة"""
        greeting = "مرحباً بك! سنبدأ الآن بجمع متطلبات الخدمة خطوة بخطوة."
        if self.first_question:
            return f"{greeting}\n\n{self.first_question}"
        return greeting

    def _get_value_by_path(self, path: str) -> Any:
        parts = path.split('.')
        current = self.service_form
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current

    def get_missing_fields(self) -> List[Tuple[str, str, str]]:
        missing = []
        # ترتيب الأقسام حسب الأهمية المنطقية
        section_order = [
            "general_information",
            "target_audience",
            "inputs",
            "service_workflow",
            "outputs",
            "sla_and_fees",
            "integrations",
            "legal_and_compliance",
            "operations_and_support"
        ]

        def add_if_missing(section: str, field: str, path: str):
            val = self._get_value_by_path(path)

            # منطق التخطي (Smart Logic)
            if field in ["payment_method", "refund_policy"]:
                fees = str(self._get_value_by_path("sla_and_fees.service_fees") or "").lower()
                if any(k in fees for k in ["مجاني", "مجانية", "0", "لا يوجد"]):
                    return

            if field in ["external_systems", "integration_type", "fallback_procedure"]:
                if not self._get_value_by_path("integrations.requires_external_system"):
                    return

            # التحقق من القيمة
            if val is None or val == "" or (isinstance(val, list) and len(val) == 0):
                missing.append((section, field, path))

        for section in section_order:
            section_data = self.service_form.get(section)

            # إذا كان القسم عبارة عن حقل مباشر (مثل inputs أو service_workflow)
            if section_data is None or isinstance(section_data, (list, str)):
                if section != "meta":  # تجاهل الميتا
                    add_if_missing(section, section, section)
                continue

            # إذا كان القسم قاموساً يحتوي حقولاً فرعية
            for key in section_data:
                path = f"{section}.{key}"
                add_if_missing(section, key, path)

        return missing

    def ask_question(self, section_name: str, field_name: str) -> str:
        """يطرح سؤال واحد بطريقة واضحة ومباشرة"""
        context = field_contexts.get(field_name, field_name)

        # صياغة prompt أفضل للحصول على سؤال واضح
        prompt = f"""اطرح سؤالاً واحداً واضحاً ومباشراً بالعربية لجمع المعلومة التالية:

الحقل المطلوب: {field_name}
السياق: {context}

متطلبات السؤال:
- يجب أن يكون السؤال واضحاً ومباشراً
- استخدم لغة مهنية وبسيطة
- اجعل السؤال قصيراً قدر الإمكان
- لا تضف أي مقدمات أو شروحات إضافية
- السؤال فقط بدون أي نص آخر

السؤال:"""

        response = self.chat.send_message(prompt)
        question = response.text.strip()

        # تنظيف السؤال من أي نصوص إضافية
        question = question.replace("السؤال:", "").replace("**", "").strip()

        return question

    def process_response(self, path: str, user_input: str) -> Any:
        """معالجة إجابة المستخدم وتحويلها للصيغة المناسبة"""
        # 1. معالجة القوائم
        list_fields = ["eligibility_conditions", "excluded_users", "required_user_information",
                       "inputs", "service_workflow", "external_systems"]

        if any(x in path for x in list_fields):
            prompt = f"""استخرج قائمة عناصر من النص التالي وأعدها كـ JSON array:
النص: "{user_input}"

متطلبات:
- أعد JSON array فقط بدون أي نص إضافي
- كل عنصر يجب أن يكون جملة واضحة ومفيدة
- إذا كان النص يحتوي على عنصر واحد فقط، أعده في array

مثال: ["العنصر الأول", "العنصر الثاني"]
"""
            res = self.client.models.generate_content(model=self.model_name, contents=prompt)
            try:
                data = res.text.strip()
                # تنظيف الاستجابة
                data = data.replace('```json', '').replace('```', '').strip()
                parsed = json.loads(data)
                return parsed if isinstance(parsed, list) else [parsed]
            except:
                # fallback: تقسيم بسيط
                return [i.strip() for i in user_input.split('و') if i.strip()]

        # 2. معالجة البوليان
        if any(x in path for x in ["legal_validity", "audit_required", "requires_external_system"]):
            user_lower = user_input.lower()
            return ("نعم" in user_input or "yes" in user_lower or
                    "صحيح" in user_input or "true" in user_lower)

        # 3. النصوص العادية - تحسين الصياغة
        prompt = f"""حسّن صياغة النص التالي ليصبح رسمياً ومهنياً مع الحفاظ على المعنى الأصلي:
النص: "{user_input}"

المتطلبات:
- أعد النص المحسّن فقط بدون أي إضافات
- احتفظ بجميع المعلومات المهمة
- استخدم لغة رسمية ومهنية
- اجعله مختصراً وواضحاً

النص المحسّن:"""

        res = self.client.models.generate_content(model=self.model_name, contents=prompt)
        improved = res.text.strip()

        # تنظيف النص
        improved = improved.replace("النص المحسّن:", "").replace("**", "").strip()

        return improved

    def update_form(self, path: str, value: Any):
        """تحديث النموذج بالقيمة الجديدة"""
        parts = path.split('.')
        curr = self.service_form
        for p in parts[:-1]:
            if p not in curr:
                curr[p] = {}
            curr = curr[p]
        curr[parts[-1]] = value

    def get_progress_info(self) -> Dict[str, Any]:
        """يعيد معلومات عن التقدم الحالي"""
        total_fields = len(self._get_all_field_paths())
        missing = len(self.get_missing_fields())
        completed = total_fields - missing

        return {
            "total": total_fields,
            "completed": completed,
            "remaining": missing,
            "percentage": int((completed / total_fields) * 100) if total_fields > 0 else 0
        }

    def _get_all_field_paths(self) -> List[str]:
        """يعيد جميع مسارات الحقول في النموذج"""
        paths = []
        section_order = [
            "general_information", "target_audience", "inputs", "service_workflow",
            "outputs", "sla_and_fees", "integrations", "legal_and_compliance",
            "operations_and_support"
        ]

        for section in section_order:
            section_data = self.service_form.get(section)
            if section_data is None or isinstance(section_data, (list, str)):
                if section != "meta":
                    paths.append(section)
            else:
                for key in section_data:
                    paths.append(f"{section}.{key}")

        return paths

    def chat_turn(self, missing_fields: List[Tuple[str, str, str]]):
        """دورة محادثة واحدة - للاستخدام في CLI"""
        section, field, path = missing_fields[0]
        question = self.ask_question(section, field)

        while True:
            print(f"\n🤖 الوكيل: {question}")
            user_ans = input("👤 أنت: ").strip()

            if not user_ans:
                continue

            if self.validator.validate(field, field_contexts.get(field, ""), user_ans):
                processed = self.process_response(path, user_ans)
                self.update_form(path, processed)
                print(f"✅ تم تسجيل {field}.")
                break
            else:
                print("⚠️ عذراً، الإجابة غير واضحة بما يكفي. يرجى المحاولة مرة أخرى.")

    def process_web_message(self, user_message: str) -> Dict[str, Any]:
        """
        معالجة رسالة من واجهة الويب
        يعيد: dict يحتوي على الاستجابة والحالة
        """
        missing = self.get_missing_fields()

        if not missing:
            return {
                "status": "completed",
                "message": "تم جمع جميع المعلومات المطلوبة!",
                "completed": True
            }

        section, field, path = missing[0]

        # التحقق من صحة الإجابة
        is_valid = self.validator.validate(
            field,
            field_contexts.get(field, ""),
            user_message
        )

        if not is_valid:
            return {
                "status": "invalid",
                "message": "⚠️ عذراً، الإجابة غير واضحة أو لا تتعلق بالسؤال. يرجى تقديم إجابة أوضح.",
                "completed": False,
                "field": field
            }

        # معالجة وحفظ الإجابة
        try:
            processed_value = self.process_response(path, user_message)
            self.update_form(path, processed_value)

            # التحقق من وجود المزيد من الحقول
            missing = self.get_missing_fields()

            if not missing:
                # انتهت جميع الأسئلة
                progress = self.get_progress_info()
                return {
                    "status": "success",
                    "message": "🎉 رائع! تم جمع جميع المعلومات المطلوبة بنجاح.",
                    "completed": True,
                    "progress": progress
                }

            # طرح السؤال التالي
            next_section, next_field, next_path = missing[0]
            next_question = self.ask_question(next_section, next_field)
            progress = self.get_progress_info()

            return {
                "status": "success",
                "message": f"✅ تم تسجيل الإجابة.\n\n{next_question}",
                "completed": False,
                "next_field": next_field,
                "progress": progress
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"حدث خطأ في معالجة الإجابة: {str(e)}",
                "completed": False
            }