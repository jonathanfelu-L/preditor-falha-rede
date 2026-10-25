from pathlib import Path
import subprocess, sys
ROOT=Path(__file__).resolve().parent
STEPS=[
 ("01 — âncoras", "pipeline/01_anchors/src/selecionar_ancoras.py"),
 ("05 — períodos A/B", "pipeline/05_periodos/src/definir_periodos.py"),
 ("02 — medições públicas", "pipeline/02_medicoes/src/descobrir_medicoes.py"),
 ("03 — sondas reais", "pipeline/03_sondas/src/listar_sondas.py"),
 ("04 — fluxos e métricas", "pipeline/04_fluxos/src/coletar_fluxos.py"),
 ("04B — auditoria de publicidade", "validar_publicidade.py"),
 ("06 — baseline", "pipeline/06_baseline/src/calcular_baseline.py"),
 ("07 — rotulagem", "pipeline/07_rotulagem/src/rotular.py"),
 ("08 — treino e avaliação", "pipeline/08_treino/src/treinar.py"),
]
def main():
    for name,script in STEPS:
        print("\n"+"="*68+f"\nETAPA {name}\n"+"="*68,flush=True)
        p=subprocess.run([sys.executable,str(ROOT/script)],cwd=ROOT)
        if p.returncode!=0:
            print(f"\nPipeline interrompido na etapa {name}. O código não criou dados artificiais para continuar.")
            raise SystemExit(p.returncode)
    print("\nTodas as etapas terminaram. Confira avaliação_teste.json e o README antes de apresentar.")
if __name__=="__main__": main()
