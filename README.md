# WhatsApp Reporting and Virtual Therapy Chatbot

A comprehensive chatbot system that provides reporting functionality and virtual therapy through WhatsApp and a web interface, with an admin dashboard for managing data and viewing analytics.

## Features

### 1. WhatsApp Bot

- **Menu System**: Respond to "hi" to get options:

  - Report submission
  - Virtual Therapy
  - Statistics
  - Physical Help information

- **Report Flow**:
  - Asks for age group (never asks for name or surname)
  - Asks for location
  - Asks "Do you have anything you'd want us to know?" (optional)
  - Confirms submission and stores data in database

### 2. Virtual Therapy

- Web-based chat interface
- Uses GPT2 model from `Backend/Models` directory
- Provides therapeutic responses to user messages
- Stores all chat conversations in database

### 3. Admin Dashboard

- Secure login system
- View all reports and chat messages
- Visual analytics with charts:
  - Reports by age group
  - Reports by location (top 10)
  - Reports over time
  - Chats by source
- Professional design

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Navigate to the Backend directory**:

   ```bash
   cd Backend
   ```

2. **Create a virtual environment** (recommended):

   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:

   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application**:
   ```bash
   python app.py
   ```

The application will start on `http://localhost:5000`

### Default Admin Credentials

- Username: `admin`
- Password: `admin123`

**⚠️ IMPORTANT**: Change the admin password in production!

## Usage

### Accessing the Web Interfaces

1. **Virtual Therapy Interface**:

   - Visit: `http://localhost:5000/therapy`
   - Start chatting with the therapy assistant

2. **Admin Dashboard**:
   - Visit: `http://localhost:5000/admin/login`
   - Login with admin credentials
   - View reports, chats, and analytics

### WhatsApp Integration

To use the WhatsApp bot:

1. **Set up Twilio Account**:

   - Sign up at [Twilio](https://www.twilio.com/)
   - Get a WhatsApp-enabled number
   - Configure webhook URL: `https://your-domain.com/whatsapp`

2. **Environment Variables** (optional):
   ```bash
   export SECRET_KEY='your-secret-key-here'
   ```

## Project Structure

```
DOC/
├── Backend/
│   ├── Models/              # GPT2 model files
│   ├── templates/           # HTML templates
│   │   ├── therapy.html
│   │   ├── admin_login.html
│   │   └── admin_dashboard.html
│   ├── app.py              # Main Flask application
│   ├── database.py         # Database models
│   ├── whatsapp_bot.py     # WhatsApp bot logic
│   ├── therapy_service.py  # Therapy model integration
│   ├── admin_routes.py     # Admin dashboard routes
│   └── requirements.txt    # Python dependencies
└── README.md
```

## Database

The application uses SQLite by default. The database file (`therapy_bot.db`) will be created automatically on first run.

### Database Tables:

- **reports**: Stores submitted reports (age group, location, additional info)
- **chat_messages**: Stores all chat conversations (user messages and bot responses)
- **users**: Stores admin user credentials

## Notes

- The therapy model may take some time to load on first use
- All personal information (name, surname) is intentionally NOT collected
- The admin dashboard provides comprehensive analytics and data visualization
- Chat messages are stored for both WhatsApp and web interface interactions

## Security Notes

- Change the default admin password in production
- Set a strong `SECRET_KEY` environment variable
- Use HTTPS in production for secure data transmission
- Consider implementing additional security measures for production deployment
