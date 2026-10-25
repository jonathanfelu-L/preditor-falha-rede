from pathlib import Path
import sys
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"pipeline/shared"))
from common import read_periods, ensure_parent, to_unix
RAW=ROOT/"pipeline/04_fluxos/data/fluxo_bruto.csv.gz"
BASE=ROOT/"pipeline/06_baseline/data/baseline_por_fluxo.csv"
OUT=ROOT/"pipeline/07_rotulagem/data/dataset_rotulado.csv.gz"
FEATURES=[
 "perda_pacotes_pct","latencia_ausente","latencia_ms","jitter_ms","rtt_sobre_p95","rtt_sobre_p99","rtt_amplitude_ms","ttl",
 "latencia_media_3","latencia_max_3","latencia_media_6","latencia_max_6","latencia_media_12","latencia_max_12",
 "perda_media_3","perda_max_3","perda_media_6","perda_max_6","perda_media_12","perda_max_12","perdas_consecutivas"
]

def classificar(r):
    total=int(r.get("pacotes_enviados",3) or 3); rec=int(r.get("pacotes_recebidos",0) or 0); lost=max(total-rec,0)
    lat=r.get("latencia_ms"); p95=r.get("rtt_p95_ms"); p99=r.get("rtt_p99_ms"); jit=r.get("jitter_ms"); jp95=r.get("jitter_p95_ms")
    if lost>=2: return "FALHA"
    if pd.notna(lat) and pd.notna(p99) and lat>p99: return "FALHA"
    if lost>=1: return "RISCO"
    if pd.notna(lat) and pd.notna(p95) and lat>p95: return "RISCO"
    if pd.notna(jit) and pd.notna(jp95) and jit>jp95: return "RISCO"
    return "OK"

def main():
    if not RAW.exists() or not BASE.exists(): raise SystemExit("Execute as etapas 4 e 6 antes da rotulagem.")
    periods=read_periods(); b0=to_unix(periods["period_B"]["start"]); b1=to_unix(periods["period_B"]["stop"])
    df=pd.read_csv(RAW); base=pd.read_csv(BASE)
    df=df.merge(base,on=["probe_id","anchor_id"],how="inner",suffixes=("","_baseline"))
    df=df[(df.timestamp_unix>=b0)&(df.timestamp_unix<b1)].copy()
    if df.empty: raise SystemExit("Não há observações reais do período B com baseline válido.")
    df=df.sort_values(["probe_id","anchor_id","timestamp_unix"])
    df["classe_atual"]=df.apply(classificar,axis=1)
    # Impute missing RTT with median of that flow's baseline, with explicit missing indicator.
    df["latencia_ausente"]=df["latencia_ms"].isna().astype(int)
    df["latencia_ms"]=df["latencia_ms"].fillna(df["latencia_mediana_ms"])
    df["jitter_ms"]=df["jitter_ms"].fillna(0.0)
    df["rtt_amplitude_ms"]=(df["rtt_max_ms"].fillna(df["latencia_mediana_ms"])-df["rtt_min_ms"].fillna(df["latencia_mediana_ms"])).clip(lower=0)
    df["rtt_sobre_p95"]=np.where(df["rtt_p95_ms"].gt(0),df["latencia_ms"]/df["rtt_p95_ms"],0.0)
    df["rtt_sobre_p99"]=np.where(df["rtt_p99_ms"].gt(0),df["latencia_ms"]/df["rtt_p99_ms"],0.0)
    group=df.groupby(["probe_id","anchor_id"],sort=False,group_keys=False)
    for n in (3,6,12):
        df[f"latencia_media_{n}"]=group["latencia_ms"].transform(lambda s:s.rolling(n,min_periods=1).mean())
        df[f"latencia_max_{n}"]=group["latencia_ms"].transform(lambda s:s.rolling(n,min_periods=1).max())
        df[f"perda_media_{n}"]=group["perda_pacotes_pct"].transform(lambda s:s.rolling(n,min_periods=1).mean())
        df[f"perda_max_{n}"]=group["perda_pacotes_pct"].transform(lambda s:s.rolling(n,min_periods=1).max())
    def streak(series):
        vals=[]; k=0
        for v in series:
            k=k+1 if pd.notna(v) and v>0 else 0
            vals.append(k)
        return pd.Series(vals,index=series.index)
    df["perdas_consecutivas"]=group["perda_pacotes_pct"].transform(streak)
    flow_group=df.groupby(["probe_id","anchor_id"],sort=False)
    df["classe_proxima"]=flow_group["classe_atual"].shift(-1)
    df["timestamp_proxima_unix"]=flow_group["timestamp_unix"].shift(-1)
    df=df.dropna(subset=["classe_proxima","timestamp_proxima_unix"])
    if df.empty: raise SystemExit("Nenhuma sequência tem rótulo futuro; faltam observações consecutivas por fluxo.")
    keep=["timestamp","timestamp_unix","timestamp_proxima_unix","measurement_id","probe_id","anchor_id","target_ip","country_code","classe_atual","classe_proxima"]+FEATURES
    df=df[keep].replace([np.inf,-np.inf],np.nan)
    # Values used by the model must not have NaNs; source features are numeric only.
    df[FEATURES]=df[FEATURES].fillna(0.0)
    ensure_parent(OUT); df.to_csv(OUT,index=False,compression="gzip")
    print(f"Dataset real rotulado: {len(df):,} linhas; fluxos: {df.groupby(['probe_id','anchor_id']).ngroups}.")
    print(f"Distribuição de classes-alvo: {df.classe_proxima.value_counts().to_dict()}")
    print(f"Arquivo: {OUT.relative_to(ROOT)}")

if __name__=="__main__": main()
