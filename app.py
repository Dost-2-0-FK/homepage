import random
import os
import string
from datetime import date
from dotenv import load_dotenv
from flask import Flask, json, redirect, render_template, request, url_for
from threading import Lock
from src.mailer import Mailer
from src.user_manager import UManager

load_dotenv()
PORT = os.getenv("PORT")
CSV = "data/anmeldungen.csv"

MAIL_TEXT = "Thanks for joining Dost 2.0 FK. Login to edit you data with this entry-code: " 
MAIL_SUBJ = "Dost 2.0 FK Registration" 
mail = Mailer()

umanger = UManager()

app = Flask(__name__)

@app.route("/")
def main(): 
    return render_template("index.html", msg=request.args.get("msg"))

@app.route("/entry/<key>")
def entry(key: str): 
    user = umanger.get_user(key)
    return render_template("access.html", user=user)

@app.route("/access", methods=["POST"])
def reservieren(): 
    access = request.form["access"]
    error_msg = ""
        
    if "@" in str(access):
        if umanger.email_exists(access): 
            error_msg = "E-Mail already registered"
        else: 
            key = __create_id()
            try:
                mail.send(
                    to_addr=access, 
                    subject=MAIL_SUBJ, 
                    text_body=MAIL_TEXT + key,
                    html_body=None
                )
                umanger.add_user(access, key)
                error_msg="We've sent you a login code via mail"
            except Exception as err: 
                error_msg = f"Unkown Error. We're sorry! ({repr(err)})"
    elif umanger.key_exists(access): 
        return redirect(f"/entry/{access}")
    else: 
        error_msg = "Entry-Code invalid"
    return redirect(url_for("main", msg=error_msg), code=303)

@app.route("/entry/<key>/update/<field>", methods=["POST"])
def update_name(key: str, field: str): 
    user = umanger.get_user(key)
    if user is None: 
        return redirect("/") 
    user.update_field(field, request.form[field])
    umanger.save_user(user)
    return render_template("access.html", user=user)

def __create_id(): 
    def id_part(n): 
        return ''.join(
            random.choices(string.ascii_letters + string.digits, k=n)
        )
    return '-'.join([id_part(4) for _ in range(4)])

if __name__ == "__main__": 
    app.run(debug=True, port=PORT)
