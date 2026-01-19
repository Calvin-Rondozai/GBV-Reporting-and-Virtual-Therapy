from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
)
from database import db, User, Report, ChatMessage
from functools import wraps
from datetime import datetime, timedelta
from collections import Counter

admin_bp = Blueprint("admin", __name__)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin_logged_in" not in session:
            return redirect(url_for("admin.login"))
        return f(*args, **kwargs)

    return decorated_function


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session["admin_logged_in"] = True
            session["admin_username"] = username
            return redirect(url_for("admin.dashboard"))
        else:
            return render_template(
                "admin_login.html", error="Invalid username or password"
            )

    return render_template("admin_login.html")


@admin_bp.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    session.pop("admin_username", None)
    return redirect(url_for("admin.login"))


@admin_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("admin_dashboard.html")


@admin_bp.route("/api/reports")
@login_required
def get_reports():
    reports = Report.query.order_by(Report.timestamp.desc()).all()
    return jsonify([report.to_dict() for report in reports])


@admin_bp.route("/api/chats")
@login_required
def get_chats():
    chats = ChatMessage.query.order_by(ChatMessage.timestamp.desc()).limit(100).all()
    return jsonify([chat.to_dict() for chat in chats])


@admin_bp.route("/api/statistics")
@login_required
def get_statistics():
    # Total reports
    total_reports = Report.query.count()

    # Reports by age group
    age_groups = (
        db.session.query(Report.age_group, db.func.count(Report.id))
        .group_by(Report.age_group)
        .all()
    )
    age_group_data = {group: count for group, count in age_groups}

    # Reports by location (top 10)
    locations = (
        db.session.query(Report.location, db.func.count(Report.id))
        .group_by(Report.location)
        .order_by(db.func.count(Report.id).desc())
        .limit(10)
        .all()
    )
    location_data = {loc: count for loc, count in locations}

    # Reports over time (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    reports_by_date = (
        db.session.query(
            db.func.date(Report.timestamp).label("date"),
            db.func.count(Report.id).label("count"),
        )
        .filter(Report.timestamp >= thirty_days_ago)
        .group_by(db.func.date(Report.timestamp))
        .all()
    )

    time_series_data = {str(date): count for date, count in reports_by_date}

    # Total chat messages
    total_chats = ChatMessage.query.count()

    # Chats by source
    chats_by_source = (
        db.session.query(ChatMessage.source, db.func.count(ChatMessage.id))
        .group_by(ChatMessage.source)
        .all()
    )
    source_data = {source: count for source, count in chats_by_source}

    # Gender reporting stats (abuser gender)
    gender_stats = (
        db.session.query(Report.gender_of_abuser, db.func.count(Report.id))
        .filter(Report.gender_of_abuser.isnot(None))
        .group_by(Report.gender_of_abuser)
        .all()
    )
    gender_data = {gender: count for gender, count in gender_stats}

    # Top 2 violation types
    violation_types = (
        db.session.query(Report.type_of_abuse, db.func.count(Report.id))
        .filter(Report.type_of_abuse.isnot(None))
        .group_by(Report.type_of_abuse)
        .order_by(db.func.count(Report.id).desc())
        .limit(2)
        .all()
    )
    top_violations = {violation: count for violation, count in violation_types}

    # Violations by location (top locations with their violations)
    top_locations_list = [loc for loc, _ in locations[:5]]  # Get top 5 locations
    violations_by_location = {}

    for loc in top_locations_list:
        violations_at_loc = (
            db.session.query(Report.type_of_abuse, db.func.count(Report.id))
            .filter(Report.location == loc)
            .filter(Report.type_of_abuse.isnot(None))
            .group_by(Report.type_of_abuse)
            .order_by(db.func.count(Report.id).desc())
            .all()
        )
        if violations_at_loc:
            violations_by_location[loc] = {
                violation: count for violation, count in violations_at_loc
            }

    return jsonify(
        {
            "total_reports": total_reports,
            "age_groups": age_group_data,
            "locations": location_data,
            "time_series": time_series_data,
            "total_chats": total_chats,
            "chats_by_source": source_data,
            "gender_stats": gender_data,
            "top_violations": top_violations,
            "violations_by_location": violations_by_location,
        }
    )
