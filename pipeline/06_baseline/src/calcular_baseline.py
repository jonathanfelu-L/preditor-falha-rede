from pathlib import Path
import sys
import pandas as pd
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT / "pipeline/shared"))
from common import read_periods, ensure_parent, to_unix
RAW=ROOT/"pipeline/04_fluxos/data/fluxo_bruto.csv.gz"
OUT=ROOT/"pipeline/06_baseline/data/baseline_por_fluxo.csv"

def main():
    if not RAW.exists(): raise SystemExit("Execute primeiro a etapa 4 para baixar as medições reais.")
    periods=read_periods(); a0=to_unix(periods["period_A"]["start"]); a1=to_unix(periods["period_A"]["stop"])
    df=pd.read_csv(RAW)
    df=df[(df.timestamp_unix>=a0)&(df.timestamp_unix<a1)].copy()
    if df.empty: raise SystemExit("Nenhuma observação real caiu no período A (baseline). Não é possível calcular percentis.")
    g=df.groupby(["probe_id","anchor_id"],dropna=False)
    out=g.agg(n_baseline=("timestamp_unix","count"), latencia_mediana_ms=("latencia_ms","median"), rtt_p95_ms=("latencia_ms",lambda s:s.quantile(.95)), rtt_p99_ms=("latencia_ms",lambda s:s.quantile(.99)), jitter_p95_ms=("jitter_ms",lambda s:s.quantile(.95))).reset_index()
    out=out[out.n_baseline>=10].copy()
    if out.empty: raise SystemExit("Nenhum fluxo teve 10 ou mais observações de baseline. Aumente a janela com dados reais; não invente dados.")
    ensure_parent(OUT); out.to_csv(OUT,index=False)
    print(f"Baselines válidos: {len(out)} fluxos de {g.ngroups} observados; saída: {OUT.relative_to(ROOT)}")

if __name__=="__main__": main()
