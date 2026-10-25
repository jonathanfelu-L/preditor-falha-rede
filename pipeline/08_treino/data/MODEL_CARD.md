# Ficha do modelo — Random Forest

- Fonte: resultados públicos da API RIPE Atlas.
- Alvo: classe da próxima observação do mesmo par sonda–âncora.
- Entradas: 21 características numéricas calculadas até a observação atual.
- Divisão: temporal; o baseline é calculado apenas na janela A.
- Arquivo de métricas: `avaliacao_teste.json`.
- Arquivo do modelo: `modelos/modelo_random_forest.joblib`.
- Limitação: os resultados só são válidos para o histórico que a API disponibilizou; não representam garantia de detecção em produção.

Consulte o JSON de avaliação para números, datas e hash deste treino.
