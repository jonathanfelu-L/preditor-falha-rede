"""Audita, antes do treino, que todos os alvos/sondas/medições usados são públicos."""
from pathlib import Path
import sys, csv, gzip
from collections import defaultdict
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "pipeline/shared"))
from common import valid_ipv4, write_json, ensure_parent

ANCHORS = ROOT / "pipeline/01_anchors/data/ancoras.csv"
MEASUREMENTS = ROOT / "pipeline/02_medicoes/data/medicoes_publicas.csv"
LINKS = ROOT / "pipeline/03_sondas/data/vinculos_sonda_ancora.csv"
RAW = ROOT / "pipeline/04_fluxos/data/fluxo_bruto.csv.gz"
OUT = ROOT / "pipeline/08_treino/data/auditoria_publicidade.json"

def truth(value):
    return str(value).strip().lower() == "true"

def rows_csv(path):
    if not path.exists():
        raise SystemExit(f"Falta arquivo necessário para auditoria: {path.relative_to(ROOT)}")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))

def main():
    anchors = rows_csv(ANCHORS)
    measurements = rows_csv(MEASUREMENTS)
    links = rows_csv(LINKS)
    raw_rows = []
    if not RAW.exists():
        raise SystemExit("Falta fluxo_bruto.csv.gz; execute a etapa 4 antes da auditoria.")
    with gzip.open(RAW, "rt", encoding="utf-8-sig", newline="") as handle:
        raw_rows = list(csv.DictReader(handle))

    anchor_map = {int(a["anchor_id"]): a for a in anchors}
    errors = []
    warnings = []
    if len(anchors) != 30:
        warnings.append(f"Há {len(anchors)} âncoras; o modelo da referência mostra 30.")
    if len({a.get("country_code") for a in anchors}) != len(anchors):
        errors.append("Há país repetido na seleção de âncoras; deveria existir uma por país.")
    if sum(a.get("country_code") == "BR" for a in anchors) != 1:
        warnings.append("A seleção não contém exatamente uma âncora no Brasil.")
    for a in anchors:
        if not truth(a.get("is_public")) or not valid_ipv4(a.get("ip_v4")):
            errors.append(f"Âncora {a.get('anchor_id')} não tem publicidade/IP global confirmados.")

    measurement_map = {}
    for m in measurements:
        mid = int(m["measurement_id"])
        aid = int(m["anchor_id"])
        if not truth(m.get("is_public")) or not valid_ipv4(m.get("target_ip")):
            errors.append(f"Medição {mid} não passou na validação pública/IP global.")
            continue
        anchor = anchor_map.get(aid)
        if not anchor or anchor.get("ip_v4") != m.get("target_ip"):
            errors.append(f"Medição {mid} não corresponde ao IP da âncora {aid} selecionada.")
        measurement_map[mid] = m

    pairs = set()
    valid_link_measurement = set()
    for link in links:
        aid, pid, mid = int(link["anchor_id"]), int(link["probe_id"]), int(link["measurement_id"])
        if not truth(link.get("probe_is_public")) or not truth(link.get("probe_ipv4_global")):
            errors.append(f"Sonda {pid} não passou na validação pública/IPv4 global.")
        if not valid_ipv4(link.get("target_ip")):
            errors.append(f"Vínculo sonda {pid} → âncora {aid} usa alvo IPv4 não global.")
        if mid not in measurement_map or int(measurement_map[mid]["anchor_id"]) != aid:
            errors.append(f"Vínculo sonda {pid} → âncora {aid} aponta para medição ausente ou incompatível ({mid}).")
        pairs.add((aid, pid))
        valid_link_measurement.add((aid, pid, mid))
    if len(pairs) < 150:
        warnings.append(f"Existem {len(pairs)} pares públicos distintos; o modelo de referência mostra 150 (30 âncoras × 5 sondas). Não complete a diferença com IDs inventados.")

    raw_probe_ids = set()
    for row in raw_rows:
        try:
            aid = int(row["anchor_id"]); pid = int(row["probe_id"]); mid = int(row["measurement_id"])
        except (KeyError, TypeError, ValueError):
            errors.append("Há linha no fluxo bruto com IDs/timestamps inválidos.")
            continue
        raw_probe_ids.add(pid)
        if not valid_ipv4(row.get("target_ip")):
            errors.append(f"Observação da sonda {pid} usa alvo IPv4 não global.")
        if mid not in measurement_map or int(measurement_map[mid]["anchor_id"]) != aid:
            errors.append(f"Observação da sonda {pid} não corresponde a medição pública rastreada.")
        if (aid, pid, mid) not in valid_link_measurement:
            errors.append(f"Observação da sonda {pid} não corresponde a vínculo público rastreado.")

    report = {
        "fonte": "RIPE Atlas REST API; validação por flags is_public e endereços IPv4 globais",
        "publicidade_validada": len(errors) == 0,
        "erros": errors,
        "avisos": warnings,
        "contagens": {
            "ancoras": len(anchors),
            "paises_distintos": len({a.get("country_code") for a in anchors}),
            "medicoes_publicas": len(measurements),
            "pares_sonda_ancora_publicos_distintos": len(pairs),
            "linhas_vinculo_por_medicao": len(links),
            "observacoes_reais": len(raw_rows),
            "sondas_distintas": len(raw_probe_ids),
        },
        "regra": "Nenhuma medição privada, IP reservado/privado, sonda não pública ou amostra sintética pode entrar no treino.",
    }
    ensure_parent(OUT)
    write_json(OUT, report)
    print(f"Auditoria de publicidade: {'APROVADA' if report['publicidade_validada'] else 'REPROVADA'}")
    print(f"Âncoras: {len(anchors)} | medições públicas: {len(measurements)} | pares sonda–âncora: {len(pairs)} | observações: {len(raw_rows)}")
    for message in warnings:
        print("AVISO:", message)
    for message in errors[:30]:
        print("ERRO:", message)
    if errors:
        raise SystemExit(f"Auditoria reprovada; o pipeline não deve treinar. Relatório: {OUT.relative_to(ROOT)}")
    print(f"Relatório: {OUT.relative_to(ROOT)}")

if __name__ == "__main__":
    main()
