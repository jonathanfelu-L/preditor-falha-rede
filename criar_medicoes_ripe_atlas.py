"""Opcional: solicita medições públicas recorrentes no RIPE Atlas.
Pode consumir créditos. Só executa após chave local + confirmação digitada.
"""
from pathlib import Path
import argparse, csv, os, sys, time
from datetime import datetime, timedelta, timezone
import requests
ROOT = Path(__file__).resolve().parent
API = "https://atlas.ripe.net/api/v2"
sys.path.insert(0, str(ROOT / "pipeline/shared"))
from common import iter_pages, valid_ipv4, explicitly_public

def main():
    parser = argparse.ArgumentParser(description="Cria 30 medições de ping públicas IPv4, usando 5 sondas públicas.")
    parser.add_argument("--confirmar-creditos", action="store_true", help="Confirma que você verificou a conta, os créditos e a autorização.")
    args = parser.parse_args()
    if not args.confirmar_creditos:
        raise SystemExit("BLOQUEADO: leia o README, confirme os créditos e rode só com --confirmar-creditos se aceitar o custo.")
    key = os.environ.get("RIPE_ATLAS_API_KEY", "").strip()
    if not key:
        raise SystemExit("Defina RIPE_ATLAS_API_KEY no terminal local. Não coloque a chave no código, GitHub ou chat.")
    anchors_path = ROOT / "pipeline/01_anchors/data/ancoras.csv"
    if not anchors_path.exists():
        raise SystemExit("Execute antes a etapa 1 para selecionar âncoras públicas.")
    anchors = list(csv.DictReader(anchors_path.open(encoding="utf-8-sig")))
    if len(anchors) != 30:
        raise SystemExit(f"Esperadas 30 âncoras públicas; encontrei {len(anchors)}. Nada foi criado.")
    for anchor in anchors:
        if str(anchor.get("is_public", "")).lower() != "true" or not valid_ipv4(anchor.get("ip_v4")):
            raise SystemExit(f"Âncora não passou na validação pública: {anchor.get('anchor_id')}. Nada foi criado.")

    # Filtros da API garantem sondas públicas, conectadas e não-âncoras.
    params = {"is_public": "true", "status": 1, "is_anchor": "false", "page_size": 500}
    candidates = []
    for probe in iter_pages(f"{API}/probes/", params, max_pages=60):
        if not explicitly_public(probe) or probe.get("is_anchor") is not False:
            continue
        address = probe.get("address_v4")
        if not valid_ipv4(address):
            continue
        status = probe.get("status")
        status_id = status.get("id") if isinstance(status, dict) else status
        if status_id not in (1, "1") and probe.get("status_name") != "Connected":
            continue
        country = (probe.get("country_code") or "").upper()
        if len(country) != 2:
            continue
        candidates.append({"id": int(probe["id"]), "country_code": country, "address_v4": address})
    selected, used_countries = [], set()
    for probe in candidates:
        if probe["country_code"] not in used_countries:
            selected.append(probe)
            used_countries.add(probe["country_code"])
        if len(selected) == 5:
            break
    if len(selected) < 5:
        raise SystemExit(f"A API devolveu apenas {len(selected)} sondas conectadas, públicas e com IPv4 global em países distintos. Nada foi criado.")
    ids = ",".join(str(p["id"]) for p in selected)
    print("Sondas públicas e IPv4 globais escolhidas:")
    for probe in selected:
        print(f"  ID {probe['id']} — {probe['country_code']} — IPv4 público {probe['address_v4']}")
    print("Serão solicitadas 30 medições públicas de ping IPv4; cada uma tentará usar essas 5 sondas.")
    print("Configuração: 3 pacotes a cada 240 segundos. A coleta começa somente agora; não cria histórico retroativo.")
    print("Pode consumir créditos ao longo do tempo. Confirme o saldo e as regras da disciplina antes de continuar.")
    phrase = input("Para enviar os pedidos, digite CRIAR 30 MEDICOES PUBLICAS: ")
    if phrase != "CRIAR 30 MEDICOES PUBLICAS":
        raise SystemExit("Cancelado. Nenhuma medição foi solicitada.")

    out = []
    session = requests.Session()
    session.headers.update({"Authorization": f"Key {key}", "Content-Type": "application/json", "Accept": "application/json"})
    for i, anchor in enumerate(anchors, 1):
        payload = {
            "definitions": [{
                "target": anchor["ip_v4"],
                "description": f"Grupo 4 Preditor Redes — anchor {anchor['anchor_id']} — ping IPv4 público",
                "type": "ping", "af": 4, "is_public": True,
                "interval": 240, "packets": 3, "is_oneoff": False,
            }],
            "probes": [{"requested": 5, "type": "probes", "value": ids}],
            # Encerramento automático evita deixar as medições recorrentes cobrando indefinidamente.
            "stop_time": stop_at_iso,
        }
        response = session.post(f"{API}/measurements/", json=payload, timeout=60)
        if response.status_code >= 400:
            print(f"ERRO na âncora {anchor['anchor_id']}: HTTP {response.status_code}: {response.text[:300]}")
            raise SystemExit("Interrompido após erro. Confira na conta quais medições foram aceitas antes de tentar novamente.")
        body = response.json()
        mids = body.get("measurements", [])
        if not mids:
            raise SystemExit(f"A API não retornou IDs para a âncora {anchor['anchor_id']}; execução interrompida.")
        for mid in mids:
            # Confirma publicamente o objeto criado antes de registrá-lo como válido.
            meta_resp = session.get(f"{API}/measurements/{mid}/", timeout=45)
            if meta_resp.status_code >= 400:
                raise SystemExit(f"Medição {mid} criada, mas não foi possível verificar a publicidade. Verifique no site RIPE Atlas antes de prosseguir.")
            metadata = meta_resp.json()
            if not explicitly_public(metadata):
                raise SystemExit(f"Medição {mid} não foi confirmada como pública. Execução interrompida.")
            out.append({"measurement_id": mid, "anchor_id": anchor["anchor_id"], "target_ip": anchor["ip_v4"], "probe_ids": ids, "is_public": True, "stop_time_utc": stop_at_iso})
        print(f"Confirmadas {i}/30 âncoras: medição(ões) {mids} pública(s).")
        time.sleep(0.25)
    destination = ROOT / "pipeline/02_medicoes/data/medicoes_criadas_por_mim.csv"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(out[0].keys()))
        writer.writeheader()
        writer.writerows(out)
    print(f"IDs de medições públicas salvos em: {destination.relative_to(ROOT)}")
    print("Não compartilhe sua chave API. Ela não foi salva neste repositório.")

if __name__ == "__main__":
    main()
