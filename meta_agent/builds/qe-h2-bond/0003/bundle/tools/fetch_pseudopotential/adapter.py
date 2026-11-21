"""Fetch the hydrogen pseudopotential this agent's runs use, anonymously and read-only, and check it.

The file is PSLibrary 1.0.0's H.pbe-rrkjus_psl.1.0.0.UPF from pseudopotentials.quantum-espresso.org, a host the lab's
execution permission lists for reads of data. It is kept at runs/inputs/pseudo/ only when its bytes are the ones the
builder read (the content hash below, the builder's material card mat-20261120-pslibrary-h-pbe-rrkjus-upf); other
bytes are not kept and the call says so. A file already there with the right bytes is not fetched again.
"""
import hashlib
import os
import urllib.request

BUNDLE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NAME = "H.pbe-rrkjus_psl.1.0.0.UPF"
URL = "https://pseudopotentials.quantum-espresso.org/upf_files/" + NAME
SHA256 = "e03cd098d78e3eeb37cc9f790690f5827234cbc019fb621913391689a9ddacf7"
DEST = os.path.join(BUNDLE, "runs", "inputs", "pseudo")


def error(code, category, message, action, retryable=False, evidence=None):
    e = {"artifact": "error_contract", "schema_version": "0.1", "code": code, "category": category, "message": message,
         "retryable": retryable, "remediation": {"action": action}}
    if evidence is not None:
        e["evidence"] = evidence
    return e


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run(payload):
    target = os.path.join(DEST, NAME)
    rel = os.path.relpath(target, BUNDLE)
    if os.path.isfile(target):
        with open(target, "rb") as f:
            if digest(f.read()) == SHA256:
                return {"file": rel, "sha256": "sha256:" + SHA256, "fetched": False}
        return error("QE-PSEUDO-003", "invalid_input", "%s is there with bytes other than the ones the builder read" % rel,
                     "a person removes it or names why it differs; this agent writes no file over it")
    try:
        with urllib.request.urlopen(URL, timeout=120) as r:
            data = r.read()
    except OSError as e:
        return error("QE-PSEUDO-002", "unavailable", "the pseudopotential could not be read from %s: %s" % (URL, e),
                     "try again later; a network problem may pass on a retry", True)
    got = digest(data)
    if got != SHA256:
        return error("QE-PSEUDO-004", "execution_failure",
                     "the file read from %s is not the bytes the builder read (sha256 %s)" % (URL, got),
                     "nothing was kept; a person says whether the source changed", False, {"sha256": "sha256:" + got})
    os.makedirs(DEST, exist_ok=True)
    with open(target, "xb") as f:
        f.write(data)
    return {"file": rel, "sha256": "sha256:" + SHA256, "fetched": True}
