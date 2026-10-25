# Preditor de Qualidade de Redes — pipeline com dados públicos do RIPE Atlas

**Grupo 4 · Projeto interdisciplinar · 2026**

Este repositório reorganiza o projeto principal para seguir o pipeline de referência da professora, mantendo as etapas de pesquisa/treinamento e o monitoramento local, mas **sem incluir a pasta `producao/`**. A coleta é feita diretamente pela API REST do RIPE Atlas. O pipeline não lê dados sintéticos para treinar e não fabrica resultados se faltarem medições.

## Garantias de origem e publicidade

O pipeline aplica validações para usar somente:

- Âncoras listadas pelo RIPE Atlas como públicas, ativas e não desativadas, com IPv4 globalmente roteável (sem endereços privados, reservados, loopback, documentação etc.).
- Medições recorrentes do tipo ping, IPv4, com `is_public=true` e destino correspondente ao IP público global da âncora escolhida.
- Sondas confirmadas na API de sondas como `is_public=true`, que não são âncoras e cujo último IPv4 conhecido é globalmente roteável.
- Resultados baixados do endpoint público de resultados com `public_only=true`, dentro da janela de tempo escolhida.

O script `validar_publicidade.py` verifica os CSVs e o fluxo bruto antes do baseline, da rotulagem e do treino. Se encontrar uma medição privada, IP não global, sonda sem publicidade confirmada ou uma linha sem rastreabilidade, interrompe o pipeline. A auditoria fica em `pipeline/08_treino/data/auditoria_publicidade.json`.

**Atenção:** as medições públicas existentes não são garantidas para todas as âncoras e todos os dias. O programa nunca completa as lacunas com dados sintéticos. A existência de um arquivo chamado `log_rede_ripe_atlas.csv` não é, por si só, prova de que o arquivo veio da API.

## O que muda em relação ao protótipo antigo

- `dataset_sintetico.csv` e `log_rede.csv` são legados do protótipo e **não entram no treinamento deste pipeline**.
- `log_rede_ripe_atlas.csv` também não é usado automaticamente: sua origem precisa ser verificada separadamente.
- Os resultados e as métricas no repositório da professora pertencem ao trabalho de referência, não ao Grupo 4.
- Os números deste projeto só devem ser citados depois de executar o pipeline e conferir `avaliacao_teste.json`.

## Etapas

1. `pipeline/01_anchors/`: seleciona 30 âncoras públicas IPv4 de países distintos, com uma no Brasil.
2. `pipeline/02_medicoes/`: procura medições públicas recorrentes de ping IPv4 para os IPs dessas âncoras.
3. `pipeline/03_sondas/`: verifica a publicidade das sondas e seleciona até cinco sondas públicas IPv4 por destino, conforme os participantes que a API disponibilizar.
4. `pipeline/04_fluxos/`: baixa resultados públicos do período e calcula latência média, perda de pacotes e jitter por par sonda–âncora.
5. `pipeline/05_periodos/`: separa duas janelas UTC consecutivas de sete dias: A (baseline) e B (rótulos/treino).
6. `pipeline/06_baseline/`: calcula percentis de referência por fluxo usando apenas o período A.
7. `pipeline/07_rotulagem/`: rotula medições de B como `OK`, `RISCO` ou `FALHA` e define o alvo da próxima observação.
8. `pipeline/08_treino/`: treina e avalia uma Random Forest com divisão temporal; grava métricas, matriz de confusão e modelo.
9. `9_monitoramento_dash/`: painel local que mostra o histórico baixado e as métricas gravadas. Não afirma ser tempo real quando a fonte é histórica.

A referência da professora apresenta 30 âncoras e 150 pares sonda–âncora (30 destinos × 5 origens). Este pipeline informa quando o histórico público consultável não chega a esse total; não completa a diferença com IDs falsos. A contagem efetiva fica registrada na auditoria.

## Requisitos

- Python 3.11 recomendado.
- Internet para consultar `https://atlas.ripe.net/api/v2/`.
- Leitura de âncoras, sondas, medições e resultados públicos não exige chave API.
- O pipeline padrão **não cria medições nem gasta créditos**.
- Criação de medições próprias é opcional, exige chave com permissão, pode consumir créditos e não gera dados retroativos.

## Como iniciar no Windows

Mais simples: dê dois cliques em `INICIAR_PIPELINE_WINDOWS.bat`. Ele cria o ambiente virtual, instala os requisitos e executa o pipeline. Requer Python 3.11.

Ou pelo PowerShell na raiz:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe executar_pipeline.py
```

O orquestrador respeita as dependências. Se a API não devolver dados públicos suficientes, a execução para na etapa correspondente; essa parada deve ser documentada, não contornada com linhas inventadas.

## Arquivos gerados

- `pipeline/01_anchors/data/ancoras.csv`: âncoras públicas IPv4 e respectivos países.
- `pipeline/02_medicoes/data/medicoes_publicas.csv`: medições recorrentes públicas encontradas.
- `pipeline/03_sondas/data/vinculos_sonda_ancora.csv`: vínculos de medições com sondas públicas/IPv4 global.
- `pipeline/04_fluxos/data/fluxo_bruto.csv.gz`: resultados públicos normalizados; mantido localmente, fora do versionamento por padrão.
- `pipeline/05_periodos/data/periodos.json`: datas UTC das janelas A/B.
- `pipeline/06_baseline/data/baseline_por_fluxo.csv`: percentis do baseline.
- `pipeline/07_rotulagem/data/dataset_rotulado.csv.gz`: dataset derivado e rotulado.
- `pipeline/08_treino/data/auditoria_publicidade.json`: auditoria das condições de publicidade.
- `pipeline/08_treino/data/avaliacao_teste.json`: métricas, classes e matriz de confusão do teste temporal.
- `pipeline/08_treino/data/modelos/modelo_random_forest.joblib`: modelo salvo quando o treino é concluído.

## Período de 14 dias

Por padrão, o pipeline define duas janelas consecutivas de sete dias contando para trás a partir do momento da execução: A = sete dias anteriores a B; B = sete dias mais recentes. A API precisa já ter resultados públicos nas datas. Iniciar uma medição hoje não cria dados do passado. Antes de apresentar, confira os timestamps reais do dataset e os limites em `periodos.json`.

## Criar medições próprias (opcional, não executar sem verificar créditos)

O arquivo `criar_medicoes_ripe_atlas.py` pode solicitar 30 medições recorrentes de ping IPv4 públicas, usando cinco sondas públicas conectadas com IPv4 global e as 30 âncoras. O script pede uma confirmação digitada além de `--confirmar-creditos` e programa encerramento automático após 14 dias. Ele começa a coletar no momento em que a API aceitar as medições; não completa o histórico anterior. Até o dia seguinte à criação, ainda não existirão 14 dias completos de coleta própria.

```powershell
$env:RIPE_ATLAS_API_KEY = "SUA_CHAVE_NO_TERMINAL_LOCAL"
.\.venv\Scripts\python.exe criar_medicoes_ripe_atlas.py --confirmar-creditos
```

Não cole a chave no chat, código, README ou GitHub. Não execute sem verificar saldo, permissão e autorização do responsável pela disciplina.

## Testes locais

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Os testes cobrem as regras de classe e bloqueiam endereços IPv4 privados/reservados e publicidade ausente. Eles não substituem uma execução bem-sucedida contra a API real.

## Referências técnicas

- [RIPE Atlas API — acesso anônimo a dados públicos](https://atlas.ripe.net/docs/apis/rest-api-manual/authentication/anonymous-access/)
- [RIPE Atlas API — âncoras](https://atlas.ripe.net/docs/apis/rest-api-reference/anchors/anchors_list/)
- [RIPE Atlas API — sondas](https://atlas.ripe.net/docs/apis/rest-api-reference/probes/probes_list/)
- [RIPE Atlas API — listar medições](https://atlas.ripe.net/docs/apis/rest-api-reference/measurements/measurements_list/)
- [RIPE Atlas API — resultados de medições](https://atlas.ripe.net/docs/apis/rest-api-reference/measurements/measurements_results/)
- [RIPE Atlas API — criação de medições e créditos](https://atlas.ripe.net/docs/apis/rest-api-manual/measurements/creating-measurements/)

## Limitações

A cobertura do histórico público varia por destino e por sonda. A seleção de 30 países e os 150 vínculos podem não ser alcançados por toda consulta. As métricas representam somente o período e as sondas observadas, e uma Random Forest acadêmica não substitui monitoramento profissional. Registre as lacunas relatadas no JSON de auditoria e de avaliação.
