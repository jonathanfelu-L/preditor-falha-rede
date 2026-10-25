from pathlib import Path
import sys, csv, time, ipaddress
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "pipeline/shared"))
from common import API, iter_pages, read_periods, parse_dt, to_unix, ensure_parent, explicitly_public, valid_ipv4

ANCHORS = ROOT / "pipeline/01_anchors/data/ancoras.csv"
OUT = ROOT / "pipeline/02_medicoes/data/medicoes_publicas.csv"

def overlaps_window(measurement, start_unix, stop_unix):
    started = parse_dt(measurement.get("start_time"))
    stopped = parse_dt(measurement.get("stop_time"))
    if started and started.timestamp() >= stop_unix:
        return False
    if stopped and stopped.timestamp() < start_unix:
        return False
    return True

def main():
    if not ANCHORS.exists():
        raise SystemExit("Execute primeiro a etapa 1: selecionar âncoras.")
    periods = read_periods()
    start = to_unix(periods["period_A"]["start"])
    stop = to_unix(periods["period_B"]["stop"])
    anchors = list(csv.DictReader(ANCHORS.open(encoding="utf-8-sig")))
    found = {}
    for i, anchor in enumerate(anchors, 1):
        ip = anchor["ip_v4"]
        if not valid_ipv4(ip) or anchor.get("is_public", "").lower() != "true":
            print(f"[{i}/{len(anchors)}] IGNORADA âncora sem confirmação de IP global/publicidade: {ip}")
            continue
        print(f"[{i}/{len(anchors)}] Buscando pings públicos IPv4 para {anchor['hostname']} ({ip})...")
        params = {
            "type": "ping", "af": 4, "is_public": "true", "is_oneoff": "false",
            "target_ip": ip, "page_size": 500,
        }
        try:
            # Paginação limitada e filtros no servidor; nunca inclui medições privadas.
            measurements = iter_pages(f"{API}/measurements/", params, max_pages=10)
            for measurement in measurements:
                if measurement.get("type") != "ping":
                    continue
                if not explicitly_public(measurement):
                    continue
                if measurement.get("is_oneoff") is True:
                    continue
                target_ip = measurement.get("target_ip")
                if not valid_ipv4(target_ip) or ipaddress.ip_address(target_ip) != ipaddress.ip_address(ip):
                    continue
                if not overlaps_window(measurement, start, stop):
                    continue
                mid = measurement.get("id")
                if not mid:
                    continue
                found[(int(mid), int(anchor["anchor_id"]))] = {
                    "measurement_id": int(mid), "anchor_id": int(anchor["anchor_id"]),
                    "anchor_hostname": anchor["hostname"], "target_ip": ip,
                    "country_code": anchor["country_code"], "start_time": measurement.get("start_time"),
                    "stop_time": measurement.get("stop_time"), "interval_s": measurement.get("interval"),
                    "probes_requested": measurement.get("probes_requested"), "is_public": True,
                    "public_ipv4_global": True, "description": measurement.get("description", ""),
                }
        except Exception as exc:
            print(f"  Aviso: consulta pública falhou para {ip}: {exc}")
        time.sleep(0.15)
    rows = sorted(found.values(), key=lambda x: (x["anchor_id"], x["measurement_id"]))
    ensure_parent(OUT)
    fields = ["measurement_id", "anchor_id", "anchor_hostname", "target_ip", "country_code", "start_time", "stop_time", "interval_s", "probes_requested", "is_public", "public_ipv4_global", "description"]
    with OUT.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Medições recorrentes públicas IPv4 elegíveis encontradas: {len(rows)}.")
    print(f"Arquivo: {OUT.relative_to(ROOT)}")
    missing = [a["ip_v4"] for a in anchors if not any(x["anchor_id"] == int(a["anchor_id"]) for x in rows)]
    if missing:
        print(f"ATENÇÃO: {len(missing)} âncoras não têm medição pública recorrente encontrada no período: {', '.join(missing[:8])}{'...' if len(missing)>8 else ''}.")
    if not rows:
        raise SystemExit("A API não encontrou medições recorrentes públicas para estas âncoras. Não foi criado dataset fictício; considere criar medições públicas próprias após conferir créditos e permissão.")

if __name__ == "__main__":
    main()
