# Caminho mais curto para preparar a entrega

## 1. Subir o código

Use o arquivo `SUBIR_NO_GITHUB.md` para copiar a estrutura para o seu repositório `preditor-falha-rede`. Não apague os arquivos antigos nesta primeira passagem.

## 2. Executar a coleta pública

No Windows, dê dois cliques em `INICIAR_PIPELINE_WINDOWS.bat`. A execução usa a API pública do RIPE Atlas; não usa Google Colab, ping simulado ou arquivos sintéticos para treinar.

## 3. Conferir o resultado

No fim, confira:

- `pipeline/08_treino/data/auditoria_publicidade.json`: precisa aprovar a publicidade de todos os alvos, sondas e medições realmente usados.
- `pipeline/08_treino/data/avaliacao_teste.json`: métricas e matriz de confusão calculadas com o dataset produzido.
- `pipeline/05_periodos/data/periodos.json`: datas UTC de A e B; confirme que o histórico público cobre a janela inteira.

Se a execução parar dizendo que não encontrou medições, sondas ou observações suficientes, não é um erro para esconder: é uma limitação real da fonte. O README explica a alternativa de iniciar medições públicas futuras, mas isso exige uma chave API e pode gastar créditos por até 14 dias. O script programa encerramento automático após esse prazo; mesmo assim, confira as medições no site do RIPE Atlas. Uma coleta nova não produzirá 14 dias completos até amanhã.

## 4. O que dizer à professora

Explique que os arquivos sintéticos e a coleta local via `icmplib` foram mantidos como protótipo antigo e não entram no treinamento novo. O pipeline atualizado seleciona apenas âncoras públicas com IPv4 global, medições de ping públicas e sondas com publicidade confirmada e IPv4 global conhecido. A auditoria registra os totais reais. Não declare que completou 14 dias se o relatório de períodos/dados não comprovar esse intervalo.
