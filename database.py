from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Report(db.Model):
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), nullable=False)
    age_group = db.Column(db.String(50), nullable=False)
    reporter_age = db.Column(db.String(10))
    location = db.Column(db.String(200), nullable=False)
    type_of_abuse = db.Column(db.String(200))
    gender_of_abuser = db.Column(db.String(50))
    still_in_danger = db.Column(db.String(20))
    relationship_with_abuser = db.Column(db.String(200))
    what_happened = db.Column(db.Text)
    additional_info = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "phone_number": self.phone_number,
            "age_group": self.age_group,
            "reporter_age": self.reporter_age,
            "location": self.location,
            "type_of_abuse": self.type_of_abuse,
            "gender_of_abuser": self.gender_of_abuser,
            "still_in_danger": self.still_in_danger,
            "relationship_with_abuser": self.relationship_with_abuser,
            "what_happened": self.what_happened,
            "additional_info": self.additional_info,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    bot_response = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(20), default="whatsapp")  # 'whatsapp' or 'web'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_message": self.user_message,
            "bot_response": self.bot_response,
            "source": self.source,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


def init_db():
    """Initialize database and create default admin user"""
    db.create_all()
    
    # Try to add missing columns to existing reports table
    try:
        from sqlalchemy import text, inspect
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('reports')]
        
        columns_to_add = {
            'type_of_abuse': 'VARCHAR(200)',
            'reporter_age': 'VARCHAR(10)',
            'gender_of_abuser': 'VARCHAR(50)',
            'still_in_danger': 'VARCHAR(20)',
            'relationship_with_abuser': 'VARCHAR(200)',
            'what_happened': 'TEXT'
        }
        
        for column_name, column_type in columns_to_add.items():
            if column_name not in columns:
                try:
                    db.session.execute(text(f"ALTER TABLE reports ADD COLUMN {column_name} {column_type}"))
                    db.session.commit()
                    print(f"✓ Added missing column: {column_name}")
                except Exception as e:
                    db.session.rollback()
                    if "duplicate column" not in str(e).lower():
                        print(f"  Could not add column {column_name}: {e}")
    except Exception as e:
        # If inspection fails or table doesn't exist, that's okay - create_all will handle it
        pass

    # Create default admin user if it doesn't exist
    admin = User.query.filter_by(username="admin").first()
    if not admin:
        admin = User(username="admin")
        admin.set_password("admin123")  # Change this in production!
        db.session.add(admin)
        db.session.commit()
        print("Default admin user created: username='admin', password='admin123'")
