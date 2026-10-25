import importlib.util
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "pipeline/shared"))
from common import valid_ipv4, explicitly_public

path = ROOT / "pipeline/07_rotulagem/src/rotular.py"
spec = importlib.util.spec_from_file_location("rotular", path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def row(**kw):
    base = {"pacotes_enviados": 3, "pacotes_recebidos": 3, "latencia_ms": 10.0,
            "rtt_p95_ms": 20.0, "rtt_p99_ms": 30.0, "jitter_ms": 1.0, "jitter_p95_ms": 3.0}
    base.update(kw)
    return base

def test_ok(): assert mod.classificar(row()) == "OK"
def test_um_pacote_perdido_risco(): assert mod.classificar(row(pacotes_recebidos=2)) == "RISCO"
def test_dois_pacotes_perdidos_falha(): assert mod.classificar(row(pacotes_recebidos=1)) == "FALHA"
def test_latencia_p99_falha(): assert mod.classificar(row(latencia_ms=31.0)) == "FALHA"
def test_latencia_p95_risco(): assert mod.classificar(row(latencia_ms=21.0)) == "RISCO"
def test_jitter_alto_risco(): assert mod.classificar(row(jitter_ms=4.0)) == "RISCO"

def test_ipv4_global_aceito(): assert valid_ipv4("8.8.8.8") is True
def test_ipv4_privado_recusado(): assert valid_ipv4("192.168.1.1") is False
def test_ipv4_loopback_recusado(): assert valid_ipv4("127.0.0.1") is False
def test_ipv4_documentacao_recusado(): assert valid_ipv4("192.0.2.10") is False
def test_ipv6_recusado(): assert valid_ipv4("2001:4860:4860::8888") is False
def test_public_true_aceito(): assert explicitly_public({"is_public": True}) is True
def test_public_false_recusado(): assert explicitly_public({"is_public": False}) is False
def test_public_ausente_recusado(): assert explicitly_public({}) is False
