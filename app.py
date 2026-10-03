from flask import Flask, render_template, request, jsonify, session
import json
import re
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "timetable_assistant_secret"

# ---------- LOAD DATA ----------

with open("timetable.json", "r", encoding="utf-8") as f:
    timetable = json.load(f)

try:
    with open("students.json", "r", encoding="utf-8") as f:
        students = json.load(f)
except FileNotFoundError:
    students = {}


# ---------- BASIC ----------

DAYS = [
    "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday"
]


def get_batch(roll):
    roll = int(roll)

    if 1 <= roll <= 23:
        return "T1"
    if 24 <= roll <= 46:
        return "T2"
    if 47 <= roll <= 69:
        return "T3"
    if 70 <= roll <= 92:
        return "T4"

    return None


def logged_in():
    return session.get("roll_no") is not None


def user_classes(day):
    batch = session.get("batch")
    result = []

    for item in timetable.get(day, []):
        item_batch = item.get("batch")

        if item_batch and item_batch != batch:
            continue

        result.append(item)

    return result


def format_class(item):
    text = f"⏰ <b>{item.get('time', '')}</b><br>"
    text += f"📚 <b>{item.get('subject', '')}</b><br>"

    if item.get("teacher"):
        text += f"👨‍🏫 Teacher: <b>{item['teacher']}</b><br>"

    if item.get("room"):
        text += f"🏫 Room: <b>{item['room']}</b><br>"

    if item.get("batch"):
        text += f"👥 Batch: <b>{item['batch']}</b><br>"

    return text


# ---------- DAY TIMETABLE ----------

def day_timetable(day):
    classes = user_classes(day)

    if not classes:
        return f"<b>📅 {day}</b><br><br>No classes scheduled."

    reply = f"<b>📅 {day} Timetable</b><br><br>"

    for item in classes:
        reply += format_class(item) + "<br>"

    return reply


# ---------- FULL TIMETABLE ----------

def full_timetable():
    reply = "<b>📅 YOUR FULL WEEK TIMETABLE</b><br><br>"

    for day in DAYS:
        reply += f"<hr><b>📌 {day}</b><br><br>"

        classes = user_classes(day)

        if not classes:
            reply += "No classes scheduled.<br><br>"
            continue

        for item in classes:
            reply += format_class(item) + "<br>"

    reply += "<hr><b>🏖️ Sunday</b><br><br>No classes scheduled."

    return reply


# ---------- SUBJECT DETECTION ----------

SUBJECTS = {
    "CN": [
        "computer networks",
        "computer network",
        "cn"
    ],

    "CNL": [
        "computer networks lab",
        "computer network lab",
        "cn lab",
        "cnl"
    ],

    "AI": [
        "artificial intelligence",
        "ai"
    ],

    "AIL": [
        "artificial intelligence lab",
        "ai lab",
        "ail"
    ],

    "AT": [
        "automata theory",
        "automata",
        "at"
    ],

    "DT": [
        "drone technology",
        "drone",
        "dt"
    ],

    "DTL": [
        "drone technology lab",
        "drone lab",
        "dt lab",
        "dtl"
    ],

    "ES": [
        "environmental studies",
        "environmental study",
        "es"
    ],

    "OE": [
        "open elective",
        "oe"
    ]
}


def find_subject(message):
    message = message.lower()

    # Long phrases first
    all_names = []

    for key, names in SUBJECTS.items():
        for name in names:
            all_names.append((name, key))

    all_names.sort(key=lambda x: len(x[0]), reverse=True)

    for name, key in all_names:
        pattern = r"\b" + re.escape(name) + r"\b"

        if re.search(pattern, message):
            return key

    return None


# ---------- SUBJECT CLASSES ----------

def get_subject_classes(subject_key, day=None):
    results = []

    days = [day] if day else DAYS

    for current_day in days:
        for item in user_classes(current_day):

            subject = item.get("subject", "").lower()

            aliases = SUBJECTS.get(subject_key, [])

            if any(
                re.search(
                    r"\b" + re.escape(alias.lower()) + r"\b",
                    subject
                )
                for alias in aliases
            ):
                results.append((current_day, item))

    return results


# ---------- TEACHER ----------

def get_teacher(subject_key, day=None):
    results = get_subject_classes(subject_key, day)

    if not results:
        return "❌ I couldn't find that subject in your timetable."

    teachers = []

    for _, item in results:
        teacher = item.get("teacher")

        if teacher and teacher not in teachers:
            teachers.append(teacher)

    if not teachers:
        return "❌ Teacher information is not available."

    return "👨‍🏫 Teacher: <b>" + ", ".join(teachers) + "</b>"


# ---------- ROOM ----------

def get_room(subject_key, day=None):
    results = get_subject_classes(subject_key, day)

    if not results:
        return "❌ I couldn't find that subject in your timetable."

    rooms = []

    for _, item in results:
        room = item.get("room")

        if room and room not in rooms:
            rooms.append(room)

    if not rooms:
        return "❌ Room information is not available."

    return "🏫 Room: <b>" + ", ".join(rooms) + "</b>"


# ---------- SUBJECT TIME ----------

def get_subject_time(subject_key, day=None):
    results = get_subject_classes(subject_key, day)

    if not results:
        return "❌ I couldn't find that subject in your timetable."

    reply = "<b>📚 " + subject_key + "</b><br><br>"

    for current_day, item in results:
        reply += (
            f"📅 <b>{current_day}</b><br>"
            f"⏰ <b>{item.get('time', '')}</b><br><br>"
        )

    return reply


# ---------- PRACTICAL TODAY ----------

def practical_today():
    today = datetime.now().strftime("%A")

    classes = [
        x for x in user_classes(today)
        if x.get("batch")
    ]

    if not classes:
        return f"<b>📅 {today}</b><br><br>❌ No practical today."

    reply = "<b>🧪 Today's Practical</b><br><br>"

    for item in classes:
        reply += format_class(item) + "<br>"

    return reply


# ---------- NEXT CLASS ----------

def next_class():
    now = datetime.now()
    today = now.strftime("%A")

    for item in user_classes(today):

        subject = item.get("subject", "").lower()

        # Ignore breaks/revision
        if any(x in subject for x in [
            "lunch",
            "tea",
            "break",
            "revision"
        ]):
            continue

        time = item.get("time", "")

        match = re.search(
            r"(\d{1,2}):(\d{2})\s*(AM|PM)",
            time,
            re.I
        )

        if not match:
            continue

        hour = int(match.group(1))
        minute = int(match.group(2))
        period = match.group(3).upper()

        if period == "PM" and hour != 12:
            hour += 12

        if period == "AM" and hour == 12:
            hour = 0

        start = hour * 60 + minute
        current = now.hour * 60 + now.minute

        if start > current:
            return (
                "<b>⏭️ Your Next Class</b><br><br>"
                + format_class(item)
            )

    return (
        f"<b>📅 {today}</b><br><br>"
        "🎉 No more classes today."
    )


# ---------- CHAT ----------

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():

    message = request.json.get("message", "").strip()
    msg = message.lower()

    if not message:
        return jsonify({"reply": "Please enter a message."})


    # ---------- ROLL NUMBER ----------

    match = re.search(
        r"(?:roll\s*(?:no|number)?\s*(?:is)?\s*)(\d{1,2})",
        msg
    )

    if match:

        roll = int(match.group(1))
        batch = get_batch(roll)

        if not batch:
            return jsonify({
                "reply": "❌ Roll number must be between 1 and 92."
            })

        session["roll_no"] = roll
        session["batch"] = batch

        return jsonify({
            "reply":
                f"👤 Roll No.: <b>{roll}</b><br><br>"
                f"👥 Your Batch: <b>{batch}</b> ✅"
        })


    # ---------- GREETING ----------

    if msg in ["hi", "hello", "hey", "hii"]:
        return jsonify({
            "reply":
                "Hello! 👋<br><br>"
                "Tell me your roll number first.<br><br>"
                "Example: <b>My roll number is 34</b>"
        })


    # ---------- LOGIN CHECK ----------

    if not logged_in():
        return jsonify({
            "reply":
                "Please tell me your roll number first.<br><br>"
                "Example: <b>My roll number is 34</b>"
        })


    # ---------- BATCH ----------

    if "batch" in msg:
        return jsonify({
            "reply":
                f"👤 Roll No.: <b>{session['roll_no']}</b><br><br>"
                f"👥 Batch: <b>{session['batch']}</b> ✅"
        })


    # ---------- FULL TIMETABLE ----------

    if any(x in msg for x in [
        "full timetable",
        "complete timetable",
        "whole timetable",
        "full time table",
        "complete time table"
    ]):
        return jsonify({"reply": full_timetable()})


    # ---------- SUBJECT DETECTION ----------

    subject = find_subject(msg)

    if subject:

        # Specific day
        selected_day = None

        if "today" in msg:
            selected_day = datetime.now().strftime("%A")

        elif "tomorrow" in msg:
            selected_day = (
                datetime.now() + timedelta(days=1)
            ).strftime("%A")

        else:
            for day in DAYS:
                if re.search(r"\b" + day.lower() + r"\b", msg):
                    selected_day = day
                    break


        # WHO TEACHES
        if any(x in msg for x in [
            "who teaches",
            "who is the teacher",
            "which teacher",
            "teacher of"
        ]):
            return jsonify({
                "reply": get_teacher(subject, selected_day)
            })


        # WHERE / ROOM
        if any(x in msg for x in [
            "where is",
            "where are",
            "which room",
            "what room",
            "room of"
        ]):
            return jsonify({
                "reply": get_room(subject, selected_day)
            })


        # WHEN / TIME
        if any(x in msg for x in [
            "when is",
            "what time",
            "time of"
        ]):
            return jsonify({
                "reply": get_subject_time(
                    subject,
                    selected_day
                )
            })


        # Generic subject question
        return jsonify({
            "reply": get_subject_time(
                subject,
                selected_day
            )
        })


    # ---------- TODAY ----------

    if "today" in msg:
        return jsonify({
            "reply": day_timetable(
                datetime.now().strftime("%A")
            )
        })


    # ---------- TOMORROW ----------

    if "tomorrow" in msg:
        tomorrow = datetime.now() + timedelta(days=1)

        return jsonify({
            "reply": day_timetable(
                tomorrow.strftime("%A")
            )
        })


    # ---------- PRACTICAL ----------

    if any(x in msg for x in [
        "practical today",
        "practicals today",
        "lab today",
        "labs today"
    ]):
        return jsonify({
            "reply": practical_today()
        })


    # ---------- NEXT CLASS ----------

    if any(x in msg for x in [
        "next class",
        "next lecture",
        "upcoming class",
        "what is my next"
    ]):
        return jsonify({
            "reply": next_class()
        })


    # ---------- SPECIFIC DAY ----------

    for day in DAYS:
        if re.search(r"\b" + day.lower() + r"\b", msg):
            return jsonify({
                "reply": day_timetable(day)
            })


    # ---------- HELP ----------

    return jsonify({
        "reply":
            "🤖 I can help with your timetable.<br><br>"
            "<b>Try:</b><br>"
            "• Who teaches AI?<br>"
            "• Who teaches CN?<br>"
            "• Where is my AI class?<br>"
            "• What room is my CN?<br>"
            "• When is my AI?<br>"
            "• What is my timetable today?<br>"
            "• What classes do I have tomorrow?<br>"
            "• Do I have practical today?<br>"
            "• What is my next class?<br>"
            "• Show my full timetable"
    })


# ---------- RUN ----------

if __name__ == "__main__":
    app.run(debug=True)