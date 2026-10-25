from __future__ import annotations
import json, time, ipaddress
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
import requests

API = "https://atlas.ripe.net/api/v2"
ROOT = Path(__file__).resolve().parents[2]
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "preditor-falha-rede-grupo4/1.1 (projeto academico)", "Accept": "application/json"})

class AtlasError(RuntimeError):
    pass

def get_json(url: str, params: dict[str, Any] | None = None, timeout: int = 45) -> Any:
    """GET com retentativas limitadas para erros transitórios da API."""
    last = None
    for attempt in range(4):
        try:
            response = SESSION.get(url, params=params, timeout=timeout)
            if response.status_code in (429, 500, 502, 503, 504):
                time.sleep(2 * (attempt + 1))
                continue
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as exc:
            last = exc
            if attempt < 3:
                time.sleep(1.5 * (attempt + 1))
    raise AtlasError(f"Falha ao consultar a API pública do RIPE Atlas ({url}). Detalhe: {last}")

def iter_pages(url: str, params: dict[str, Any] | None = None, max_pages: int = 100) -> Iterable[dict[str, Any]]:
    """Itera a paginação usando o link next da própria API."""
    next_url = url
    first = True
    pages = 0
    while next_url and pages < max_pages:
        data = get_json(next_url, params=params if first else None)
        first = False
        pages += 1
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    yield item
            break
        results = data.get("results", []) if isinstance(data, dict) else []
        for item in results:
            if isinstance(item, dict):
                yield item
        next_url = data.get("next") if isinstance(data, dict) else None

def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

def write_json(path: Path, obj: Any) -> None:
    ensure_parent(path)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")

def read_periods() -> dict[str, Any]:
    path = ROOT / "pipeline/05_periodos/data/periodos.json"
    if not path.exists():
        raise FileNotFoundError("Períodos não definidos. Execute pipeline/05_periodos/src/definir_periodos.py primeiro.")
    return json.loads(path.read_text(encoding="utf-8"))

def parse_dt(value: Any) -> datetime | None:
    if value in (None, "", 0):
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)
        except ValueError:
            try:
                return datetime.fromtimestamp(float(value), tz=timezone.utc)
            except (ValueError, OverflowError, OSError):
                return None
    return None

def to_unix(value: str) -> int:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())

def valid_ipv4(value: Any) -> bool:
    """True somente para IPv4 globalmente roteável (não privado/reservado)."""
    try:
        address = ipaddress.ip_address(str(value))
        return isinstance(address, ipaddress.IPv4Address) and address.is_global
    except ValueError:
        return False

def explicitly_public(obj: dict[str, Any]) -> bool:
    """Não presume publicidade se o campo estiver ausente ou tiver valor inesperado."""
    value = obj.get("is_public")
    return value is True or (isinstance(value, str) and value.strip().lower() == "true")

def fmt_dt(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
