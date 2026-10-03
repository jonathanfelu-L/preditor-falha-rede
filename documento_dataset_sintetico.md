# Documento — Gerador de Dataset Sintético

**Grupo:** 4
**Responsável:** Jonathan Ferreira Luna

## Objetivo

Criar um conjunto de dados artificial, seguindo o contrato de dados do projeto, para permitir o início do treinamento da árvore de decisão (Estrutura de Dados II) sem depender da coleta real de rede.

## Regras usadas para gerar cada classe

Os valores de `latencia_ms`, `perda_pacotes_pct` e `jitter_ms` foram sorteados dentro de faixas diferentes para cada classe, seguindo a regra de bom senso de que quanto maior a latência, a perda de pacotes e o jitter, pior a condição do dispositivo:

| Classe | Latência (ms) | Perda de pacotes (%) | Jitter (ms) |
|---|---|---|---|
| **OK** | 5 a 100 | 0 a 1,5 | 0 a 10 |
| **RISCO** | 100 a 300 | 2 a 14 | 10 a 40 |
| **FALHA** | 300 a 800 | 15 a 100 | 40 a 150 |

Essas faixas foram escolhidas para ficarem coerentes com os critérios de classificação definidos no memorando de decisão do projeto (perda de pacotes acima de 15% ou latência muito alta tende a FALHA; valores intermediários tendem a RISCO).

## Como foi gerado

- Foram geradas **150 linhas no total**, sendo **50 de cada classe** (OK, RISCO, FALHA), garantindo uma distribuição balanceada.
- Cada linha recebeu um `ip` sorteado entre 4 endereços fictícios (`10.0.0.1` a `10.0.0.4`), simulando 4 dispositivos monitorados.
- O `timestamp` de cada linha foi gerado sequencialmente, simulando medições ao longo do tempo.
- Ao final, as linhas foram embaralhadas, para não ficarem agrupadas por classe.

## Resultado

Arquivo `dataset_sintetico.csv`, com 150 linhas e as colunas do contrato de dados: `timestamp, ip, latencia_ms, perda_pacotes_pct, jitter_ms, status_real`.

Esse dataset será usado para o primeiro treinamento da árvore de decisão (Sprints 1 e 2). Na Sprint 5, o modelo será retreinado com o `log_rede.csv` real, e os resultados serão comparados.
