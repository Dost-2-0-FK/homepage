import argparse
from email.message import EmailMessage
import sys
from email import policy 
from email.parser import BytesParser 
from email.generator import BytesGenerator 
from email.utils import parseaddr
from subprocess import Popen, PIPE
from typing import Tuple 

DOMAIN = "@dost-2-0-fk.art"
MAP_PATH = "/etc/postfix/generic_collectives"

def load_real_to_alias():
    """
    Returns dict: real_email -> alias_localpart (e.g. 'alex@gmail.com' -> 'hebel')
    based on your JSON structure.
    """
    with open(MAP_PATH, "r", encoding="utf-8") as f:
        lines = [line.rstrip() for line in f]
        mapping = {line.split("\t")[0]:line.split("\t")[1] for line in lines}
    return mapping

def parse_message() -> Tuple[EmailMessage, bytes]: 
    raw = sys.stdin.buffer.read() 
    msg = BytesParser(policy=policy.SMTP).parsebytes(raw) 
    return msg, raw 

def msg_to_bytes(msg: EmailMessage) -> bytes: 
    from io import BytesIO 
    buf = BytesIO() 
    BytesGenerator(buf, policy=policy.SMTP).flatten(msg) 
    return buf.getvalue() 

def deliver_as_is() -> int: 
    _, raw = parse_message() 
    sys.stdout.buffer.write(raw) 
    return 0 

def main(): 
    ap = argparse.ArgumentParser() 
    ap.add_argument("--sender", required=True)
    ap.add_argument("--recipient", required=True) 
    args = ap.parse_args() 

    envelope_sender = args.sender or "" 
    envelope_sender = envelope_sender.strip("<>") 
    envelope_sender_l = envelope_sender.lower()

    rcpt = args.recipient.strip() 

    # Load mapping 
    try: 
        real_to_alias = load_real_to_alias()
    except Exception as e: 
        print(f"larp_rewrite: failed to load mapping: {e}", file=sys.stderr) 
        sys.stdout.buffer.write(sys.stdin.buffer.read()) 
        return 0 

    print(real_to_alias) 
    print(real_to_alias[envelope_sender_l])

    # sender already alias -> no rewrite (let postfix deliver as-is)
    if envelope_sender_l.endswith("@" + DOMAIN): 
        return deliver_as_is()

    alias_local = real_to_alias.get(envelope_sender_l)
    # unkown real sender -> no rewrite (let postfix deliver as-is)
    if not alias_local: 
        return deliver_as_is()

    # Parse message and rewrite from 
    msg, _ = parse_message() 
    from_header = msg.get("From", "") 
    name, _ = parseaddr(from_header) 

    # Only rewrite if header_from matches or is blank; 
    # if MUAs forge something else, we still rewrite based on envelope_sender 
    msg["From"] = alias_local if not name else f"{name} <{alias_local}>" 

    out_bytes = msg_to_bytes(msg) 

    p = Popen(["/usr/sbin/sendmail", "-oi", "-f", alias_local, rcpt], stdin=PIPE)
    p.communicate(out_bytes) 
    if p.returncode != 0: 
        print(f"larp_rewrite: sendmail failed with {p.returncode}", file=sys.stderr)
        # Tempfail, so mail can be retried: 
        return 75  # EX_TEMPFAIL 

    return 0


if __name__ == "__main__": 
    sys.exit(main())
