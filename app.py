import random
import os
import string
from typing import List
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, url_for
from src.secretor import Abbr, SecretFileEntry, Secretor
from src.communicator import Comm, CommUser
from src.mailer import Mailer
from src.user_manager import UManager, User
from src.seafiler import Seafile

load_dotenv()
PORT = os.getenv("PORT")
CSV = "data/anmeldungen.csv"

REGISTRATION_MAIL_SUBJ = "Dost 2.0 FK Registration" 
RESEND_MAIL_SUBJ = "Dost 2.0 FK Entry Code" 

MAIL_HOST = "@dost-2-0-fk.art"

MSG_MISSING = "Enter e-mail adress to send your entry code to!"
MSG_EMAIL_UNKOWN = "E-mail unknown!"
MSG_UNKNOWN= "Entry-Code unknown!"
MSG_INVALID = "Entry-Code invalid!"
MSG_UNAUTHORIZED = "You have no right to be here!"
MSG_USED = "E-Mail already registered!"
MSG_CONFIRM = "We've sent you a login code via mail."
MSG_ERROR = "Unknown Error. We're sorry!"
MSG_DELETED = "we successfully deleted you from our system."
mail = Mailer()

comm = Comm()
if "SEAFILE_CSV" not in os.environ: 
    exit("Missing SEAFILE_CSV!")
seafiler = Seafile(os.getenv("USE_SEAFILE", "False") == "True")
umanger = UManager(seafiler)
secretor = Secretor()

SEAFILE_MAIL_DIR = os.getenv("SEAFILE_MAILS", "")


def __build_register_mail(key: str) -> str: 
    msg = (
        "Thanks for joining Dost 2.0 FK.\n\n"
        "Login to edit your data with this entry-code:\n\n"    
        f"    {key}\n\n"
        "Do not loose this code and under no circumstances share it with anybody else!\n\n"
        ".\n\n"
        "Sincerely,\n"
        "Dost 2.0 FK Team\n\n\n"
        "-----\n"
        "previous mails you might have missed:\n"
        "-----\n"
    )
    for name in seafiler.list_files(SEAFILE_MAIL_DIR): 
        mail_content = seafiler.download_data(f"{SEAFILE_MAIL_DIR}/{name}").text()
        msg += f"\n\n-----\nOn the {name[:-3]} we wrote: \n" + mail_content
    return msg

def __build_resend_mail(key: str) -> str: 
    return (
        "Forgot your code? Well, in the past this used to happen.\n\n"
        "Here is your entry code:\n\n"
        f"    {key}\n\n"
        "Do not loose this code and under no circumstances share it with anybody else!.\n\n"
        "Thanks for being part of Dost 2.0 FK.\n\n"
        "Sincerely,\n"
        "Dost 2.0 FK Team"
    )
        
def print_list(lst: List[str]) -> str: 
    if len(lst) == 0 or lst[0] == '': 
        return '---' 
    return str(lst)

def print_connections(connections: List[str]) -> str: 
    lst = []
    users = secretor.get_chars_by_key()
    for connection in connections: 
        if connection in users: 
            name, _ = users[connection]
            lst.append(name) 
        else:
            lst.append(connection) 
    return '; '.join(lst)

def get_user_from_key(key: str) -> CommUser|None: 
    user = umanger.get_user(key)
    if user is None: 
        return None
    comm_user = comm.get_user(user.email.lower())
    return comm_user

app = Flask(__name__)
app.jinja_env.globals.update(print_list=print_list)
app.jinja_env.globals.update(print_connections=print_connections)
app.jinja_env.globals.update(get_user_from_key=get_user_from_key)

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
        chars=secretor.get_chars_by_key(),
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
        chars=secretor.get_chars_by_key(),
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
        chars=secretor.get_chars_by_key(),
        is_editor= "chars" in me.collective or "orga" in me.collective
    )

@app.route("/secret/<key>/entry/update", methods=["POST"])
def secret_file_update_entry(key: str):
    connections = request.form.get("connections", "").split("; ")
    connections = secretor.replace_connection_names_with_keys(connections)
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
        connections=connections,
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

@app.route("/secret/entry/delete/<key>", methods=["POST"])
def secret_file_delete_entry(key: str):
    if secretor.delete_secret_file_entry(key):
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

    def handle_registration(access: str) -> str: 
        if umanger.email_exists(access): 
            return MSG_USED
        key = __create_id()
        try:
            mail.send(
                to_addr=access, 
                subject=REGISTRATION_MAIL_SUBJ, 
                text_body=__build_register_mail(key),
                html_body=None
            )
            umanger.add_user(access, key)
            return MSG_CONFIRM
        except Exception as err: 
            return f"{MSG_ERROR} ({repr(err)})"

    def handle_resend_key(access: str) -> str: 
        key = umanger.get_key_from_email(access)
        if key is not None:
            mail.send(
                to_addr=access, 
                subject=RESEND_MAIL_SUBJ, 
                text_body=__build_resend_mail(key),
                html_body=None
            )
            return MSG_CONFIRM
        else: 
            return MSG_EMAIL_UNKOWN
        
    if "@" in str(access):
        if "forgot_key" in request.form.keys(): 
            error_msg = handle_resend_key(access) 
        else: 
            error_msg = handle_registration(access) 
    elif umanger.key_exists(access): 
        return redirect(f"/entry/{access}")
    else: 
        error_msg = MSG_MISSING if "forgot_key" in request.form.keys() else MSG_INVALID
    return redirect(url_for("main", msg=error_msg), code=303)

@app.route("/entry/<key>/update/user", methods=["POST"])
def update_user(key: str): 
    user = umanger.get_user(key)
    if user is None: 
        return redirect(url_for("main", msg=MSG_UNKNOWN), code=303)
    if "name" in request.form.keys():
        user.update_field("name", request.form["name"])
    if "status" in request.form.keys():
        user.update_field("status", request.form["status"])
    if "arrival" in request.form.keys():
        user.update_field("arrival", request.form["arrival"])
    umanger.save_user(user)
    return redirect(url_for("entry", key=key), code=303)

@app.route("/entry/<key>/update/<field>", methods=["POST"])
def update_user_experience(key: str, field: str): 
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
    feedback_to = request.args.get("feedback_to", default="")
    content = request.form["content"]
    subject = request.form["subject"]
    if feedback_to: 
        subject = f"[Dost:fb/{feedback_to}] {subject}"
    me_mail = me + MAIL_HOST 
    to_mail = [to + MAIL_HOST]
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

    return redirect(url_for("secret_file_reviews", key=key), code=303)

def __create_id(): 
    def id_part(n): 
        return ''.join(
            random.choices(string.ascii_letters + string.digits, k=n)
        )
    return '-'.join([id_part(4) for _ in range(4)])

if __name__ == "__main__": 
    app.run(debug=True, port=PORT)
