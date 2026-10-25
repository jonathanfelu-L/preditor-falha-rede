# Aplicar a entrega no repositório do projeto principal

Repositório: https://github.com/jonathanfelu-L/preditor-falha-rede

Esta entrega é uma reorganização do **pipeline principal** e não inclui `producao/`. Ela mantém os arquivos antigos para consulta, mas os scripts de treinamento não usam `dataset_sintetico.csv` nem `log_rede.csv`.

## Opção recomendada: Git no Windows

1. Baixe e extraia `preditor_rede_entrega.zip`.
2. Abra o PowerShell na pasta onde ficou a pasta `preditor_rede_entrega`.
3. Clone o repositório:

   ```powershell
   git clone https://github.com/jonathanfelu-L/preditor-falha-rede.git
   ```

4. Copie o conteúdo novo para dentro da cópia clonada (não use `/MIR`; assim os arquivos legados que não estão no pacote não são apagados):

   ```powershell
   robocopy .\preditor_rede_entrega .\preditor-falha-rede /E /XD __pycache__ .pytest_cache .venv /XF *.pyc
   ```

   Se o `robocopy` terminar com código 0 a 7, a cópia normalmente foi executada. Confira visualmente as pastas antes de seguir.

5. Entre no repositório e confira as mudanças:

   ```powershell
   cd .\preditor-falha-rede
   git status
   ```

6. Envie as mudanças:

   ```powershell
   git add .
   git commit -m "Reorganiza pipeline com dados publicos do RIPE Atlas"
   git push
   ```

   Se o Git solicitar autenticação, conclua pelo método oficial do GitHub. Não coloque token nem chave da API nos arquivos.

## Rodar o pipeline

Dentro da pasta clonada, dê dois cliques em `INICIAR_PIPELINE_WINDOWS.bat`, ou use:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe executar_pipeline.py
```

O pipeline padrão apenas lê a API pública. **Ele não cria medições e não consome créditos.** Se houver histórico público suficiente, ele cria os dados derivados e treina o modelo. Se não houver, para com um aviso em vez de fabricar linhas.

## Dados antigos

Não apague já `dataset_sintetico.csv`, `log_rede.csv` nem o notebook. Eles ficam como histórico do protótipo; o novo README explica que não podem ser usados como prova de coleta real. Só os arquivos derivados do pipeline novo podem servir ao treinamento relatado como real.

## Importante antes de entregar

- Abra `pipeline/08_treino/data/auditoria_publicidade.json`: tem de mostrar `publicidade_validada: true`.
- Abra `pipeline/08_treino/data/avaliacao_teste.json` e use apenas métricas produzidas nessa execução.
- O relatório de auditoria avisa se o número de âncoras ou vínculos públicos ficar abaixo do modelo de referência.
- Não afirme que já foram coletados 14 dias completos se as medições não cobrirem as datas exibidas em `pipeline/05_periodos/data/periodos.json`.
- `criar_medicoes_ripe_atlas.py` é opcional e separado. Só cria novas medições se você tiver uma API key local e confirmar conscientemente os créditos. Nunca envie sua chave para o chat ou para o GitHub.
