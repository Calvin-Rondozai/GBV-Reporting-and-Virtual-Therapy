from database import db, Report, ChatMessage
from datetime import datetime
import re

# Store user sessions (in production, use Redis or database)
user_sessions = {}


def handle_whatsapp_message(phone_number, message):
    """Handle incoming WhatsApp messages"""
    try:
        # Normalize message - but keep original for processing
        if not message:
            message = ""
        message_lower = message.lower().strip()
        message_original = message.strip()

        # Initialize session if needed
        if phone_number not in user_sessions:
            user_sessions[phone_number] = {"state": "idle", "report_data": {}}

        session = user_sessions[phone_number]

        # Handle greetings
        if message_lower in ["hi", "hello", "hey", "start"]:
            session["state"] = "menu"
            return get_main_menu()

        # Handle menu selection
        if session["state"] == "menu":
            result = handle_menu_selection(phone_number, message_lower, session)
            return result

        # Handle report flow - pass original message to preserve case for age groups
        if session["state"].startswith("report_"):
            result = handle_report_flow(phone_number, message_original, session)
            return result

        # Handle virtual therapy
        if session["state"] == "therapy":
            result = handle_therapy_message(phone_number, message_original, session)
            return result

        # Default response
        return "Thank you for your message. To begin, please send 'hi' and we'll be happy to assist you. 👋"
    except Exception as e:
        print(f"Error in handle_whatsapp_message: {e}")
        import traceback

        traceback.print_exc()
        return "Sorry, I encountered an error. Please send 'hi' to restart."


def get_main_menu():
    """Return main menu options"""
    return """Thank you for reaching out. We're here to support you. Please select an option:

1️⃣ *Report* - Submit a report
2️⃣ *Virtual Therapy* - Chat with our therapy assistant
3️⃣ *Statistics* - View statistics
4️⃣ *Physical Help* - Get information about physical help

Reply with the number or option name."""


def handle_menu_selection(phone_number, message, session):
    """Handle menu option selection"""
    if "1" in message or "report" in message:
        session["state"] = "report_age"
        session["report_data"] = {}
        return "We appreciate you taking this important step. Your information will be handled with care and confidentiality. Let's begin with a few questions.\n\nWhat age group are you in?\n\nPlease reply with:\n- Child (0-12)\n- Teen (13-17)\n- Young Adult (18-25)\n- Adult (26-40)\n- Middle Age (41-60)\n- Senior (60+)"

    elif "2" in message or "therapy" in message or "virtual" in message:
        session["state"] = "therapy"
        return "Welcome to Virtual Therapy. I'm here to listen and help. How are you feeling today?"

    elif "3" in message or "statistics" in message or "stats" in message:
        return get_statistics()

    elif "4" in message or "physical" in message or "help" in message:
        return get_physical_help_info()

    else:
        return "Please select a valid option:\n1️⃣ Report\n2️⃣ Virtual Therapy\n3️⃣ Statistics\n4️⃣ Physical Help"


def handle_report_flow(phone_number, message, session):
    """Handle the report submission flow"""
    state = session["state"]
    report_data = session["report_data"]

    if not message:
        return "Please provide a response."

    if state == "report_age":
        # Validate age group - check both exact matches and partial matches
        age_groups = ["child", "teen", "young adult", "adult", "middle age", "senior"]
        message_lower = message.lower().strip()

        matched_group = None
        for group in age_groups:
            if group in message_lower or message_lower in group:
                matched_group = group
                break

        # Also check for numbers that might indicate age
        if not matched_group:
            try:
                age_num = int(message_lower.split()[0])  # Try to get first number
                if age_num <= 12:
                    matched_group = "child"
                elif age_num <= 17:
                    matched_group = "teen"
                elif age_num <= 25:
                    matched_group = "young adult"
                elif age_num <= 40:
                    matched_group = "adult"
                elif age_num <= 60:
                    matched_group = "middle age"
                else:
                    matched_group = "senior"
            except (ValueError, IndexError):
                pass

        if matched_group:
            report_data["age_group"] = matched_group.title()
            session["state"] = "report_location"
            return "Thank you. To better assist you, what is your location? (City, Country or area)"
        else:
            return "Please select a valid age group:\n- Child (0-12)\n- Teen (13-17)\n- Young Adult (18-25)\n- Adult (26-40)\n- Middle Age (41-60)\n- Senior (60+)"

    elif state == "report_location":
        if message.strip():
            report_data["location"] = message.strip()
            session["state"] = "report_abuse_type"
            return "We understand this is difficult. What type of abuse did you experience?\n\nPlease reply with:\n- Physical\n- Emotional/Psychological\n- Sexual\n- Financial\n- Verbal\n- Domestic Violence\n- Other (please specify)"
        else:
            return "Please provide your location."

    elif state == "report_abuse_type":
        if message.strip():
            abuse_type = message.strip()
            # Normalize common variations
            message_lower = message.lower().strip()
            if "physical" in message_lower:
                abuse_type = "Physical"
            elif "emotional" in message_lower or "psychological" in message_lower:
                abuse_type = "Emotional/Psychological"
            elif "sexual" in message_lower:
                abuse_type = "Sexual"
            elif "financial" in message_lower:
                abuse_type = "Financial"
            elif "verbal" in message_lower:
                abuse_type = "Verbal"
            elif "domestic" in message_lower or "violence" in message_lower:
                abuse_type = "Domestic Violence"

            report_data["type_of_abuse"] = abuse_type
            session["state"] = "report_abuser_gender"
            return "Thank you for sharing. What is the gender of the abuser?\n\nPlease reply with:\n- Male\n- Female\n- Other\n- Prefer not to say"
        else:
            return "Please provide the type of abuse you experienced."

    elif state == "report_abuser_gender":
        if message.strip():
            gender = message.strip()
            message_lower = message.lower().strip()
            if "male" in message_lower and "female" not in message_lower:
                gender = "Male"
            elif "female" in message_lower:
                gender = "Female"
            elif "other" in message_lower:
                gender = "Other"
            elif "prefer not" in message_lower or "not to say" in message_lower:
                gender = "Prefer not to say"

            report_data["gender_of_abuser"] = gender
            session["state"] = "report_in_danger"
            return "Your safety is our priority. Are you still in danger?\n\nPlease reply with:\n- Yes\n- No\n- Not sure"
        else:
            return "Please provide the gender of the abuser."

    elif state == "report_in_danger":
        if message.strip():
            danger_status = message.strip()
            message_lower = message.lower().strip()
            if "yes" in message_lower:
                danger_status = "Yes"
            elif "no" in message_lower:
                danger_status = "No"
            elif "not sure" in message_lower or "unsure" in message_lower:
                danger_status = "Not sure"

            report_data["still_in_danger"] = danger_status
            session["state"] = "report_relationship"
            return "We understand. What is your relationship with the abuser?\n\nPlease reply with:\n- Family member\n- Partner/Spouse\n- Ex-partner/Ex-spouse\n- Friend\n- Colleague\n- Stranger\n- Other (please specify)"
        else:
            return "Please let us know if you are still in danger (Yes/No/Not sure)."

    elif state == "report_relationship":
        if message.strip():
            relationship = message.strip()
            message_lower = message.lower().strip()
            if "family" in message_lower:
                relationship = "Family member"
            elif "partner" in message_lower or "spouse" in message_lower:
                if "ex" in message_lower:
                    relationship = "Ex-partner/Ex-spouse"
                else:
                    relationship = "Partner/Spouse"
            elif "friend" in message_lower:
                relationship = "Friend"
            elif "colleague" in message_lower or "coworker" in message_lower:
                relationship = "Colleague"
            elif "stranger" in message_lower:
                relationship = "Stranger"

            report_data["relationship_with_abuser"] = relationship
            session["state"] = "report_what_happened"
            return "We're here to listen. Can you please tell us what happened? (You can share as much or as little detail as you're comfortable with)"
        else:
            return "Please provide your relationship with the abuser."

    elif state == "report_what_happened":
        if message.strip():
            report_data["what_happened"] = message.strip()
            session["state"] = "report_additional"
            return "Thank you for sharing. Is there anything else you'd like us to know? (You can type 'skip' or 'no' if you have nothing to add)"
        else:
            return "Please share what happened, or type 'skip' if you prefer not to share details."

    elif state == "report_additional":
        additional_info = None
        message_lower = message.lower().strip()
        if message_lower not in ["skip", "no", "n", "nothing", "none"]:
            additional_info = message.strip()

        report_data["additional_info"] = additional_info

        # Save report to database
        try:
            report = Report(
                phone_number=phone_number,
                age_group=report_data.get("age_group", ""),
                reporter_age=report_data.get("reporter_age"),
                location=report_data.get("location", ""),
                type_of_abuse=report_data.get("type_of_abuse"),
                gender_of_abuser=report_data.get("gender_of_abuser"),
                still_in_danger=report_data.get("still_in_danger"),
                relationship_with_abuser=report_data.get("relationship_with_abuser"),
                what_happened=report_data.get("what_happened"),
                additional_info=report_data.get("additional_info"),
                timestamp=datetime.utcnow(),
            )
            db.session.add(report)
            db.session.commit()

            # Reset session
            session["state"] = "idle"
            session["report_data"] = {}

            return """✅ Your report has been received. Thank you for your courage in coming forward.

We take every report seriously and will handle your information with the utmost care and confidentiality. If you indicated you are still in danger, our team will prioritize your case.

📞 *Contact Information:*
• Hotline: 0800-HELP (0800-4357) - Available 24/7
• Email: support@therapyservices.org
• Emergency: 999

*Remember:* We also offer Virtual Therapy for ongoing support. Send 'hi' and select option 2 to chat with our therapy assistant anytime you need someone to talk to.

You are not alone. We are here to support you every step of the way.

Take care of yourself, and please reach out if you need further support.

Send 'hi' to return to the main menu."""
        except Exception as e:
            db.session.rollback()
            import traceback

            error_details = traceback.format_exc()
            print(f"Error saving report: {e}")
            print(f"Traceback: {error_details}")
            print(f"Report data: {report_data}")

            # Check if it's a database schema issue
            error_str = str(e).lower()
            if "no such column" in error_str or "does not exist" in error_str:
                return """⚠️ We apologize - the system needs to be updated. Please contact support immediately, or try again after a few moments.

Your information is important to us. If the problem persists, please save a screenshot of your responses and contact support."""

            return "We sincerely apologize, but there was an error submitting your report. Please try again, or contact support if the issue persists. We are here to help."

    return "Please continue with the report process."


def handle_therapy_message(phone_number, message, session):
    """Handle therapy chat messages"""
    # In a real implementation, you'd call the therapy service here
    # For now, return a simple response
    response = "I understand. Can you tell me more about that?"

    # Save chat message
    try:
        chat_msg = ChatMessage(
            session_id=phone_number,
            user_message=message,
            bot_response=response,
            source="whatsapp",
            timestamp=datetime.utcnow(),
        )
        db.session.add(chat_msg)
        db.session.commit()
    except:
        pass

    return response


def get_statistics():
    """Get statistics about reports"""
    try:
        total_reports = Report.query.count()

        if total_reports == 0:
            return "📊 *Statistics*\n\nNo reports have been submitted yet.\n\nFor detailed statistics, please visit the admin dashboard."

        # Age groups statistics with percentages
        from sqlalchemy import func

        age_groups = (
            db.session.query(Report.age_group, func.count(Report.id))
            .group_by(Report.age_group)
            .all()
        )
        age_group_list = []
        for group, count in age_groups:
            if group:
                percentage = round((count / total_reports) * 100, 1)
                age_group_list.append(f"• {group} {percentage}%")
        age_group_stats = (
            "\n".join(age_group_list) if age_group_list else "• No data available"
        )

        # Ratio of abuse by abuser gender
        gender_ratios = (
            db.session.query(Report.gender_of_abuser, func.count(Report.id))
            .filter(Report.gender_of_abuser.isnot(None))
            .group_by(Report.gender_of_abuser)
            .all()
        )

        # Calculate totals for male and female
        total_with_gender = sum(count for _, count in gender_ratios)
        male_count = sum(
            count
            for gender, count in gender_ratios
            if gender and "male" in str(gender).lower()
        )
        female_count = sum(
            count
            for gender, count in gender_ratios
            if gender and "female" in str(gender).lower()
        )

        ratio_of_abuse = []
        if total_with_gender > 0:
            if female_count > 0:
                female_percentage = round((female_count / total_with_gender) * 100, 1)
                ratio_of_abuse.append(f". Female: {female_percentage}%")
            if male_count > 0:
                male_percentage = round((male_count / total_with_gender) * 100, 1)
                ratio_of_abuse.append(f". Male: {male_percentage}%")

        ratio_of_abuse_stats = (
            "\n".join(ratio_of_abuse) if ratio_of_abuse else ". No data available"
        )

        # Top 3 violation types (without numbers)
        violation_types = (
            db.session.query(Report.type_of_abuse, func.count(Report.id))
            .filter(Report.type_of_abuse.isnot(None))
            .group_by(Report.type_of_abuse)
            .order_by(func.count(Report.id).desc())
            .limit(3)
            .all()
        )
        top_violations_list = (
            "\n".join(
                [f"• {violation}" for violation, _ in violation_types if violation]
            )
            if violation_types
            else "• No data available"
        )

        # Top 3 locations with their top violation
        locations = (
            db.session.query(Report.location, func.count(Report.id))
            .group_by(Report.location)
            .order_by(func.count(Report.id).desc())
            .limit(3)
            .all()
        )

        location_with_violations = []
        for loc, _ in locations:
            if loc:
                # Get top violation for this location
                top_violation_for_loc = (
                    db.session.query(Report.type_of_abuse, func.count(Report.id))
                    .filter(Report.location == loc)
                    .filter(Report.type_of_abuse.isnot(None))
                    .group_by(Report.type_of_abuse)
                    .order_by(func.count(Report.id).desc())
                    .first()
                )
                if top_violation_for_loc:
                    violation_name = top_violation_for_loc[0]
                    location_with_violations.append(f"• {violation_name} - {loc}")
                else:
                    location_with_violations.append(f"• {loc}")

        location_stats = (
            "\n".join(location_with_violations)
            if location_with_violations
            else "• No data available"
        )

        # Gender violations for male abusers
        male_abuser_violations = (
            db.session.query(Report.type_of_abuse, func.count(Report.id))
            .filter(Report.gender_of_abuser.ilike("%male%"))
            .filter(Report.type_of_abuse.isnot(None))
            .group_by(Report.type_of_abuse)
            .order_by(func.count(Report.id).desc())
            .limit(3)
            .all()
        )
        male_abuser_violations_list = (
            "\n".join(
                [
                    f"• {violation}"
                    for violation, _ in male_abuser_violations
                    if violation
                ]
            )
            if male_abuser_violations
            else "• No data available"
        )

        # Gender violations for female abusers
        female_abuser_violations = (
            db.session.query(Report.type_of_abuse, func.count(Report.id))
            .filter(Report.gender_of_abuser.ilike("%female%"))
            .filter(Report.type_of_abuse.isnot(None))
            .group_by(Report.type_of_abuse)
            .order_by(func.count(Report.id).desc())
            .limit(3)
            .all()
        )
        female_abuser_violations_list = (
            "\n".join(
                [
                    f"• {violation}"
                    for violation, _ in female_abuser_violations
                    if violation
                ]
            )
            if female_abuser_violations
            else "• No data available"
        )

        stats_message = f"""📊 *Statistics Report*

*Age Groups:*
{age_group_stats}

*Ratio of Abuse*
{ratio_of_abuse_stats}

*Violations by Male Abusers:*
{male_abuser_violations_list}

*Violations by Female Abusers:*
{female_abuser_violations_list}

*Top 3 Violations:*
{top_violations_list}

*Top 3 Locations:*
{location_stats}

For detailed analytics and charts, please contact us at support@therapyservices.org."""

        return stats_message
    except Exception as e:
        print(f"Error getting statistics: {e}")
        return "Statistics are currently unavailable. Please try again later."


def get_physical_help_info():
    """Get physical help information"""
    return """🏥 *Physical Help Resources*

If you need immediate physical help:
• Emergency Services: 999
• Crisis Hotline: 0800-HELP (0800-4357) - Available 24/7
• Local Support Centers: Contact your local health department

For non-emergency support, please visit our website or contact your local health services.

Send 'hi' to return to the main menu."""
