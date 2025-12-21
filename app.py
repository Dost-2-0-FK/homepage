import random
import os
import string
from typing import List
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, url_for
from src.secretor import Abbr, SecretFileEntry, Secretor
from src.communicator import Comm
from src.mailer import Mailer
from src.user_manager import UManager

load_dotenv()
PORT = os.getenv("PORT")
CSV = "data/anmeldungen.csv"

MAIL_PRE = "Thanks for joining Dost 2.0 FK. Login to edit your data with this entry-code:" 
MAIL_POST = "Do not loose this code and under no circumstances share it with anybody else!" 
MAIL_END = "Sincerely,\nDost 2.0 FK Team!" 
MAIL_SUBJ = "Dost 2.0 FK Registration" 

MAIL_HOST = "@dost-2-0-fk.art"

MSG_UNKNOWN= "Entry-Code unknown!"
MSG_INVALID = "Entry-Code invalid!"
MSG_UNAUTHORIZED = "You have no right to be here!"
MSG_USED = "E-Mail already registered!"
MSG_CONFIRM = "We've sent you a login code via mail."
MSG_ERROR = "Unknown Error. We're sorry!"
MSG_DELETED = "we successfully deleted you from our system."
mail = Mailer()

comm = Comm()
secretor = Secretor()
umanger = UManager()

def print_list(lst: List[str]) -> str: 
    if len(lst) == 0 or lst[0] == '': 
        return '---' 
    return str(lst)

app = Flask(__name__)
app.jinja_env.globals.update(print_list=print_list)

@app.route("/")
def main(): 
    return render_template("index.html", msg=request.args.get("msg"))

@app.route("/entry/<key>")
def entry(key: str): 
    user = umanger.get_user(key)
    if user is None: 
        return redirect(url_for("main", msg=MSG_INVALID), code=303)
    me = comm.get_user(user.email.lower())
    return render_template(
        "entry.html", 
        user=user, 
        msg=request.args.get("msg"),
        has_communicate=me is not None,
        is_editor= me is not None and ("chars" in me.collective or "orga" in me.collective)
    )

@app.route("/communicate/<key>")
def communicate(key: str): 
    user = umanger.get_user(key)
    if user is None: 
        return redirect(url_for("main", msg=MSG_INVALID), code=303)
    me = comm.get_user(user.email.lower())
    if me is None:
        return redirect(url_for("entry", key=key, msg=MSG_UNAUTHORIZED), code=303)
    return render_template(
        "communicate.html", 
        user=user, 
        has_communicate=comm.get_user(user.email.lower()) is not None,
        is_editor= "chars" in me.collective or "orga" in me.collective,
        collectives=comm.collectives,
        me=me
    )

@app.route("/secret/<key>")
def secret_file(key: str): 
    user = umanger.get_user(key)
    if user is None: 
        return redirect(url_for("main", msg=MSG_INVALID), code=303)
    me = comm.get_user(user.email.lower())
    if me is None:
        return redirect(url_for("entry", key=key, msg=MSG_UNAUTHORIZED), code=303)
    return render_template(
        "secret-file.html", 
        user=user, 
        has_communicate=comm.get_user(user.email.lower()) is not None,
        me=me,
        entries=secretor.secret_files(),
        gms=secretor.gms,
        cbis=secretor.cbis,
        is_editor= "chars" in me.collective or "orga" in me.collective
    )

@app.route("/secret/<key>/edit")
def secret_file_entries(key: str): 
    user = umanger.get_user(key)
    if user is None: 
        return redirect(url_for("main", msg=MSG_INVALID), code=303)
    me = comm.get_user(user.email.lower())
    if me is None:
        return redirect(url_for("entry", key=key, msg=MSG_UNAUTHORIZED), code=303)
    cur = secretor.get_secret_file_entry(request.args.get("entry-key", ""))
    print("CUR: ", cur)
    return render_template(
        "secret-file/edit.html", 
        user=user, 
        me=me,
        cur=cur,
        has_communicate=comm.get_user(user.email.lower()) is not None,
        entries=secretor.users_secret_file_entries(key),
        gms=secretor.gms,
        cbis=secretor.cbis,
        chars=secretor.get_chars(),
        is_editor= "chars" in me.collective or "orga" in me.collective
    )

@app.route("/secret/<key>/reviews")
def secret_file_reviews(key: str): 
    user = umanger.get_user(key)
    if user is None: 
        return redirect(url_for("main", msg=MSG_INVALID), code=303)
    me = comm.get_user(user.email.lower())
    if me is None:
        return redirect(url_for("entry", key=key, msg=MSG_UNAUTHORIZED), code=303)
    return render_template(
        "secret-file/review.html", 
        user=user, 
        has_communicate=comm.get_user(user.email.lower()) is not None,
        me=me,
        entries=secretor.secret_files_in_review(me.collective),
        gms=secretor.gms,
        cbis=secretor.cbis,
        is_editor= "chars" in me.collective or "orga" in me.collective
    )

@app.route("/secret/<key>/entry/update", methods=["POST"])
def secret_file_update_entry(key: str):
    print(request.form.to_dict(flat=False))
    entry = SecretFileEntry(
        key=request.form.get("key") if request.form.get("key", "") != "" else __create_id(),
        name=request.form.get("name", "---"),
        sirname=request.form.get("sirname", "---"),
        maidenname=request.form.get("maidenname", "---"),
        gender=request.form.get("gender", "???"),
        dob=request.form.get("dob", "???"),
        dob_zr=request.form.get("dob_zr", ""),
        zone=request.form.get("zone", "???"),
        genetic_augmentations=request.form.get("genetic_augmentations", "").split("; "),
        computer_brain_interfaces=request.form.get("computer_brain_interfaces", "").split("; "),
        violence_potential=int(request.form.get("violence_potential", "0")),
        estimated_wealth=int(request.form.get("estimated_wealth", "0")),
        crimes=request.form.get("crimes", "0").split("; "),
        employers=request.form.get("employers", "").split("; "),
        connections=request.form.get("connections", "").split("; "),
        illnesses=request.form.get("illnesses", "").split("; "),
        background=request.form.get("background", "").strip(),
        notes=request.form.get("notes", "").strip(),
        _creator=request.form.get("_creator", ""),
        _published=bool(request.form.get("_published", "")),
        _review=bool(request.form.get("_review", ""))
    )
    secretor.add_secret_file_entry(entry)
    return redirect(f"/secret/{key}/edit")

@app.route("/secret/entry/review/<key>", methods=["POST"])
def secret_file_review_entry(key: str):
    if secretor.review_secret_file_entry(key): 
        return "", 200 
    return "", 404

@app.route("/secret/add/<lst_name>/", methods=["POST"]) 
def add_lst_entry(lst_name: str): 
    lst = Abbr(
        abbr=request.form.get("abbr"),
        name=request.form.get("name"), 
        desc=request.form.get("desc").strip(),
        _creator=request.form.get("_creator") 
    )
    if lst_name == "gm":
        secretor.add_gm(lst)
    if lst_name == "cbi":
        secretor.add_cbi(lst)
    return "", 200

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

@app.route("/communicate/<key>/send/<me>/<to>", methods=["POST"]) 
def communicate_send(key: str, me: str, to: str): 
    content = request.form["content"]
    subject = request.form["subject"]
    me_mail = me + MAIL_HOST 
    to_mail = [to + MAIL_HOST]
    print(request.form)
    if to == "all":
        group = request.form["group"]
        if group == "users": 
            to_mail = umanger.all_mails()
        elif group == "collectives": 
            to_mail = comm.users.keys()
    for addr in to_mail: 
        print(f"{me} sends mail \"{subject}\" to {addr}: {content}")
        if mail.mode == "server":
            mail.send(
                to_addr=addr, 
                subject=subject, 
                text_body=content,
                html_body=None,
                from_addr=me_mail
            )

    return redirect(url_for("communicate", key=key), code=303)

def __create_id(): 
    def id_part(n): 
        return ''.join(
            random.choices(string.ascii_letters + string.digits, k=n)
        )
    return '-'.join([id_part(4) for _ in range(4)])

if __name__ == "__main__": 
    app.run(debug=True, port=PORT)
