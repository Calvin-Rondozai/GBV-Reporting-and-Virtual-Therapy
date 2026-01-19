from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
from twilio.twiml.messaging_response import MessagingResponse
from database import db, init_db, Report, ChatMessage, User
from whatsapp_bot import handle_whatsapp_message
from therapy_service import TherapyService
from admin_routes import admin_bp
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///therapy_bot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app)
db.init_app(app)

# Initialize database
with app.app_context():
    init_db()

# Initialize therapy service - use absolute path to Models directory
models_path = os.path.join(os.path.dirname(__file__), 'Models')
therapy_service = TherapyService(models_path)

# Register admin blueprint
app.register_blueprint(admin_bp, url_prefix='/admin')

@app.route('/')
def index():
    return redirect(url_for('therapy_page'))

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'Flask app is running'}), 200

# WhatsApp webhook endpoint
@app.route('/whatsapp', methods=['POST'])
def whatsapp_webhook():
    try:
        incoming_msg = request.values.get('Body', '') or ''
        incoming_msg_stripped = incoming_msg.strip() if incoming_msg else ''
        from_number = request.values.get('From', '')
        
        print(f"Received WhatsApp message from {from_number}: {incoming_msg_stripped[:50]}")  # Debug log
        
        resp = MessagingResponse()
        
        # Handle the message - pass original for better processing
        try:
            response_text = handle_whatsapp_message(from_number, incoming_msg_stripped)
            if not response_text:
                response_text = "Sorry, I didn't understand. Please send 'hi' to start."
        except Exception as e:
            print(f"Error in handle_whatsapp_message: {e}")
            import traceback
            traceback.print_exc()
            response_text = "Sorry, I encountered an error. Please try again or send 'hi' to restart."
        
        resp.message(response_text)
        return str(resp), 200
        
    except Exception as e:
        print(f"Error in whatsapp webhook: {e}")
        import traceback
        traceback.print_exc()
        resp = MessagingResponse()
        resp.message("Sorry, I encountered an error. Please try again.")
        return str(resp), 200

# Virtual Therapy API endpoint
@app.route('/api/therapy/chat', methods=['POST'])
def therapy_chat():
    data = request.json
    user_message = data.get('message', '')
    session_id = data.get('session_id', 'default')
    
    if not user_message:
        return jsonify({'error': 'Message is required'}), 400
    
    try:
        response = therapy_service.generate_response(user_message)
        
        # Save chat message
        chat_msg = ChatMessage(
            session_id=session_id,
            user_message=user_message,
            bot_response=response,
            source='web',
            timestamp=datetime.utcnow()
        )
        db.session.add(chat_msg)
        db.session.commit()
        
        return jsonify({
            'response': response,
            'session_id': session_id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Therapy web interface
@app.route('/therapy')
def therapy_page():
    return render_template('therapy.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
