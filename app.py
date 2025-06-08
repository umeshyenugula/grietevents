from flask import Flask, render_template, session, request, jsonify, url_for, flash, redirect
from pymongo import MongoClient
from contactformsender import send_html_email
from contactsender import send_html_email_contact
from datetime import datetime, timedelta
from pymongo import ReturnDocument 
from dotenv import load_dotenv
import os
app = Flask(__name__)
app.secret_key = 'ABCDEFGHIJKLMNOP'
client = MongoClient("mongodb+srv://grietevents:Umesh%400531@logindata.fugvbow.mongodb.net/")
db = client["grietevents"]
users = db["users"]
announcements_collection = db["announcements"]
@app.route("/")
def home():
    return render_template("index.html")
@app.route("/announcements")
def get_announcements():
    try:
        announcements = announcements_collection.find()
        output = [{"message": a["message"], "date": a.get("date", "") ,"eventname":a.get("eventname","None")} for a in announcements]
        return jsonify(output)
    except Exception as e:
        return jsonify({"error": str(e)})
@app.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        user = users.find_one({'username': username})
        if user:
            if password == user['password']:
                session['username'] = username
                session['eventname'] = user['eventname'] 
                flash("Login successful!")
                return redirect(url_for("dashboard"))
            else:
                flash("Incorrect password.")
        else:
            flash("Username does not exist.")
        return redirect(url_for("login"))
    return render_template("login.html")
@app.route("/register", methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        data = {
            'name': request.form.get("name"),
            'username': request.form.get("username"),
            'password': request.form.get("password"),
            'email': request.form.get("email"),
            'subevents': request.form.get("subevents", 'None'),
            'eligibity': request.form.get("eligibity"),
            'eventname': request.form.get("eventname"),
            'eventdate': request.form.get("eventdate"),
            'eventtype': request.form.get("eventtype"),
            'eventsize': request.form.get("eventsize"),
            'location': request.form.get("location")
        }
        users.insert_one(data)
        return redirect(url_for("login"))
    return render_template("register.html")
@app.route("/t&c")
def tandc():
    return render_template("t&c.html")
@app.route("/dashboard")
def dashboard():
    if 'username' not in session:
        flash("Please log in first.")
        return redirect(url_for("login"))
    username = session['username']
    user = users.find_one({'username': username})
    eventname = user['eventname']
    event_collection = db[eventname]
    count = event_collection.count_documents({})
    return render_template("dashboard.html",
                           Event_Name=user['eventname'],
                           et=user['eventtype'],
                           ed=user['eventdate'],
                           es=user['eventsize'],
                           loc=user['location'],
                           sb=user['subevents'],
                           num=count)
@app.route("/dashboard-info")
def dashboard_info():
    if 'username' not in session:
        return "Unauthorized", 401
    username = session['username']
    user = users.find_one({'username': username})
    eventname = user['eventname']
    event_collection = db[eventname]
    count = event_collection.count_documents({})
    return render_template("partials/dashboard_info.html",
                           Event_Name=user['eventname'],
                           et=user['eventtype'],
                           ed=user['eventdate'],
                           es=user['eventsize'],
                           loc=user['location'],
                           sb=user['subevents'],
                           num=count)
@app.route("/announcement")
def annouce():
    return render_template("partials/annoucements.html")
@app.route("/post-announcement", methods=["POST"])
def post_announcement():
    if 'username' not in session:
        return "Unauthorized", 401
    message = request.form.get("message")
    if not message:
        return "No message provided.", 400
    announcements_collection.insert_one({
        "message": message,
        "eventname":session['eventname'],
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    return redirect(url_for("dashboard"))
@app.route("/add-participant",methods=['POST','GET'])
def add_participant_partial():
    return render_template("partials/addparticipant.html")
@app.route("/submit-participant",methods=['POST'])
def sendapplicant():
    if 'username' not in session:
        return "Unauthorized", 401
    if request.method=='POST':
         data = {
            'name': request.form.get("name"),
            'branch': request.form.get("branch"),
            'RollNo': request.form.get("rollno"),
            'email': request.form.get("email"),
            'subevents': request.form.get("subevent", ''),
            'teamsize': request.form.get("teamsize"),
            'amount': request.form.get("amount"),
            'contact': request.form.get("contact"),
            'date': datetime.now()


         }
         username = session['username']
         user = users.find_one({'username': username})
         eventname = user['eventname']
         eventdb = db[eventname]
         count = eventdb.count_documents({})
         data["Verification"]=f'GRIET{eventname}-{count+1}'
         eventdb.insert_one(data)
         send_html_email(data['email'],data['name'],user['eventdate'],data['RollNo'],data['branch'],user['eventname']+"-"+data['subevents'],data["Verification"])
         return redirect(url_for('dashboard'))
@app.route("/see-participants", methods=['GET'])
def see_participants_page():
    if 'username' not in session:
        flash("Please log in first.")
        return redirect(url_for('login'))

    return render_template("partials/seeparticipants.html")
@app.route("/api/seeparticipants", methods=['GET'])
def get_participants_json():
    if 'username' not in session:
        return jsonify([])
    username = session['username']
    user = users.find_one({'username': username})
    eventname = user['eventname']
    event_collection = db[eventname]
    participants = list(event_collection.find())
    result = []
    for p in participants:
        result.append({
            "name": p.get("name", ""),
            "sub_event": p.get("subevents", ""),
            "amount_paid": p.get("amount", ""),
            "email": p.get("email", ""),
            "contact": p.get("contact", ""),
            "team_size": p.get("teamsize", ""),
            "roll_no": p.get("RollNo", ""),
            "branch": p.get("branch", "")
        })
    return jsonify(result)
@app.route("/update-event",methods=['GET'])
def update_event_partial():
    username=session['username']
    user = users.find_one({'username': username})
    return render_template("partials/updatevents.html",
                           et=user['eventtype'],
                           ed=user['eventdate'],
                           es=user['eventsize'],
                           loc=user["location"],
                           se=user['subevents'],
                           el=user['eligibity'])
@app.route("/update", methods=['POST'])
def updatedetails():
    if 'username' not in session:
        return "Unauthorized", 401
    fields = ["eventdate", "eventtype", "eventsize", "location", "subevents", "eligibity"]
    update_fields = {}
    for field in fields:
        value = request.form.get(field)
        if value is not None and value.strip() != "":
            update_fields[field] = value
    if update_fields:
        users.find_one_and_update(
            {"username": session['username']},
            {"$set": update_fields},
            return_document=ReturnDocument.AFTER
        )
        return redirect(url_for("dashboard"))
    else:
        return redirect(url_for("dashboard"))
@app.route("/transactions")
def transactions_partial():
    if 'username' not in session:
        flash("Please log in first.")
        return redirect(url_for('login'))

    return render_template("partials/seetransactions.html")
@app.route("/transactions-data", methods=["GET"])
def transactions_data():
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    username = session['username']
    user = users.find_one({"username": username})
    eventname = user.get("eventname")
    event_collection = db[eventname]
    participants = list(event_collection.find())
    result = []
    total_amount = 0
    for p in participants:
        amount_str = p.get("amount", "0")
        try:
            amount = int(amount_str)
        except ValueError:
            amount = 0
        total_amount += amount
        result.append({
            "name": p.get("name", ""),
            "roll_no": p.get("RollNo", ""),
            "subevent": p.get("subevents", ""),
            "teamsize": p.get("teamsize", ""),
            "amount": amount_str,
            "verification_number": p.get("Verification", "")
        })
    return jsonify({"participants": result, "total_amount": total_amount})
@app.route("/stats")
def stats_partial():
    return render_template("partials/stats.html")
@app.route("/api/stats-data")
def stats_data():
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    username = session['username']
    user = users.find_one({'username': username})
    eventname = user['eventname']
    event_collection = db[eventname]
    today = datetime.now()
    dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
    registrations = []
    amounts = []
    for d in dates:
        start = datetime.strptime(d, "%Y-%m-%d")
        end = start + timedelta(days=1)
        regs = list(event_collection.find({
            "date": {"$gte": start, "$lt": end}
        }))
        registrations.append(len(regs))
        day_total = 0
        for p in regs:
            amount = p.get("amount", "0")
            try:
                amount_int = int(amount)
            except (ValueError, TypeError):
                amount_int = 0
            day_total += amount_int
        amounts.append(day_total)
    return jsonify({
        "dates": dates,
        "registrations": registrations,
        "amounts": amounts
    })
@app.route("/verify")
def verify_partial():
    return render_template("partials/verification.html")
@app.route("/api/verify")
def api_verify():
    code = request.args.get("code")
    eventname = session.get('eventname')
    event_collection = db[eventname]
    participant = event_collection.find_one({"Verification": code})
    if not participant:
        return jsonify({"error": "Participant not found."})
    return jsonify({
        "name": participant["name"],
        "branch": participant["branch"],
        "roll_no": participant["RollNo"],
        "event": participant["subevents"],
        "date": participant["date"],
        "teamsize": participant["teamsize"],
        "amount_paid": participant["amount"]
    })
@app.route("/profile")
def profile():
    if 'username' not in session:
        return "Unauthorized", 401
    username=session['username']
    user = users.find_one({'username': username})
    return render_template("partials/profile.html",
                           name=user['name'],
                           email=user['email'],
                           username=user['username'],
                           event=user['eventname'],
                           date=user['eventdate'],
                           subevents=user['subevents'])
@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))
@app.route("/about")
def about():
    return render_template("about.html")
@app.route("/contact")
def contact():
    return render_template("contact.html")
@app.route("/submit_contact", methods=['POST', 'GET'])
def sendcontact():
    name = request.form.get("name")
    email = request.form.get("email")
    subject = request.form.get("subject")
    message = request.form.get("message")
    msg = send_html_email_contact(email, subject, name, message)
    flash(f"Message Sent with Message id : {msg}")
    return redirect(url_for("contact"))
if __name__ == "__main__":
    app.run(debug=True)
