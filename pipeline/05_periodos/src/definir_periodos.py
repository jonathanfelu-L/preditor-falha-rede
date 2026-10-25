from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys, argparse
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "pipeline/shared"))
from common import fmt_dt, write_json
OUT = ROOT / "pipeline/05_periodos/data/periodos.json"

def main():
    ap = argparse.ArgumentParser(description="Define duas janelas históricas consecutivas de 7 dias (UTC).")
    ap.add_argument("--fim-utc", help="Fim ISO-8601 opcional; padrão: instante atual em UTC, para reprodução pode informar YYYY-MM-DDTHH:MM:SSZ")
    args = ap.parse_args()
    end = datetime.fromisoformat(args.fim_utc.replace("Z", "+00:00")) if args.fim_utc else datetime.now(timezone.utc)
    if end.tzinfo is None: end = end.replace(tzinfo=timezone.utc)
    end = end.astimezone(timezone.utc)
    mid = end - timedelta(days=7); start = end - timedelta(days=14)
    obj = {"timezone": "UTC", "created_at": fmt_dt(datetime.now(timezone.utc)), "period_A": {"start": fmt_dt(start), "stop": fmt_dt(mid), "purpose": "baseline; não entra no treino"}, "period_B": {"start": fmt_dt(mid), "stop": fmt_dt(end), "purpose": "dataset rotulado e treino"}, "window_days": 14, "note": "Intervalos [start, stop); o limite entre A e B não se sobrepõe. Os dados precisam já existir na API para o período histórico."}
    write_json(OUT, obj)
    print(f"Períodos salvos: {OUT.relative_to(ROOT)}")
    print(f"A (baseline): {obj['period_A']['start']} até {obj['period_A']['stop']}")
    print(f"B (dados):    {obj['period_B']['start']} até {obj['period_B']['stop']}")

if __name__ == "__main__": main()
