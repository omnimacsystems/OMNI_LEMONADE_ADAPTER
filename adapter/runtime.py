"""Explicit loopback HTTP transport and read-only runtime preflight. No launch/download API."""
import hashlib
import json
import struct
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit
from .core import Hold


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise Hold("REDIRECT_FORBIDDEN")


class Client:
    def __init__(self, endpoint, model, fingerprint):
        u = urlsplit(endpoint)
        if (u.scheme != "http" or u.hostname != "127.0.0.1" or not u.port
                or u.username or u.password or u.query or u.fragment or u.path != "/v1"):
            raise Hold("EXPLICIT_LOOPBACK_ENDPOINT_REQUIRED")
        self.endpoint, self.model, self.fingerprint = endpoint, model, fingerprint
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def request(self, route, data=None, timeout=30):
        if route not in {"health", "tokenize", "completions"}:
            raise Hold("ENDPOINT_FORBIDDEN")
        payload = None if data is None else json.dumps(data, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(self.endpoint+"/"+route, payload, {"Content-Type":"application/json"})
        with self.opener.open(req, timeout=timeout) as response:
            raw = response.read(8*1024*1024+1)
            if len(raw) > 8*1024*1024:
                raise Hold("RESPONSE_TOO_LARGE")
            return json.loads(raw)


def gguf_template(path):
    """Read bounded GGUF metadata, never tensors or native code."""
    with Path(path).open("rb") as f:
        def number(fmt):
            b=f.read(struct.calcsize("<"+fmt))
            return struct.unpack("<"+fmt,b)[0]
        def string():
            n=number("Q")
            if n > 16*1024*1024:
                raise Hold("GGUF_METADATA_LIMIT")
            return f.read(n).decode("utf-8")
        def value(t):
            formats={0:"B",1:"b",2:"H",3:"h",4:"I",5:"i",6:"f",7:"?",10:"Q",11:"q",12:"d"}
            if t in formats:return number(formats[t])
            if t==8:return string()
            if t==9:
                subtype,n=number("I"),number("Q")
                if n>1000000:raise Hold("GGUF_METADATA_LIMIT")
                for _ in range(n):value(subtype)
                return None
            raise Hold("GGUF_UNKNOWN_TYPE")
        if f.read(4)!=b"GGUF" or number("I")!=3:raise Hold("GGUF_VERSION")
        number("Q")
        count=number("Q")
        if count>10000:raise Hold("GGUF_METADATA_LIMIT")
        template=None
        for _ in range(count):
            k=string();v=value(number("I"))
            if k=="tokenizer.chat_template":template=v
        if not isinstance(template,str):raise Hold("GGUF_TEMPLATE_MISSING")
        return template


def preflight(client, lock, lemonade_dir, backend_dir, model_path):
    roots={"lemonade":Path(lemonade_dir).resolve(), "backend":Path(backend_dir).resolve()}
    for item in lock["files"]:
        path=roots[item["root"]]/item["path"]
        if not path.resolve().is_relative_to(roots[item["root"]]) or file_hash(path)!=item["sha256"]:
            raise Hold("RUNTIME_FILE_HASH:"+item["path"])
    model_path=Path(model_path).resolve()
    if model_path.name!=lock["model_file"] or file_hash(model_path)!=lock["model_sha256"]:
        raise Hold("MODEL_HASH")
    template=gguf_template(model_path)
    if hashlib.sha256(template.encode()).hexdigest()!=lock["template_sha256"]:
        raise Hold("TEMPLATE_HASH")
    health=client.request("health")
    if health.get("version")!=lock["lemonade_version"]:raise Hold("LEMONADE_VERSION")
    loaded=health.get("all_models_loaded", [])
    if len(loaded)!=1:raise Hold("EXACTLY_ONE_MODEL_REQUIRED")
    m=loaded[0];cmd=m.get("launch_command",[])
    if (not m.get("backend_alive") or m.get("backend_health")!="ready"
            or m.get("model_name")!=lock["model_file"][:-5]
            or m.get("device")!="gpu" or m.get("recipe_options",{}).get("llamacpp_backend")!="cuda"
            or m.get("recipe_options",{}).get("ctx_size")!=4096
            or not cmd or Path(cmd[0]).resolve()!=roots["backend"]/"llama-server.exe"
            or Path(m["checkpoint"]).resolve()!=model_path):
        raise Hold("RUNTIME_IDENTITY")
    # Public proof deliberately omits machine-specific paths and process IDs.
    proof={"version":health["version"],"model":m["model_name"],"device":m["device"],
           "backend":"cuda","context_window":4096,"files_verified":len(lock["files"]),
           "model_sha256":lock["model_sha256"],"template_sha256":lock["template_sha256"],
           "trust_boundary":"Local operator-controlled loopback server; file/health checks are not remote attestation"}
    return template,proof
