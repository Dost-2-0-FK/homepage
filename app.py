import random
import os
import string
from datetime import date
from typing import MutableSequence
from dotenv import load_dotenv
from flask import Flask, json, redirect, render_template, request, url_for
from threading import Lock
from src.mailer import Mailer
from src.user_manager import UManager

load_dotenv()
PORT = os.getenv("PORT")
CSV = "data/anmeldungen.csv"

MAIL_PRE = "Thanks for joining Dost 2.0 FK. Login to edit your data with this entry-code:" 
MAIL_POST = "Do not loose this code and under no circumstances share it with anybody else!" 
MAIL_END = "Sincerely,\nDost 2.0 FK Team!" 
MAIL_SUBJ = "Dost 2.0 FK Registration" 

MSG_UNKNOWN= "Entry-Code unknown!"
MSG_INVALID = "Entry-Code invalid!"
MSG_USED = "E-Mail already registered!"
MSG_CONFIRM = "We've sent you a login code via mail."
MSG_ERROR = "Unknown Error. We're sorry!"
MSG_DELETED = "we successfully deleted you from our system."
mail = Mailer()

umanger = UManager()

app = Flask(__name__)

@app.route("/")
def main(): 
    return render_template("index.html", msg=request.args.get("msg"))

@app.route("/entry/<key>")
def entry(key: str): 
    user = umanger.get_user(key)
    if user is None: 
        return redirect(url_for("main", msg=MSG_INVALID), code=303)
    return render_template("entry.html", user=user)

@app.route("/access", methods=["POST"])
def reservieren(): 
    access = request.form["access"]
    error_msg = ""
        
    if "@" in str(access):
        if umanger.email_exists(access): 
            error_msg = MSG_USED
        else: 
            key = __create_id()
            try:
                mail.send(
                    to_addr=access, 
                    subject=MAIL_SUBJ, 
                    text_body=f"{MAIL_PRE} {key}\n{MAIL_POST}\n\n{MAIL_END}",
                    html_body=None
                )
                umanger.add_user(access, key)
                error_msg=MSG_CONFIRM
            except Exception as err: 
                error_msg = f"{MSG_ERROR} ({repr(err)})"
    elif umanger.key_exists(access): 
        return redirect(f"/entry/{access}")
    else: 
        error_msg = MSG_INVALID
    return redirect(url_for("main", msg=error_msg), code=303)

@app.route("/entry/<key>/update/<field>", methods=["POST"])
def update_name(key: str, field: str): 
    user = umanger.get_user(key)
    if user is None: 
        return redirect(url_for("main", msg=MSG_UNKNOWN), code=303)
    user.update_field(field, request.form[field])
    umanger.save_user(user)
    return redirect(url_for("entry", key=key), code=303)

@app.route("/entry/<key>/delete-me/", methods=["POST"])
def delete_user(key: str): 
    user = umanger.get_user(key)
    if user is None: 
        return redirect(url_for("main", msg=MSG_UNKNOWN), code=303)
    umanger.delete_user(user)
    return redirect(url_for("main", msg=f"{key}, {MSG_DELETED}"), code=303)


def __create_id(): 
    def id_part(n): 
        return ''.join(
            random.choices(string.ascii_letters + string.digits, k=n)
        )
    return '-'.join([id_part(4) for _ in range(4)])

if __name__ == "__main__": 
    app.run(debug=True, port=PORT)
