"""
Flask Web Server for Government Services Requirements Gathering Chatbot
Integrates the existing chatbot backend with a web interface
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
import os
import threading
from typing import Dict, Any
from datetime import datetime

# Import existing chatbot modules
from chat_agent import ChatAgent
from service_builder import ServiceBuildingAgent
from prompts import service_intake_form

# Try to import the agents pipeline, handle if not available
try:
    from agents.main import run_pipeline
    PIPELINE_AVAILABLE = True
except ImportError:
    PIPELINE_AVAILABLE = False
    print("⚠️  Warning: agents.main module not found. Pipeline will be skipped.")

# Flask app setup
app = Flask(__name__)
CORS(app)

# Global variables for chat session
chat_agent = None
api_key = 'AIzaSyDsypEf_rGmTqqBmP2D3Zm7l0b3l5xjHJo'  # Move to environment variables in production
session_active = False
service_form_copy = None


def initialize_chat_session():
    """Initialize a new chat session"""
    global chat_agent, session_active, service_form_copy
    
    try:
        service_form_copy = service_intake_form.copy()
        chat_agent = ChatAgent(service_form=service_form_copy, api_key=api_key)
        session_active = True
        return True
    except Exception as e:
        print(f"Error initializing chat session: {e}")
        return False


@app.route('/')
def index():
    """Serve the main HTML page"""
    try:
        with open('chatbot_ui.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Error: chatbot_ui.html not found", 404


@app.route('/init', methods=['GET'])
def init_session():
    """Initialize the chat session"""
    global chat_agent
    
    if initialize_chat_session():
        # الحصول على الترحيب الأولي مع السؤال الأول
        initial_message = chat_agent.get_initial_greeting()

        return jsonify({
            'status': 'success',
            'message': initial_message
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'فشل في تهيئة الجلسة'
        }), 500


@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    global chat_agent, session_active, service_form_copy

    if not session_active or chat_agent is None:
        return jsonify({
            'status': 'error',
            'message': 'الجلسة غير نشطة. يرجى تحديث الصفحة.'
        }), 400

    try:
        data = request.json
        user_message = data.get('message', '').strip()

        if not user_message:
            return jsonify({
                'status': 'error',
                'message': 'الرجاء إدخال رسالة'
            }), 400

        # استخدام الدالة الجديدة لمعالجة الرسالة
        result = chat_agent.process_web_message(user_message)

        # إذا تم الانتهاء من جميع الأسئلة، نقوم ببناء الوثيقة
        if result.get('completed'):
            session_active = False
            finalize_session()

            return jsonify({
                'status': 'success',
                'response': result['message'],
                'completed': True
            })

        # إذا كانت الإجابة غير صحيحة
        if result['status'] == 'invalid':
            return jsonify({
                'status': 'success',
                'response': result['message'],
                'completed': False
            })

        # إذا كانت الإجابة صحيحة ويوجد المزيد من الأسئلة
        return jsonify({
            'status': 'success',
            'response': result['message'],
            'completed': False,
            'progress': result.get('progress', {})
        })

    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'حدث خطأ: {str(e)}'
        }), 500


def finalize_session():
    """Finalize the session and build the service document"""
    global service_form_copy

    try:
        # Update metadata
        service_form_copy["meta"]["created_at"] = datetime.now().isoformat()
        service_form_copy["meta"]["last_updated_at"] = datetime.now().isoformat()
        service_form_copy["meta"]["completion_status"] = "completed"
        service_form_copy["meta"]["created_by"] = "Web User"

        # Build service document
        print("\n" + "=" * 60)
        print("جاري بناء وثيقة الخدمة القياسية...")
        print("=" * 60)

        service_builder = ServiceBuildingAgent(service_form_copy, api_key)
        document = service_builder.build_service_document()

        # Save the document
        service_builder.save_to_file()
        print(f"\n💾 تم حفظ الوثيقة في: {service_builder.get_json_path()}")

        # Run pipeline if available
        if PIPELINE_AVAILABLE:
            try:
                print("\n" + "=" * 60)
                print("جاري تشغيل pipeline المعالجة...")
                print("=" * 60)
                run_pipeline(service_form_copy)
                print("\n✅ تم إكمال pipeline بنجاح!")
            except Exception as e:
                print(f"\n⚠️  خطأ في تشغيل pipeline: {e}")

        print("\n✅ تم إتمام العملية بنجاح!")

    except Exception as e:
        print(f"\n❌ خطأ في إنهاء الجلسة: {e}")
        import traceback
        traceback.print_exc()


@app.route('/status', methods=['GET'])
def status():
    """Get current session status"""
    global session_active, chat_agent

    progress = None
    if chat_agent:
        try:
            progress = chat_agent.get_progress_info()
        except:
            pass

    return jsonify({
        'active': session_active,
        'initialized': chat_agent is not None,
        'progress': progress
    })


@app.route('/reset', methods=['POST'])
def reset_session():
    """Reset the chat session"""
    global session_active, chat_agent, service_form_copy

    session_active = False
    chat_agent = None
    service_form_copy = None

    if initialize_chat_session():
        initial_message = chat_agent.get_initial_greeting()
        return jsonify({
            'status': 'success',
            'message': 'تم إعادة تعيين الجلسة بنجاح',
            'initial_message': initial_message
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'فشل في إعادة تعيين الجلسة'
        }), 500


def run_server(host='127.0.0.1', port=5000, debug=False):
    """Run the Flask server"""
    print("=" * 60)
    print("🚀 نظام جمع متطلبات الخدمات الحكومية - واجهة الويب")
    print("=" * 60)
    print(f"\n📡 الخادم يعمل على: http://{host}:{port}")
    print(f"🌐 افتح المتصفح وانتقل إلى العنوان أعلاه")
    print("\n⌨️  اضغط Ctrl+C لإيقاف الخادم")
    print("=" * 60 + "\n")

    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == '__main__':
    # Check if chatbot_ui.html exists
    if not os.path.exists('chatbot_ui.html'):
        print("❌ Error: chatbot_ui.html not found!")
        print("Please make sure chatbot_ui.html is in the same directory as this script.")
        exit(1)

    # Check if API key is set
    if not api_key or api_key == 'YOUR_API_KEY_HERE':
        print("❌ Error: Please set your API key in the script!")
        exit(1)

    # Run the server
    try:
        run_server(host='127.0.0.1', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n\n👋 تم إيقاف الخادم. شكراً لاستخدامك النظام!")
    except Exception as e:
        print(f"\n❌ خطأ في تشغيل الخادم: {e}")