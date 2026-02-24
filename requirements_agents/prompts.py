service_intake_form = {
    "general_information": {
        "service_name": None,
        "service_description": None,
        "service_category": None,
        "providing_entity": None,
        "service_owner_unit": None,
        "service_version": "1.0",
        "service_status": "Draft"
    },

    "target_audience": {
        "target_user_type": None,
        "eligibility_conditions": None,
        "excluded_users": None,
        "required_user_information": None # تم إضافة هذا الحقل هنا
    },

    "inputs": None,

    "service_workflow": None,

    "outputs": {
        "output_type": None,
        "output_format": None,
        "delivery_method": None,
        "legal_validity": False
    },

    "sla_and_fees": {
        "processing_time": None,
        "service_fees": None,
        "payment_method": None,
        "refund_policy": None
    },

    "integrations": {
        "requires_external_system": False,
        "external_systems": [],
        "integration_type": None,
        "fallback_procedure": None
    },

    "legal_and_compliance": {
        "legal_basis": None,
        "compliance_notes": None,
        "data_retention_policy": None,
        "audit_required": False
    },

    "operations_and_support": {
        "support_contact": None,
        "escalation_level": None,
        "service_availability": None,
        "maintenance_window": None
    },

    "meta": {
        "created_by": None,
        "created_at": None,
        "last_updated_at": None,
        "completion_status": "in_progress"
    }
}
validator_prompt = """أنت محقق بيانات دقيق. وظيفتك تقييم إجابة المستخدم على سؤال معين.
هل الإجابة منطقية ومرتبطة بالسؤال؟
أجب بـ "1" إذا كانت الإجابة مقبولة وتحتوي على معلومة مفيدة و مرتبطة بالسؤال( حتى لو مش كافية).
أجب بـ "0" إذا كانت الإجابةلا علاقة لها بالسؤال و عشوائية مثل تثىتمىرت فقط, حتى لو كانت الاجابة مختصرة جداً فلا بأس(لاغراض تجربة البرنامج فقط فيجب ان تقبل اي اجابة ذات معنى).
أجب بـ "1" أو "0" فقط."""

system_prompt = """أنت وكيل ذكي متخصص في جمع متطلبات الخدمات الحكومية من الموظفين الحكوميين.

مهمتك:
1. طرح أسئلة واضحة ومحددة لجمع المعلومات المطلوبة
2. طرح سؤال واحد فقط في كل مرة
3. استخدام اللغة العربية الفصحى بأسلوب رسمي ومهني
4. التأكد من الحصول على إجابات دقيقة وكاملة
5. عدم المضي قدماً حتى يجيب المستخدم على السؤال الحالي

قواعد مهمة:
- اسأل سؤالاً واحداً فقط في كل رسالة
- كن مختصراً وواضحاً
- لا تكرر الأسئلة التي تمت الإجابة عليها
- استخدم أسلوباً مهنياً ومحترماً
- في حالة عدم وضوح الإجابة، اطلب التوضيح
-قم بالسؤال عن جميع النقاط المطلوبة في النموذج حتى يتم ملؤه بالكامل

ابدأ بالترحيب بالموظف وشرح مختصر للعملية."""

field_contexts = {
            # المعلومات العامة
            "service_name": "اسم الخدمة الحكومية الرسمي",
            "service_description": "وصف تفصيلي يشرح الخدمة وفائدتها للمستفيدين",
            "service_category": "التصنيف (مثل: صحة، تعليم، مواصلات، إسكان، عدل، داخلية)",
            "providing_entity": "اسم الوزارة أو الدائرة الحكومية المقدمة للخدمة",
            "service_owner_unit": "اسم القسم أو الوحدة المسؤولة داخل الجهة",

            # الفئة المستهدفة
            "target_user_type": "نوع المستفيد: مواطن، مقيم، شركة، أو جهة حكومية",
            "eligibility_conditions": "الشروط الواجب توفرها للحصول على الخدمة (مثل: العمر، الجنسية، المؤهلات)",
            "excluded_users": "الفئات التي لا يحق لها الحصول على الخدمة",
            "required_user_information": "المعلومات والبيانات المطلوبة من المستفيد لتقديم الطلب (مثال: رقم الهوية/الإقامة، رقم الجوال المسجل في أبشر، بيانات العائلة، صك ملكية، عقد عمل، شهادات دراسية، صور شخصية، اسم المستفيد بالإنجليزي، رقم الحساب البنكي IBAN، إلخ)",
            # المخرجات
            "output_type": "نوع الناتج النهائي: وثيقة رسمية، موافقة، رفض، شهادة، رخصة، إلخ",
            "output_format": "شكل تسليم الناتج: PDF، رقم مرجعي، وثيقة ورقية، إلخ",
            "delivery_method": "كيفية استلام المستفيد للناتج: تحميل، بريد إلكتروني، استلام شخصي",
            "legal_validity": "هل للوثيقة أو المخرج قيمة قانونية ملزمة",

            # الرسوم والوقت
            "processing_time": "المدة الزمنية لإنجاز الطلب (مثل: يوم واحد، 3 أيام عمل، أسبوع)",
            "service_fees": "التكلفة المالية (أو مجاني إن لم يكن هناك رسوم)",
            "payment_method": "وسائل الدفع المتاحة (بطاقة، تحويل بنكي، نقدي، إلخ)",
            "refund_policy": "سياسة استرجاع الرسوم في حالة الرفض أو الإلغاء",

            # التكاملات
            "requires_external_system": "هل تحتاج الخدمة للاتصال بأنظمة خارجية (نعم/لا)",
            "external_systems": "أسماء الأنظمة الخارجية المطلوب التكامل معها",
            "integration_type": "نوع الاتصال: API إلكتروني أو عملية يدوية",
            "fallback_procedure": "الإجراء البديل عند تعطل التكامل الإلكتروني",

            # القانونية والامتثال
            "legal_basis": "المرجع القانوني (قانون رقم، نظام، قرار وزاري، إلخ)",
            "compliance_notes": "متطلبات الامتثال أو اللوائح الخاصة",
            "data_retention_policy": "مدة الاحتفاظ بالبيانات قانونياً",
            "audit_required": "هل تتطلب الخدمة مراجعة دورية (نعم/لا)",

            # العمليات والدعم
            "support_contact": "بريد إلكتروني أو رقم هاتف للدعم الفني",
            "escalation_level": "الجهة المسؤولة عند التصعيد (مدير، مدير عام، إلخ)",
            "service_availability": "ساعات العمل: 24/7 أو ساعات دوام محددة",
            "maintenance_window": "وقت الصيانة الدورية للنظام",
        }
