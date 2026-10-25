from pathlib import Path
import sys, json, hashlib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, classification_report, confusion_matrix
from sklearn.dummy import DummyClassifier
from joblib import dump
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"pipeline/shared"))
from common import read_periods, ensure_parent, write_json
DATA=ROOT/"pipeline/07_rotulagem/data/dataset_rotulado.csv.gz"
OUT=ROOT/"pipeline/08_treino/data"
LABELS=["OK","RISCO","FALHA"]
FEATURES=["perda_pacotes_pct","latencia_ausente","latencia_ms","jitter_ms","rtt_sobre_p95","rtt_sobre_p99","rtt_amplitude_ms","ttl","latencia_media_3","latencia_max_3","latencia_media_6","latencia_max_6","latencia_media_12","latencia_max_12","perda_media_3","perda_max_3","perda_media_6","perda_max_6","perda_media_12","perda_max_12","perdas_consecutivas"]

def main():
    if not DATA.exists(): raise SystemExit("Execute primeiro a etapa 7.")
    df=pd.read_csv(DATA).sort_values("timestamp_unix").reset_index(drop=True)
    df=df.dropna(subset=FEATURES+["classe_proxima"])
    if len(df)<100: raise SystemExit(f"Só existem {len(df)} linhas elegíveis. O treino exige ao menos 100 para uma demonstração mínima; não foram criadas linhas sintéticas.")
    present=set(df["classe_proxima"].astype(str))
    if len(present)<2: raise SystemExit(f"Só há classe(s) {sorted(present)}; não é possível treinar/avaliar um classificador útil de três classes.")
    unique_ts=np.sort(df.timestamp_unix.unique())
    if len(unique_ts)<3: raise SystemExit("Não há timestamps distintos suficientes para divisão temporal.")
    split_ts=unique_ts[max(1,int(len(unique_ts)*0.8))]
    # Excluir do treino a linha cujo rótulo futuro cairia no teste.
    train=df[(df.timestamp_unix<split_ts)&(df.timestamp_proxima_unix<split_ts)]
    test=df[df.timestamp_unix>=split_ts]
    if train.empty or test.empty: raise SystemExit("A divisão temporal criou treino ou teste vazio.")
    X_train=train[FEATURES].astype(float); y_train=train["classe_proxima"].astype(str)
    X_test=test[FEATURES].astype(float); y_test=test["classe_proxima"].astype(str)
    model=RandomForestClassifier(n_estimators=200,min_samples_leaf=5,max_features="sqrt",random_state=42,n_jobs=-1,class_weight=None)
    model.fit(X_train,y_train); pred=model.predict(X_test)
    cm=confusion_matrix(y_test,pred,labels=LABELS)
    # Persistence is a simple baseline: repeat the current class for the next observation.
    persistence_pred=test["classe_atual"].astype(str)
    report={
      "fonte":"RIPE Atlas REST API (medições públicas); sem dados sintéticos no dataset do treino",
      "periodos_utc":read_periods(),
      "metodo_split":"temporal: primeiros 80% dos timestamps para treino, últimos 20% para teste; baseline calculado apenas em A",
      "linhas_dataset":int(len(df)),"linhas_treino":int(len(train)),"linhas_teste":int(len(test)),
      "timestamp_inicio_teste_utc":pd.to_datetime(int(test.timestamp_unix.min()),unit="s",utc=True).isoformat(),
      "timestamp_fim_teste_utc":pd.to_datetime(int(test.timestamp_unix.max()),unit="s",utc=True).isoformat(),
      "classes_realmente_presentes":sorted(present),"features":FEATURES,
      "random_forest":{"n_estimators":200,"min_samples_leaf":5,"max_features":"sqrt","random_state":42},
      "acuracia":float(accuracy_score(y_test,pred)),"balanced_accuracy":float(balanced_accuracy_score(y_test,pred)),"macro_f1":float(f1_score(y_test,pred,average="macro",labels=LABELS,zero_division=0)),
      "f1_por_classe":classification_report(y_test,pred,labels=LABELS,output_dict=True,zero_division=0),
      "matriz_confusao":{"ordem_classes":LABELS,"linhas_classe_real_colunas_classe_prevista":cm.tolist()},
      "persistencia":{"acuracia":float(accuracy_score(y_test,persistence_pred)),"macro_f1":float(f1_score(y_test,persistence_pred,average="macro",labels=LABELS,zero_division=0))},
      "alerta":"Métricas válidas apenas para as medições que a API devolveu. Confira o número de fluxos, a duração real e a distribuição de classes antes de usar na apresentação."
    }
    modeldir=OUT/"modelos"; ensure_parent(modeldir/"placeholder.txt")
    modelpath=modeldir/"modelo_random_forest.joblib"; dump(model,modelpath)
    report["hash_sha256_modelo"]=hashlib.sha256(modelpath.read_bytes()).hexdigest()
    write_json(OUT/"avaliacao_teste.json",report)
    (OUT/"MODEL_CARD.md").write_text("# Ficha do modelo — Random Forest\n\n- Fonte: resultados públicos da API RIPE Atlas.\n- Alvo: classe da próxima observação do mesmo par sonda–âncora.\n- Entradas: 21 características numéricas calculadas até a observação atual.\n- Divisão: temporal; o baseline é calculado apenas na janela A.\n- Arquivo de métricas: `avaliacao_teste.json`.\n- Arquivo do modelo: `modelos/modelo_random_forest.joblib`.\n- Limitação: os resultados só são válidos para o histórico que a API disponibilizou; não representam garantia de detecção em produção.\n\nConsulte o JSON de avaliação para números, datas e hash deste treino.\n",encoding="utf-8")
    print(f"Treino concluído com dados reais: treino={len(train):,}; teste={len(test):,}.")
    print(f"Acurácia={report['acuracia']:.3f}; macro-F1={report['macro_f1']:.3f}; baseline persistência macro-F1={report['persistencia']['macro_f1']:.3f}.")
    print(f"Métricas: {(OUT/'avaliacao_teste.json').relative_to(ROOT)}")
    print(f"Modelo: {modelpath.relative_to(ROOT)}")

if __name__=="__main__": main()
