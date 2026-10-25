from pathlib import Path
import sys, csv, time, gzip
from datetime import datetime, timezone
import pandas as pd
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "pipeline/shared"))
from common import API, get_json, read_periods, to_unix, ensure_parent, valid_ipv4
MED = ROOT / "pipeline/02_medicoes/data/medicoes_publicas.csv"
LINK = ROOT / "pipeline/03_sondas/data/vinculos_sonda_ancora.csv"
OUT = ROOT / "pipeline/04_fluxos/data/fluxo_bruto.csv.gz"

def as_float(x):
    try:
        v=float(x)
        return v if v>=0 else None
    except (TypeError,ValueError): return None

def parse_result(obj):
    packet_results=obj.get("result") or []
    if not isinstance(packet_results,list): packet_results=[]
    rtts=[]
    for packet in packet_results:
        if isinstance(packet,dict):
            rtt=as_float(packet.get("rtt"))
            if rtt is not None: rtts.append(rtt)
    total=len(packet_results)
    received=len(rtts)
    latency=sum(rtts)/len(rtts) if rtts else None
    return {"latencia_ms":latency,"rtt_min_ms":min(rtts) if rtts else None,"rtt_max_ms":max(rtts) if rtts else None,"pacotes_enviados":total,"pacotes_recebidos":received,"perda_pacotes_pct":100.0*(total-received)/total if total else None,"ttl":as_float(obj.get("ttl"))}

def main():
    if not MED.exists() or not LINK.exists(): raise SystemExit("Execute as etapas 2 e 3 antes da coleta.")
    periods=read_periods(); start=to_unix(periods["period_A"]["start"]); stop=to_unix(periods["period_B"]["stop"])
    api_start=periods["period_A"]["start"]; api_stop=periods["period_B"]["stop"]
    measurements=list(csv.DictReader(MED.open(encoding="utf-8-sig")))
    links=list(csv.DictReader(LINK.open(encoding="utf-8-sig")))
    # Relaciona cada sonda somente às medições onde foi listada como participante.
    probes_by_measurement={}
    for link in links:
        if str(link.get("probe_is_public", "")).strip().lower() != "true":
            continue
        key=(int(link["anchor_id"]), int(link["measurement_id"]))
        probes_by_measurement.setdefault(key,set()).add(int(link["probe_id"]))
    rows=[]; failures=0
    for i,m in enumerate(measurements,1):
        mid=int(m["measurement_id"]); aid=int(m["anchor_id"]); probes=probes_by_measurement.get((aid,mid),set())
        if not probes or str(m.get("is_public", "")).strip().lower() != "true": continue
        if not valid_ipv4(m.get("target_ip")): continue
        # public_only=true é aplicado na API e os IDs são filtrados pela etapa 3.
        params={"start":api_start,"stop":api_stop,"probe_ids":",".join(map(str,sorted(probes))),"public_only":"true"}
        try:
            payload=get_json(f"{API}/measurements/{mid}/results/",params=params,timeout=90)
            if not isinstance(payload,list):
                print(f"Aviso: formato inesperado para medição {mid}; ignorada."); continue
            for obs in payload:
                if not isinstance(obs,dict) or obs.get("prb_id") is None or obs.get("timestamp") is None: continue
                try: pid=int(obs["prb_id"]); ts=int(obs["timestamp"])
                except (ValueError,TypeError): continue
                if pid not in probes or not (start <= ts < stop): continue
                stats=parse_result(obs)
                if stats["pacotes_enviados"] == 0:
                    continue  # sem resultados por pacote: não inferir perda de 100%
                rows.append({"timestamp":datetime.fromtimestamp(ts,tz=timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z"),"timestamp_unix":ts,"measurement_id":mid,"probe_id":pid,"anchor_id":aid,"target_ip":m["target_ip"],"country_code":m["country_code"],**stats})
        except Exception as e:
            failures+=1; print(f"Aviso: não foi possível baixar resultados da medição {mid}: {e}")
        if i%10==0: print(f"Processadas {i}/{len(measurements)} medições; observações até agora: {len(rows)}")
        time.sleep(0.12)
    if not rows:
        raise SystemExit("A API não devolveu resultados no período escolhido. Não foi criado dataset fictício. Confira o histórico público ou inicie medições próprias para a coleta futura.")
    df=pd.DataFrame(rows).drop_duplicates(subset=["timestamp_unix","probe_id","anchor_id"],keep="last")
    df=df.sort_values(["probe_id","anchor_id","timestamp_unix"])
    df["jitter_ms"]=df.groupby(["probe_id","anchor_id"])["latencia_ms"].diff().abs()
    # First observation in each flow has no previous RTT, so it remains missing.
    ensure_parent(OUT)
    df.to_csv(OUT,index=False,compression="gzip")
    print(f"Observações reais salvas: {len(df):,}. Medições com erro: {failures}.")
    print(f"Fluxos distintos: {df.groupby(['probe_id','anchor_id']).ngroups}; saída: {OUT.relative_to(ROOT)}")
    print("A coluna jitter_ms é a diferença absoluta entre latências médias de execuções consecutivas do mesmo fluxo.")

if __name__ == "__main__": main()
