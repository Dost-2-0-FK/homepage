import argparse
from email.message import EmailMessage
import sys
from email import policy 
from email.parser import BytesParser 
from email.generator import BytesGenerator 
from email.utils import parseaddr
from subprocess import Popen, PIPE
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
    msg = BytesParser(policy=policy.SMTP).parsebytes(raw) 
    return msg

def msg_to_bytes(msg: EmailMessage) -> bytes: 
    from io import BytesIO 
    buf = BytesIO() 
    BytesGenerator(buf, policy=policy.SMTP).flatten(msg) 
    return buf.getvalue() 

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
        p = Popen(["/usr/sbin/sendmail", "-oi", "-f", env_from, rcpt], stdin=PIPE)
        p.communicate(raw) 
        return p.returncode

    alias_addr = real_to_alias.get(header_from_addr_l)
    # unkown real sender -> no rewrite (let postfix deliver as-is)
    if not alias_addr: 
        env_from = envelope_sender or header_from_addr or ""
        p = Popen(["/usr/sbin/sendmail", "-oi", "-f", env_from, rcpt], stdin=PIPE)
        p.communicate(raw) 
        return p.returncode

    # Only rewrite if header_from matches or is blank; 
    # if MUAs forge something else, we still rewrite based on envelope_sender 
    if name: 
        msg["From"] = f"{name} <{alias_addr}>" 
    else: 
        msg["From"] = alias_addr 

    out_bytes = msg_to_bytes(msg) 

    p = Popen(["/usr/sbin/sendmail", "-oi", "-f", alias_addr, rcpt], stdin=PIPE)
    p.communicate(out_bytes) 
    return p.returncode

if __name__ == "__main__": 
    sys.exit(main())
