from pathlib import Path
import json
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
raw=ROOT/"pipeline/04_fluxos/data/fluxo_bruto.csv.gz"
report=ROOT/"pipeline/08_treino/data/avaliacao_teste.json"
st.set_page_config(page_title="Preditor de Rede — Grupo 4",layout="wide")
st.title("Preditor de Falha/Risco em Redes")
st.caption("Painel acadêmico do histórico real baixado da API RIPE Atlas. Atualize a coleta antes de esperar dados mais recentes; esta tela não cria medições.")
if not raw.exists():
    st.warning("Ainda não existe arquivo de medições baixadas. Execute `python executar_pipeline.py` na raiz do projeto.")
    st.stop()
df=pd.read_csv(raw)
if df.empty:
    st.warning("O arquivo de medições está vazio. Confira as mensagens do pipeline.")
    st.stop()
df["data_utc"]=pd.to_datetime(df["timestamp"],utc=True,errors="coerce")
latest=df["data_utc"].max()
c1,c2,c3,c4=st.columns(4)
c1.metric("Observações reais",f"{len(df):,}")
c2.metric("Fluxos sonda–âncora",f"{df.groupby(['probe_id','anchor_id']).ngroups:,}")
c3.metric("Âncoras",f"{df['anchor_id'].nunique():,}")
c4.metric("Último dado UTC",latest.strftime("%Y-%m-%d %H:%M") if pd.notna(latest) else "Indisponível")
st.subheader("Últimas medições coletadas")
recent=df.sort_values("data_utc",ascending=False).head(100).copy()
st.dataframe(recent[["data_utc","probe_id","anchor_id","target_ip","latencia_ms","perda_pacotes_pct","jitter_ms"]],use_container_width=True,hide_index=True)
st.subheader("Latência ao longo do tempo — amostra mais recente")
flow_options=sorted(df.apply(lambda r:f"sonda {int(r.probe_id)} → âncora {int(r.anchor_id)}",axis=1).unique())
selected=st.selectbox("Fluxo",flow_options)
sel=df[df.apply(lambda r:f"sonda {int(r.probe_id)} → âncora {int(r.anchor_id)}"==selected,axis=1)].sort_values("data_utc").tail(200)
if not sel.empty:
    fig,ax=plt.subplots(); ax.plot(sel.data_utc,sel.latencia_ms,marker=".",linewidth=1); ax.set_xlabel("Data UTC");ax.set_ylabel("Latência média (ms)");fig.autofmt_xdate();st.pyplot(fig);plt.close(fig)
if report.exists():
    st.subheader("Avaliação do modelo gravada")
    d=json.loads(report.read_text(encoding="utf-8"))
    a,b,c=st.columns(3);a.metric("Acurácia teste",f"{d.get('acuracia',0):.3f}");b.metric("Macro-F1",f"{d.get('macro_f1',0):.3f}");c.metric("Macro-F1 persistência",f"{d.get('persistencia',{}).get('macro_f1',0):.3f}")
    st.write("Matriz de confusão: linhas = classe real; colunas = classe prevista; ordem OK, RISCO, FALHA.")
    st.dataframe(pd.DataFrame(d.get("matriz_confusao",{}).get("linhas_classe_real_colunas_classe_prevista",[]),index=["Real OK","Real RISCO","Real FALHA"],columns=["Previsto OK","Previsto RISCO","Previsto FALHA"]),use_container_width=True)
    st.caption(d.get("alerta","Confira o relatório antes de apresentar."))
else:
    st.info("O modelo ainda não foi treinado. Quando a etapa 8 concluir, esta página mostrará as métricas.")
