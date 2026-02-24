import subprocess
import time
import os
import sys
import webbrowser

def run_platform():
    # تحديد المسارات المطلقة
    base_dir = os.getcwd()
    frontend_dir = os.path.join(base_dir, "frontend")
    backend_dir = base_dir # لأن التشغيل سيكون app.main:app

    print("🚀 جاري تشغيل منصة نشمي (نظام السيرفر المزدوج)...")

    # 1. التأكد من وجود الملفات
    if not os.path.exists(os.path.join(frontend_dir, "index.html")):
        print(f"❌ خطأ: لم يتم العثور على index.html في {frontend_dir}")
        return

    # 2. تشغيل الـ Backend (FastAPI) على المنفذ 8000
    # نستخدم -m uvicorn app.main:app للتشغيل من المجلد الرئيسي
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=backend_dir
    )
    print("✅ Backend: يعمل على http://127.0.0.1:8000")

    # 3. تشغيل الـ Frontend (Simple HTTP Server) على المنفذ 3000
    # نحدد cwd=frontend_dir ليعرض ملف index.html مباشرة
    frontend_proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", "3000"],
        cwd=frontend_dir
    )
    print("✅ Frontend: يعمل على http://127.0.0.1:3000")

    # انتظر قليلاً لضمان التشغيل ثم افتح المتصفح على الفرونت اند
    time.sleep(3)
    webbrowser.open("http://127.0.0.1:3000/index.html")

    print("\n🔥 النظام يعمل الآن! (الباك والفرونت منفصلان)")
    print("💡 اضغط Ctrl+C لإيقاف جميع العمليات.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 يتم الآن إغلاق كافة السيرفرات...")
        backend_proc.terminate()
        frontend_proc.terminate()
        print("👋 وداعاً!")

if __name__ == "__main__":
    run_platform()

# taskkill /F /IM python.exe /T