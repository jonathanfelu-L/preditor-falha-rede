from pathlib import Path
import sys, csv
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "pipeline/shared"))
from common import API, iter_pages, ensure_parent, valid_ipv4, explicitly_public

OUT = ROOT / "pipeline/01_anchors/data/ancoras.csv"

def main():
    # O filtro is_public=true é aplicado no servidor do RIPE Atlas. Também rejeitamos
    # qualquer resposta que explicitamente diga que a âncora não é pública.
    params = {
        "page_size": 500,
        "is_public": "true",
        "is_active": "true",
        "is_disabled": "false",
        "is_decommissioned": "false",
        "include": "probe",
    }
    rows = list(iter_pages(f"{API}/anchors/", params, max_pages=20))
    eligible = []
    for anchor in rows:
        ip = anchor.get("ip_v4")
        country = (anchor.get("country") or anchor.get("country_code") or "").strip().upper()
        if not anchor.get("id") or not valid_ipv4(ip) or len(country) != 2 or country == "--":
            continue
        if "is_public" in anchor and not explicitly_public(anchor):
            continue
        probe_details = anchor.get("probe") if isinstance(anchor.get("probe"), dict) else {}
        if "is_public" in probe_details and not explicitly_public(probe_details):
            continue
        eligible.append({
            "anchor_id": int(anchor["id"]),
            "hostname": anchor.get("hostname") or anchor.get("fqdn") or "",
            "ip_v4": ip,
            "country_code": country,
            "city": anchor.get("city") or "",
            "probe_host_id": (probe_details.get("id") if probe_details else anchor.get("probe")),
            "is_public": True,  # confirmado pelo filtro is_public=true da API
            "public_ipv4_global": True,
            "is_active": anchor.get("is_active", True),
        })
    # Uma âncora por país; Brasil primeiro. Só endereços IPv4 globalmente roteáveis.
    by_country = {}
    for anchor in sorted(eligible, key=lambda x: (x["country_code"] != "BR", not bool(x["is_active"]), x["anchor_id"])):
        by_country.setdefault(anchor["country_code"], anchor)
    if "BR" not in by_country:
        raise SystemExit("A API pública não devolveu uma âncora IPv4 global elegível no Brasil. Não foram inventados dados.")
    selected = [by_country["BR"]] + [by_country[c] for c in sorted(by_country) if c != "BR"][:29]
    ensure_parent(OUT)
    fields = list(selected[0].keys()) if selected else ["anchor_id", "hostname", "ip_v4", "country_code", "city", "probe_host_id", "is_public", "public_ipv4_global", "is_active"]
    with OUT.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(selected)
    print(f"Âncoras listadas pela API como públicas, ativas e elegíveis: {len(eligible)}; países distintos: {len(by_country)}.")
    print(f"Arquivo: {OUT.relative_to(ROOT)}")
    print(f"Âncoras selecionadas: {len(selected)}; Brasil: {sum(x['country_code'] == 'BR' for x in selected)}.")
    if len(selected) < 30:
        raise SystemExit(f"Só existem {len(selected)} âncoras IPv4 públicas elegíveis em países distintos. Requisito do modelo: 30 (Brasil + 29 países). Não prossiga como se estivesse completo.")

if __name__ == "__main__":
    main()
