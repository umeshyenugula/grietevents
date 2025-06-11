from flask import Flask, render_template, session, request, jsonify, url_for, flash, redirect,send_file
import qrcode
from pymongo import MongoClient
from contactformsender import send_html_email
from contactsender import send_html_email_contact
from datetime import datetime, timedelta
from pymongo import ReturnDocument 
from dotenv import load_dotenv
import os
import secrets
import qrcode
from io import BytesIO
from otpverify import send_otp
from copy import deepcopy
from bson import ObjectId
from PIL import Image, ImageDraw
load_dotenv()  
mongo_uri = os.getenv("MONGO_URI")
app = Flask(__name__)
secret_key = secrets.token_hex(32)  
app.secret_key = secret_key
client = MongoClient(mongo_uri)
db = client["grietevents"]
users = db["users"]
temp=db['SelfRegistrations']
announcements_collection = db["announcements"]
@app.route("/")
def home():
    return render_template("index.html")
@app.route("/announcements")
def get_announcements():
    try:
        announcements = announcements_collection.find().sort("date", -1) 
        output = [
            {
                "message": a["message"],
                "date": a.get("date", ""),
                "eventname": a.get("eventname", "None")
            } 
            for a in announcements
        ]
        return jsonify(output)
    except Exception as e:
        return jsonify({"error": str(e)})
@app.route("/student-register")
def student_register():
    return render_template("selfregistrations.html")
@app.route("/get-events", methods=["GET"])
def get_events():
    try:
        events = users.distinct("eventname")
        return jsonify({"status": "success", "events": events})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
@app.route("/get-subevents/<eventname>")
def get_subevents(eventname):
    try:
        subevents_cursor = users.find({"eventname": eventname}, {"subevents": 1})
        subevent_set = set()
        for doc in subevents_cursor:
            sub_str = doc.get("subevents", "")
            subevent_set.update([s.strip() for s in sub_str.split(",") if s.strip()])
        return jsonify({"status": "success", "subevents": list(subevent_set)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
@app.route("/selfregister", methods=['POST'])
def selfregister():
    if request.method == 'POST':
        data = {
            'name': request.form.get("name"),
            'branch': request.form.get("branch"),
            'RollNo': request.form.get("rollno"),
            'email': request.form.get("email"),
            'eventname': request.form.get("eventname"),
            'subevents': request.form.get("subevent"),
            'teamsize': request.form.get("teamsize"),
            'contact': request.form.get("contact"),
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S') 
        }
        session['data'] = data
        return redirect(url_for('payment'))
@app.route("/payment")
def payment():
    set=session.get("data")
    if (not set):
       return "dataLostRefilAgain"
    formdata=session['data']
    eventname=formdata['eventname']
    requests=db['requests']
    paydetails=requests.find_one({"eventname":eventname})
    if(paydetails):
        upi = paydetails.get("upi_id")
        subevents = paydetails.get("subevents", {})
        for subevent, amount in subevents.items():
            if(subevent==formdata['subevents']):
                price=amount
                session['amount']=price
        data=f'upi://pay?pa={upi}&mode=028&mc=0000&am={price}'
        session['qrdata']=data
        return render_template("payment.html",
                                amount=price, 
                               image_url=url_for('generate_qr'))
    else:
        return "Organizer is Not Opened for Self Registration Contact Organizer For More details"
def sanitize_for_mongo(data):
    """Recursively converts ObjectIds and other non-serializables to strings."""
    if isinstance(data, dict):
        return {k: sanitize_for_mongo(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_for_mongo(v) for v in data]
    elif isinstance(data, ObjectId):
        return str(data)
    return data

@app.route("/submit-payment", methods=["POST"])
def submit_payment():
    txn_number = request.form.get("transaction")
    if txn_number:
        raw_data = session.get('data', {})
        clean_data = deepcopy(raw_data)
        clean_data = sanitize_for_mongo(clean_data) 
        clean_data['txn_number'] = txn_number
        clean_data['amount'] = session.get('amount', 0)
        session.pop("amount", None)
        temp.insert_one(clean_data)
        flash("Payment Submitted Successfully!Details Sent to Organizer for Approval,  Once Approved Your will receive confirmation mail ")
        return redirect(url_for('home'))
    return "Error: No Transaction Number Entered"
@app.route("/generate-qr")
def generate_qr():
    data=session['qrdata']
    img = qrcode.make(data)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype='image/png') 
@app.route("/login", methods=['POST', 'GET'])
def login():
    username=session.get("username")
    if(username):
        return redirect(url_for("dashboard"))
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
@app.route("/recovery", methods=['GET', 'POST'])
def recovery():
    if request.method == 'POST':
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()

        if username:
            recvar = username
        elif email:
            recvar = email
        else:
            flash("Enter at least one field for password recovery", "error")
            return render_template("recovery.html")
        query = {"email": recvar} if "@" in recvar else {"username": recvar}
        user = users.find_one(query)

        if user:
            otp = send_otp(user['email'], user['eventname'], user['name'], "recotp.html")
            session['otprec'] = otp
            session['recvar'] = recvar
            session.pop("last_resend_time", None) 
            return render_template("recoveryotppage.html")
        else:
            flash("Account not found. Please check for any typo mistakes", "error")
            return render_template("recovery.html")
    return render_template("recovery.html")
@app.route("/recresend", methods=['GET'])
def recresend():
    recvar = session.get("recvar")
    if not recvar:
        flash("Session expired. Please register a request again.", "error")
        return redirect(url_for('recovery'))
    now = datetime.now()
    last_resend = session.get("last_resend_time")
    if last_resend:
        last_time = datetime.strptime(last_resend, "%Y-%m-%d %H:%M:%S")
        if now - last_time < timedelta(minutes=2):
            wait_seconds = 120 - int((now - last_time).total_seconds())
            flash(f"Please wait {wait_seconds} seconds before resending OTP.", "warning")
            return render_template("recoveryotppage.html")

    query = {"email": recvar} if "@" in recvar else {"username": recvar}
    user = users.find_one(query)
    if user:
        otp = send_otp(user['email'], user['eventname'], user['name'], "recotp.html")
        session["otprec"] = otp
        session["last_resend_time"] = now.strftime("%Y-%m-%d %H:%M:%S")
        flash("OTP has been resent successfully.", "success")
    else:
        flash("User not found. Please try recovery again.", "error")
        return redirect(url_for('recovery'))
    return render_template("recoveryotppage.html")
@app.route('/reverify', methods=['POST'])
def verify_recovery():
    entered_otp = request.form.get("otp")
    session_otp = session.get("otprec")
    recvar = session.get("recvar")
    if not (entered_otp and session_otp and recvar):
        flash("Session expired or invalid access.", "error")
        return redirect(url_for('recovery'))
    if entered_otp == session_otp:
        return render_template("reset_password.html")
    else:
        flash("Invalid OTP. Please try again.", "error")
        return render_template("recoveryotppage.html")
@app.route("/reset-password", methods=['POST'])
def reset_password():
    new_password = request.form.get("new_password")
    confirm_password = request.form.get("confirm_password")
    recvar = session.get("recvar")
    if not recvar:
        flash("Session expired. Please start recovery again.", "error")
        return redirect(url_for('recovery'))
    if (new_password != confirm_password):
        flash("Passwords do not match. Please try again.", "error")
        return render_template("reset_password.html")
    query = {"email": recvar} if "@" in recvar else {"username": recvar}
    update = {"$set": {"password": new_password}}
    result = users.update_one(query, update)
    if result.modified_count == 1:
        flash("Password updated successfully. Please login.", "success")
        session.pop("recvar", None)
        session.pop("otprec", None)
        return redirect(url_for('login'))
    else:
        flash("Password reset failed. Please try again.", "error")
        return render_template("reset_password.html")
@app.route("/register", methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        if 'formdata' in session and 'otp' in session:
            return render_template("otp.html")
        data = {
            'name': request.form.get("name"),
            'username': request.form.get("username"),
            'password': request.form.get("password"),
            'email': request.form.get("email"),
            'subevents': request.form.get("subevents", 'Nothing'),
            'eligibity': request.form.get("eligibity"),
            'eventname': request.form.get("eventname"),
            'eventdate': request.form.get("eventdate"),
            'eventtype': request.form.get("eventtype"),
            'eventsize': request.form.get("eventsize"),
            'location': request.form.get("location")
        }
        user = users.find_one({'username': data['username']})
        if(user):
            return jsonify({"status": "error", "message": "Username already exists."})
        otp = send_otp(data['email'], data['eventname'], data['name'],"otpverify.html")
        session['formdata'] = data
        session['otp'] = otp
        otp_html = render_template("otp.html")
        return jsonify({"status": "success", "html": otp_html})
    return render_template("register.html")
@app.route("/verify-otp",methods=['POST'])
def otpverfication():
    rotp=request.form.get("otp")
    if(rotp==session['otp']):
        users.insert_one(session['formdata'])
        session.pop("formdata",None)
        session.pop("otp",None)
        return redirect(url_for("login"))
    flash("Incorrect OTP")
    return render_template("otp.html")
@app.route("/resend", methods=["GET"])
def resend():
    formdata = session.get("formdata")
    if not formdata:
        flash("Session expired. Please register again.")
        return redirect(url_for('register'))
    now = datetime.now()
    last_resend = session.get("last_resend_time")
    if last_resend:
        last_time = datetime.strptime(last_resend, "%Y-%m-%d %H:%M:%S")
        if now - last_time < timedelta(minutes=2):
            wait_seconds = 120 - int((now - last_time).total_seconds())
            flash(f"Please wait {wait_seconds} seconds before resending OTP.")
            return render_template("otp.html")
    email = formdata.get("email")
    eventname = formdata.get("eventname")
    name = formdata.get("name")
    otp = send_otp(email, eventname, name,'otpverify.html')
    session["otp"] = otp
    session["last_resend_time"] = now.strftime("%Y-%m-%d %H:%M:%S")
    flash("OTP has been resent successfully.")
    return render_template("otp.html")
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
@app.route("/requestform")
def requestform():
    eventname = session.get('eventname')
    if not eventname:
        return "Event not selected in session."
    requests_collection = db['requests']
    existing_entry = requests_collection.find_one({"eventname": eventname})
    if existing_entry:
        return "Data Already Filled and Form Created"
    else:
        return render_template("partials/requestform.html")
@app.route("/approvals")
def approvals():
    return render_template("partials/approve.html")
@app.route("/api/pending-approvals")
def get_pending_approvals():
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    event_name = session.get('eventname')
    if not event_name:
        return jsonify({"error": "Event context missing in session"}), 400
    pending = list(db['SelfRegistrations'].find(
        {'eventname': event_name},
        {'_id': 0} 
    ))
    return jsonify(pending)
@app.route("/approve", methods=["POST"])
def approve_participant():
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    rollno = data.get("rollno")
    txn = data.get("transaction_number")
    user = users.find_one({'username': session['username']})
    eventname = user['eventname']
    eventdb = db[eventname]

    p = db['SelfRegistrations'].find_one({"RollNo": rollno, "txn_number": txn})
    if not p:
        return jsonify({"error": "Participant not found."}), 404

    p["date"] = datetime.now()
    count = eventdb.count_documents({})
    p["Verification"] = f'GRIET{eventname}-{count + 1}'
    eventdb.insert_one(p)
    db['SelfRegistrations'].delete_one({"RollNo": rollno, "txn_number": txn})
    
    send_html_email(
        p['email'], p['name'], user['eventdate'], rollno,
        p['branch'], user['eventname'] + "-" + p.get('subevent', ''),
        p["Verification"]
    )

    return jsonify({"message": "Participant approved and moved to event database."})

@app.route("/reject", methods=["POST"])
def reject_participant():
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    rollno = data.get("rollno")
    txn = data.get("transaction_number")

    result = db['SelfRegistrations'].delete_one({"RollNo": rollno, "txn_number": txn})
    if result.deleted_count == 0:
        return jsonify({"error": "Participant not found."}), 404
    return jsonify({"message": "Participant rejected and removed from list."})
@app.route("/api/get-subevents")
def fetch_subevents_api(): 
    eventname = session.get("eventname")
    if not eventname:
        return jsonify({"subevents": []})
    event_doc = db.users.find_one({"eventname": eventname})
    subevents = []
    if event_doc:
        raw = event_doc.get("subevents", "")
        if isinstance(raw, str):
            subevents = [s.strip() for s in raw.split(",") if s.strip()]
        elif isinstance(raw, list):
            subevents = raw
    return jsonify({"subevents": subevents})
@app.route("/submit-request", methods=["POST"])
def submit_request():
    data = request.get_json()
    print("Received JSON:", data)  
    upi_id = data.get("upi_id")
    subevents = data.get("subevents", {})
    general_amount = data.get("general_amount", None)
    request_entry = {
        "eventname": session.get("eventname", "Unknown Event"),
        "upi_id": upi_id,
        "subevents": subevents,
        "general_amount": general_amount,
        "timestamp": datetime.now().isoformat()
    }
    db.requests.insert_one(request_entry)
    return jsonify({"message": "Request submitted successfully"})
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
@app.route("/pverify",methods=['GET','POST'])
def pverify():
    if request.method=='POST':
        vnum=request.form.get("verification_number",None)
        if(vnum):
            if "-" in vnum:
                code,num=vnum.split("-")
                eventname=code[5:]
                print(eventname)
                eventb=db[eventname]
                student=eventb.find_one({'Verification':vnum})
                if student:
                    return render_template("public-student-pass-verification.html", 
                                       student=student,
                                       name=student['name'],
                                       branch=student['branch'],
                                       event=eventname+student['subevents'],
                                       date=student['date'],
                                       roll=student['RollNo'],
                                       teamsize=student['teamsize'],
                                       amount=student['amount'])
                else:
                    return render_template("public-student-pass-verification.html",
                                        error="Invalid Verification Number")
            else:
                return render_template("public-student-pass-verification.html",
                        error="Please enter Verification Number/valid verification number")
    else:
        return render_template("public-student-pass-verification.html")
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
