# Preditor de Falha e Risco em Dispositivos de Rede

Projeto interdisciplinar de **Redes de Computadores**, **Estrutura de Dados II** e **Análise de Sistemas** (agosto a novembro de 2026), desenvolvido com a metodologia Scrum.

## Identificação

| Campo | Informação |
|---|---|
| **Grupo** | Grupo 4 |
| **Integrante** | Jonathan Ferreira Luna |
| **Turma** | [preencher] |
| **Professores** | Andréa Ono Sakai, Denise Braito de Souza e Luis Ricardo de Oliveira |
| **Período** | 17/08/2026 a 12/11/2026 |

Projeto conduzido individualmente, acumulando os papéis de Product Owner, Scrum Master e equipe de desenvolvimento.

## Objetivo

Desenvolver, de forma iterativa e incremental, uma aplicação que treina uma **árvore de decisão** a partir de um log histórico de rede e disponibiliza um **dashboard em tempo real** capaz de classificar dispositivos como **OK**, **RISCO** ou **FALHA**, combinando monitoramento real via ping com um modo de simulação de eventos.

## Descrição

- **Redes:** coleta métricas (latência, jitter e perda de pacotes) e gera o arquivo `log_rede.csv`.
- **Estrutura de Dados II:** gera dados sintéticos, treina a árvore de decisão, calcula a acurácia e constrói o dashboard.
- **Análise de Sistemas:** conduz requisitos, regras de negócio, Product Backlog e cerimônias Scrum.

**Contrato de dados:** `timestamp, ip, latencia_ms, perda_pacotes_pct, jitter_ms, status_real`

## Estrutura do repositório

```
.
├── README.md
├── memorando_de_decisao_grupo4.md
├── dados/          # log_rede.csv e dataset sintético
├── src/            # gerador sintético, modelo (árvore) e dashboard
├── docs/           # requisitos, regras de negócio, relatórios, casos de uso
└── scrum/          # backlogs, registros das cerimônias, evidências
```

## Tecnologias

Python, Pandas, scikit-learn (opcional), Streamlit/Flask, Cisco Packet Tracer, GitHub Projects.

## Como executar

```bash
pip install -r requirements.txt
# Instruções de execução serão adicionadas conforme o desenvolvimento
```

## Status

Em desenvolvimento. Apresentação final entre 10 e 12/11/2026.
