import subprocess
import time
import os
import sys
import webbrowser

def run_services():
    # المسار حيث توجد الملفات (main.py و app.html)
    service_dir = os.path.join(os.getcwd(), "generated_service")

    print("🚀 جاري تشغيل نظام الخدمة الحكومية (MVP)...")

    # 1. التأكد من وجود الملفات
    if not os.path.exists(os.path.join(service_dir, "app.html")):
        print(f"❌ خطأ: لم يتم العثور على ملف app.html في {service_dir}")
        return

    # 2. تشغيل الـ Backend (FastAPI) على المنفذ 8000
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=service_dir
    )
    print("✅ Backend: يعمل على الرابط http://127.0.0.1:8000")

    # 3. تشغيل الـ Frontend (Simple HTTP Server) على المنفذ 3000
    # ملاحظة: سيقوم الخادم بعرض ملف app.html عند الدخول للرابط
    frontend_proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", "3000"],
        cwd=service_dir
    )
    print("✅ Frontend: يعمل على الرابط http://127.0.0.1:3000/app.html")

    # انتظر ثانية ثم افتح المتصفح تلقائياً
    time.sleep(2)
    webbrowser.open("http://127.0.0.1:3000/app.html")

    print("\n🔥 النظام يعمل الآن بنجاح! اضغط Ctrl+C لإيقاف جميع الخدمات.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 يتم الآن إغلاق الخدمات...")
        backend_proc.terminate()
        frontend_proc.terminate()
        print("👋 وداعاً!")

if __name__ == "__main__":
    run_services()