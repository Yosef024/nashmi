from typing import Dict, Any
import json
import os
import google.generativeai as genai

class ServiceBuildingAgent:
    """
    وكيل بناء الخدمة المسؤول عن كتابة الخدمة بالشكل القياسي
    يستخدم Gemini لتحسين الوثيقة
    """

    COUNTER_FILE = "service_counter.txt"  # ملف تخزين العداد
    service_counter = 0  # عداد تسلصلي للخدمات

    @classmethod
    def _load_counter(cls):
        """تحميل قيمة العداد من الملف"""
        if os.path.exists(cls.COUNTER_FILE):
            try:
                with open(cls.COUNTER_FILE, 'r', encoding='utf-8') as f:
                    cls.service_counter = int(f.read().strip())
            except:
                cls.service_counter = 0
        else:
            cls.service_counter = 0

    @classmethod
    def _save_counter(cls):
        """حفظ قيمة العداد إلى الملف"""
        with open(cls.COUNTER_FILE, 'w', encoding='utf-8') as f:
            f.write(str(cls.service_counter))

    def __init__(self, service_data: Dict[str, Any], api_key: str = None):
        # تحميل العداد من الملف عند الإنشاء الأول
        if ServiceBuildingAgent.service_counter == 0:
            ServiceBuildingAgent._load_counter()

        self.service_data = service_data
        self.api_key = api_key

        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-3-flash-preview')

    def check_service_exists(self, service_name: str) -> bool:
        """
        يتحقق من وجود الخدمة في النظام
        حالياً يرجع False دائماً (سيتم تطويره لاحقاً)
        """
        # TODO: تطوير هذه الدالة للتحقق من قاعدة البيانات
        return False

    def build_service_document(self) -> str:
        """
        يبني وثيقة الخدمة بالشكل القياسي
        """
        service_name = self.service_data["general_information"]["service_name"]

        # التحقق من عدم وجود الخدمة مسبقاً
        if self.check_service_exists(service_name):
            return f"⚠️ تنبيه: الخدمة '{service_name}' موجودة مسبقاً في النظام."

        # بناء الوثيقة القياسية
        document = self._generate_standard_document()

        return document

    def _generate_standard_document(self) -> str:
        """
        يولد الوثيقة القياسية للخدمة
        """
        data = self.service_data

        document = f"""
{'=' * 80}
                    وثيقة الخدمة الحكومية - نموذج قياسي
{'=' * 80}

📋 القسم الأول: المعلومات العامة
{'─' * 80}
اسم الخدمة:           {data['general_information']['service_name']}
وصف الخدمة:          {data['general_information']['service_description']}
فئة الخدمة:          {data['general_information']['service_category']}
الجهة المقدمة:        {data['general_information']['providing_entity']}
الوحدة المسؤولة:      {data['general_information']['service_owner_unit']}
إصدار الخدمة:        {data['general_information']['service_version']}
حالة الخدمة:         {data['general_information']['service_status']}

{'=' * 80}
👥 القسم الثاني: الفئة المستهدفة والأهلية
{'─' * 80}
نوع المستخدم المستهدف:  {data['target_audience']['target_user_type']}

شروط الأهلية:
"""
        # إضافة شروط الأهلية
        if data['target_audience']['eligibility_conditions']:
            for i, condition in enumerate(data['target_audience']['eligibility_conditions'], 1):
                document += f"  {i}. {condition}\n"
        else:
            document += "  - لا توجد شروط خاصة\n"

        document += "\nالفئات المستثناة:\n"
        if data['target_audience']['excluded_users']:
            for i, excluded in enumerate(data['target_audience']['excluded_users'], 1):
                document += f"  {i}. {excluded}\n"
        else:
            document += "  - لا يوجد\n"

        document += f"""
{'=' * 80}
📤 القسم الثالث: المخرجات
{'─' * 80}
نوع المخرج:          {data['outputs']['output_type']}
شكل المخرج:          {data['outputs']['output_format']}
طريقة التسليم:       {data['outputs']['delivery_method']}
الصلاحية القانونية:  {'نعم' if data['outputs']['legal_validity'] else 'لا'}

{'=' * 80}
💰 القسم الرابع: الرسوم والوقت
{'─' * 80}
وقت المعالجة:        {data['sla_and_fees']['processing_time']}
رسوم الخدمة:         {data['sla_and_fees']['service_fees']}
طريقة الدفع:         {data['sla_and_fees']['payment_method']}
سياسة الاسترجاع:     {data['sla_and_fees']['refund_policy']}

{'=' * 80}
🔗 القسم الخامس: التكاملات
{'─' * 80}
يتطلب أنظمة خارجية:  {'نعم' if data['integrations']['requires_external_system'] else 'لا'}
"""

        if data['integrations']['requires_external_system']:
            document += "الأنظمة الخارجية:\n"
            if data['integrations']['external_systems']:
                for i, system in enumerate(data['integrations']['external_systems'], 1):
                    document += f"  {i}. {system}\n"
            document += f"نوع التكامل:         {data['integrations']['integration_type']}\n"
            document += f"الإجراء البديل:      {data['integrations']['fallback_procedure']}\n"

        document += f"""
{'=' * 80}
⚖️ القسم السادس: القانونية والامتثال
{'─' * 80}
الأساس القانوني:     {data['legal_and_compliance']['legal_basis']}
ملاحظات الامتثال:    {data['legal_and_compliance']['compliance_notes']}
سياسة الاحتفاظ:      {data['legal_and_compliance']['data_retention_policy']}
يتطلب مراجعة:       {'نعم' if data['legal_and_compliance']['audit_required'] else 'لا'}

{'=' * 80}
🛠️ القسم السابع: العمليات والدعم
{'─' * 80}
جهة الاتصال للدعم:   {data['operations_and_support']['support_contact']}
مستوى التصعيد:       {data['operations_and_support']['escalation_level']}
توفر الخدمة:         {data['operations_and_support']['service_availability']}
نافذة الصيانة:       {data['operations_and_support']['maintenance_window']}

{'=' * 80}
📝 بيانات وصفية
{'─' * 80}
تم الإنشاء بواسطة:   {data['meta']['created_by']}
تاريخ الإنشاء:       {data['meta']['created_at']}
آخر تحديث:           {data['meta']['last_updated_at']}
حالة الاكتمال:       {data['meta']['completion_status']}

{'=' * 80}
"""

        return document

    def enhance_document_with_ai(self, document: str) -> str:
        """
        يستخدم Gemini لتحسين صياغة الوثيقة (اختياري)
        """
        if not self.api_key:
            return document

        prompt = f"""قم بمراجعة الوثيقة التالية وتحسين صياغتها مع الحفاظ على البنية والمحتوى:

{document}

أعد الوثيقة بنفس البنية مع تحسين الصياغة فقط."""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except:
            return document

    def save_to_file(self, filename: str = None):
        """
        يحفظ الوثيقة في ملف
        """
        if filename is None:
            # استخدام العداد التسلسلي لإنشاء اسم الملف
            ServiceBuildingAgent.service_counter += 1
            # حفظ العداد إلى الملف
            ServiceBuildingAgent._save_counter()
            filename = f"service{ServiceBuildingAgent.service_counter}.txt"

        document = self.build_service_document()

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(document)

        print(f"\n💾 تم حفظ وثيقة الخدمة في: {filename}")

        # حفظ نسخة JSON أيضاً
        json_filename = filename.replace('.txt', '.json')
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(self.service_data, f, ensure_ascii=False, indent=2)

        print(f"💾 تم حفظ البيانات بصيغة JSON في: {json_filename}")
