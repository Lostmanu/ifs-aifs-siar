"""Utilidades compartidas: rutas, recibos con SHA-256, peticiones acotadas."""
from pathlib import Path, PureWindowsPath
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from html.parser import HTMLParser
import hashlib, json, re, time, socket

CODE = Path(__file__).resolve().parent
BASE = CODE.parent                     # work/medicion_escala
ROOT = BASE.parent.parent              # qu
OUT = BASE / 'outputs'  # Paquete autónomo: todas las salidas quedan dentro de su raíz.
RAW = BASE / 'raw'
STATE = BASE / 'state'
DATOS = BASE / 'datos'
UA = 'MedicionEscala/1.0 (bounded non-commercial research)'


def ruta(valor):
    """Convierte una ruta GUARDADA COMO DATO en un Path del sistema actual.

    Los manifiestos escritos en Windows guardaban el separador '\\', que en POSIX no separa:
    Path('raw\\heredado\\x.json') seria un unico nombre de fichero. PureWindowsPath trata
    tanto '/' como '\\' como separador, asi que esto funciona en los dos sistemas y con
    manifiestos viejos y nuevos.
    """
    return Path(*PureWindowsPath(str(valor)).parts)


def now():
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(p):
    return sha256_bytes(Path(p).read_bytes())


def dump(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def spec():
    """Especificacion congelada. En el arbol de trabajo vive en OUT; en un paquete extraido, en BASE."""
    for p in (OUT / 'metodo_fijado.json', BASE / 'metodo_fijado.json'):
        if p.exists():
            return load(p)
    raise FileNotFoundError('no encuentro metodo_fijado.json ni en outputs/ ni en la raiz del paquete')


def log(path, msg):
    line = f'{now()} {msg}'
    print(line, flush=True)
    with open(path, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


class Hidden(HTMLParser):
    def __init__(self):
        super().__init__()
        self.fields = {}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'input' and a.get('type') == 'hidden' and a.get('name'):
            self.fields[a['name']] = a.get('value', '')


def redact_session(body):
    return re.sub(r'<(?:input|meta)\b[^>]*(?:csrf|CSRF)[^>]*>', '<!-- session field omitted -->', body.decode('utf-8')).encode()


def http(url, opener=None, fields=None, timeout=180):
    """Una petición. Devuelve (status, body, error). Nunca lanza por HTTP; sí registra."""
    data = urlencode(fields).encode() if fields is not None else None
    req = Request(url, data=data, headers={'User-Agent': UA})
    try:
        with (opener.open if opener else urlopen)(req, timeout=timeout) as r:
            body = r.read(30_000_001)
            if len(body) > 30_000_000:
                return None, b'', 'response exceeded 30 MB'
            return r.status, body, None
    except HTTPError as e:
        try:
            body = e.read()
        except Exception:
            body = b''
        return e.code, body, f'HTTP {e.code}'
    except (URLError, TimeoutError, socket.timeout, ConnectionError, OSError) as e:
        return None, b'', f'{type(e).__name__}: {e}'
    except Exception as e:  # p. ej. http.client.IncompleteRead, RemoteDisconnected
        partial = getattr(e, 'partial', b'')
        return None, partial if isinstance(partial, bytes) else b'', f'{type(e).__name__}: {str(e)[:120]}'


def fetch_with_receipt(url, path, opener=None, fields=None, redact=False, timeout=180, extra=None, fresh=False):
    """Descarga y guarda cuerpo + recibo. Si ya existe un recibo con status 200 y hash válido, reutiliza (salvo fresh).

    Devuelve el cuerpo ORIGINAL (sin redactar) para que el llamador pueda leer los campos de sesión;
    en disco se guarda la versión redactada cuando redact=True.
    """
    path = Path(path)
    receipt_path = path.with_name(path.name + '.receipt.json')
    clean = {k: v for k, v in (fields or {}).items() if 'csrf' not in k.lower()}
    if not fresh and path.exists() and receipt_path.exists():
        rec = load(receipt_path)
        if rec['url'] == url and rec.get('query_fields', {}) == clean and rec['status'] == 200 and sha256_file(path) == rec['saved_sha256']:
            return rec, path.read_bytes()
    started = now()
    status, body, error = http(url, opener, fields, timeout)
    saved = redact_session(body) if (redact and body) else body
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(saved)
    rec = {'url': url, 'method': 'POST' if fields is not None else 'GET', 'query_fields': clean, 'status': status, 'error': error,
           'requested_at_utc': started, 'received_at_utc': now(), 'timeout_seconds': timeout,
           'raw_sha256': sha256_bytes(body), 'saved_sha256': sha256_bytes(saved), 'bytes': len(saved), 'session_fields_redacted': bool(redact)}
    if extra:
        rec.update(extra)
    dump(receipt_path, rec)
    return rec, body
