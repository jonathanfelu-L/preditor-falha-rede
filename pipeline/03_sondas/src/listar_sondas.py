from pathlib import Path
import sys, csv, time
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "pipeline/shared"))
from common import API, get_json, iter_pages, read_periods, to_unix, ensure_parent, explicitly_public

MED = ROOT / "pipeline/02_medicoes/data/medicoes_publicas.csv"
OUT = ROOT / "pipeline/03_sondas/data/vinculos_sonda_ancora.csv"

def _ids(obj):
    """Extrai IDs presentes nos campos de sondas que a API documenta."""
    found = set()
    for key in ("probes", "current_probes"):
        value = obj.get(key)
        if isinstance(value, list):
            for probe in value:
                raw = probe.get("id") if isinstance(probe, dict) else probe
                if raw is None and isinstance(probe, dict) and probe.get("url"):
                    raw = str(probe["url"]).rstrip("/").split("/")[-1]
                try:
                    found.add(int(raw))
                except (TypeError, ValueError):
                    continue
    return found

def main():
    if not MED.exists():
        raise SystemExit("Execute primeiro a etapa 2.")
    periods = read_periods()
    start = to_unix(periods["period_A"]["start"])
    stop = to_unix(periods["period_B"]["stop"])
    measurements = list(csv.DictReader(MED.open(encoding="utf-8-sig")))
    # Candidatos por medição, sem presumir que uma sonda participa de todas as medições.
    by_measurement = {}
    all_ids = set()
    for i, measurement in enumerate(measurements, 1):
        if str(measurement.get("is_public", "")).strip().lower() != "true":
            continue
        try:
            mid = int(measurement["measurement_id"])
            aid = int(measurement["anchor_id"])
            detail = get_json(f"{API}/measurements/{mid}/", params={"optional_fields": "probes,current_probes"})
            ids = _ids(detail) if isinstance(detail, dict) and explicitly_public(detail) else set()
            # Fallback correto: busca participantes que realmente aparecem em resultados
            # públicos dentro da janela. Não interpreta chaves de /latest/ como IDs.
            if not ids:
                results = get_json(
                    f"{API}/measurements/{mid}/results/",
                    params={"start": periods["period_A"]["start"], "stop": periods["period_B"]["stop"], "public_only": "true"}, timeout=90,
                )
                if isinstance(results, list):
                    for result in results:
                        try:
                            if isinstance(result, dict) and result.get("prb_id") is not None:
                                ids.add(int(result["prb_id"]))
                        except (ValueError, TypeError):
                            continue
            if ids:
                by_measurement[(aid, mid)] = ids
                all_ids.update(ids)
        except Exception as exc:
            print(f"Aviso na medição {measurement.get('measurement_id')}: {exc}")
        if i % 10 == 0:
            print(f"Verificadas {i}/{len(measurements)} medições públicas")
        time.sleep(0.10)

    if not all_ids:
        ensure_parent(OUT)
        with OUT.open("w", newline="", encoding="utf-8-sig") as handle:
            csv.writer(handle).writerow(["anchor_id", "anchor_hostname", "target_ip", "country_code", "probe_id", "measurement_id", "probe_is_public", "probe_ipv4_global"])
        raise SystemExit("Nenhuma sonda participante foi identificada nas medições públicas e na janela escolhida.")

    # Confirma publicidade individualmente pela API de sondas; consulta em lotes.
    public_probes = {}
    ids_sorted = sorted(all_ids)
    for offset in range(0, len(ids_sorted), 100):
        batch = ids_sorted[offset:offset + 100]
        for probe in iter_pages(f"{API}/probes/", {"id__in": ",".join(map(str, batch)), "is_public": "true", "page_size": 500}, max_pages=3):
            try:
                pid = int(probe["id"])
            except (KeyError, ValueError, TypeError):
                continue
            if pid not in batch or not explicitly_public(probe) or probe.get("is_anchor") is not False:
                continue
            # Para este projeto exigimos sonda pública, não-âncora, com IPv4 global conhecido.
            address = probe.get("address_v4")
            from common import valid_ipv4
            if not valid_ipv4(address):
                continue
            public_probes[pid] = probe

    anchor_by_id = {}
    anchor_path = ROOT / "pipeline/01_anchors/data/ancoras.csv"
    if anchor_path.exists():
        for anchor in csv.DictReader(anchor_path.open(encoding="utf-8-sig")):
            anchor_by_id[int(anchor["anchor_id"])] = anchor

    # Seleção determinística de até cinco sondas públicas NÃO-âncora por destino.
    ids_por_ancora = {}
    for (aid, mid), ids in by_measurement.items():
        ids_por_ancora.setdefault(aid, set()).update(ids.intersection(public_probes))
    selected_by_anchor = {aid: set(sorted(ids)[:5]) for aid, ids in ids_por_ancora.items()}

    rows = []
    for (aid, mid), ids in sorted(by_measurement.items()):
        selected = ids.intersection(public_probes).intersection(selected_by_anchor.get(aid, set()))
        anchor = anchor_by_id.get(aid, {})
        for pid in sorted(selected):
            rows.append({
                "anchor_id": aid,
                "anchor_hostname": anchor.get("hostname", ""),
                "target_ip": anchor.get("ip_v4", ""),
                "country_code": anchor.get("country_code", ""),
                "probe_id": pid,
                "measurement_id": mid,
                "probe_is_public": True,
                "probe_ipv4_global": True,
            })
    ensure_parent(OUT)
    fields = ["anchor_id", "anchor_hostname", "target_ip", "country_code", "probe_id", "measurement_id", "probe_is_public", "probe_ipv4_global"]
    with OUT.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    unique_pairs = {(r["anchor_id"], r["probe_id"]) for r in rows}
    anchors_seen = {aid for aid, _ in unique_pairs}
    print(f"Vínculos públicos distintos sonda–âncora: {len(unique_pairs)}; linhas por medição: {len(rows)}.")
    print(f"Âncoras com sonda pública observada: {len(anchors_seen)}; sondas públicas distintas: {len({pid for _, pid in unique_pairs})}.")
    print(f"Arquivo: {OUT.relative_to(ROOT)}")
    per_anchor = {aid: len(ids) for aid, ids in selected_by_anchor.items()}
    short = {aid: count for aid, count in per_anchor.items() if count < 5}
    if short:
        print(f"Atenção: {len(short)} âncoras têm menos de 5 sondas públicas elegíveis na API; total não completado artificialmente.")
    if len(unique_pairs) < 150:
        print("ATENÇÃO: o modelo de referência tem 150 vínculos (30 âncoras × 5 sondas). O requisito ainda não foi atingido com as medições públicas encontradas.")
    if not rows:
        raise SystemExit("Nenhuma combinação pública e verificável sonda–âncora foi encontrada.")

if __name__ == "__main__":
    main()
