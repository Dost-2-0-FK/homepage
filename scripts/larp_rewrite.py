import argparse
from email.message import EmailMessage
import smtplib 
import sys
from email import policy 
from email.parser import BytesParser 
from email.generator import BytesGenerator 
from email.utils import parseaddr
from typing import Dict

DEBUG_LOG = "/tmp/larp_rewrite.log"
DOMAIN = "@dost-2-0-fk.art"
MAP_PATH = "/etc/postfix/generic_collectives"

def load_real_to_alias() -> Dict[str, str]:
    """
    Returns dict: real_email -> alias_localpart (e.g. 'alex@gmail.com' -> 'hebel')
    based on your JSON structure.
    """
    with open(MAP_PATH, "r", encoding="utf-8") as f:
        lines = [line.rstrip() for line in f]
        mapping = {line.split("\t")[0]:line.split("\t")[1] for line in lines}
    return mapping

def parse_message(raw: bytes) -> EmailMessage: 
    return BytesParser(policy=policy.SMTP).parsebytes(raw) 

def msg_to_bytes(msg: EmailMessage) -> bytes: 
    from io import BytesIO 
    buf = BytesIO() 
    BytesGenerator(buf, policy=policy.SMTP).flatten(msg) 
    return buf.getvalue() 

def send_via_local_smtp(env_from: str, rcpt: str, msg_bytes: bytes): 
    with smtplib.SMTP("127.0.0.1", 10026) as s: 
        s.sendmail(env_from, [rcpt], msg_bytes)

def main(): 
    ap = argparse.ArgumentParser() 
    ap.add_argument("--sender", required=True)
    ap.add_argument("--recipient", required=True) 
    args = ap.parse_args() 

    envelope_sender = args.sender.strip("<>").strip()
    rcpt = args.recipient.strip() 

    # Parse message and rewrite from 
    raw = sys.stdin.buffer.read() 
    msg = parse_message(raw) 

    name, header_from_addr = parseaddr(msg.get("From", "")) 
    header_from_addr_l = header_from_addr.lower()

    with open(DEBUG_LOG, "a") as fp:
        fp.write(f"CALLED sender={envelope_sender!r} rcpt={rcpt!r} from_header={header_from_addr_l!r}\n")

    # Load mapping 
    try: 
        real_to_alias = load_real_to_alias()
    except Exception as e: 
        print(f"larp_rewrite: failed to load mapping: {e}", file=sys.stderr) 
        sys.stdout.buffer.write(sys.stdin.buffer.read()) 
        return 0 

    # sender already alias -> no rewrite (let postfix deliver as-is)
    if header_from_addr_l.endswith("@" + DOMAIN): 
        env_from = envelope_sender or header_from_addr or ""
        send_via_local_smtp(env_from, rcpt, raw)
        return 0

    # Look ip mapping real -> alias
    alias_addr = real_to_alias.get(header_from_addr_l)

    # unkown real sender -> no rewrite (let postfix deliver as-is)
    if not alias_addr: 
        env_from = envelope_sender or header_from_addr or ""
        send_via_local_smtp(env_from, rcpt, raw)
        return 0

    # Only rewrite if header_from matches or is blank; 
    # if MUAs forge something else, we still rewrite based on envelope_sender 
    if name: 
        msg["From"] = f"{name} <{alias_addr}>" 
    else: 
        msg["From"] = alias_addr 

    # Optional debug header
    msg.add_header("X-Dost-Rewritten-From", header_from_addr_l)

    out_bytes = msg_to_bytes(msg) 

    # Envelope sender also becomes alias (hide real address)
    env_from = alias_addr

    send_via_local_smtp(env_from, rcpt, out_bytes)
    return 0


if __name__ == "__main__": 
    sys.exit(main())
