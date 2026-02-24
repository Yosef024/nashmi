import os
import sys
import importlib.util
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="منصة نشمي المركزية")

# إعدادات الـ CORS لضمان عمل الـ Fetch من أي مكان
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. تصحيح المسارات (Paths)
# نستخدم BASE_DIR لنضمن أن المسارات تعمل حتى لو شغلت السكريبت من مجلد مختلف
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SERVICES_ROOT = os.path.join(BASE_DIR, "agents", "generated_services")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

print(f"🔍 DEBUG: Searching for Frontend in: {FRONTEND_DIR}")
print(f"🔍 DEBUG: Searching for Services in: {SERVICES_ROOT}")

active_services = []


def auto_load_services():
    # تفريغ القائمة عند إعادة التحميل (Reload) لضمان عدم التكرار
    active_services.clear()

    if not os.path.exists(SERVICES_ROOT):
        os.makedirs(SERVICES_ROOT)
        return

    # إضافة مسار الخدمات إلى sys.path ليتمكن البايثون من استيراد الموديولات
    if SERVICES_ROOT not in sys.path:
        sys.path.append(SERVICES_ROOT)

    for folder in os.listdir(SERVICES_ROOT):
        folder_path = os.path.join(SERVICES_ROOT, folder)

        if os.path.isdir(folder_path):
            backend_file = os.path.join(folder_path, "backend.py")

            if os.path.exists(backend_file):
                try:
                    # تحميل الموديول ديناميكياً
                    spec = importlib.util.spec_from_file_location(f"{folder}.module", backend_file)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    # تسجيل الروابط (Endpoints)
                    if hasattr(module, "register_endpoints"):
                        module.register_endpoints(app)

                        # تحويل اسم المجلد لاسم مقروء للواجهة
                        display_name = folder.replace("service_", "").replace("_", " ")
                        active_services.append({
                            "id": folder,
                            "name": display_name,
                            "url": f"/view/{folder}/app.html"
                        })
                        print(f"✅ تم تفعيل خدمة: {display_name}")
                except Exception as e:
                    print(f"❌ خطأ في تحميل {folder}: {e}")


# تشغيل عملية التحميل
auto_load_services()


# 2. توفير الـ API الخاص بالخدمات
@app.get("/api/system/services")
async def get_services():
    return active_services


# 3. تعديل الـ Mounts لتناسب طلبك
# ملفات الخدمات المولدة (HTML/JS)
app.mount("/view", StaticFiles(directory=SERVICES_ROOT), name="services")

# واجهة المنصة الرئيسية (الـ Dashboard)
# تم تغيير المسار هنا من platform_ui إلى frontend كما طلبت
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="dashboard")
else:
    print(f"⚠️ تحذير: لم يتم العثور على مجلد الـ frontend في {FRONTEND_DIR}")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)