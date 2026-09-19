# market-ml-lab

Laboratório de aprendizado e pesquisa em Machine Learning aplicado a mercados.
O objetivo é construir uma plataforma com várias fontes, ativos e períodos,
modelos próprios e resultados avaliados com rigor.

O CCXT é o primeiro fornecedor de conectores. Fontes adicionais poderão ser
integradas para ampliar a cobertura de cripto, ações e commodities.
O projeto não faz recomendações de investimento nem executa operações.

## O que funciona agora

- Listar os identificadores de corretoras da versão instalada do CCXT.
- Criar um conector a partir do identificador escolhido.
- Consultar o catálogo de mercados de uma corretora pela API.
- Buscar históricos de candles de uma hora em lotes, com início e fim definidos.
- Devolver uma tabela com corretora, par, intervalo e horário UTC, além de OHLCV.
- Filtrar candles ainda abertos e limitar o histórico ao período solicitado.
- Reunir os lotes, remover horários repetidos e ordenar o histórico.
- Verificar identificação, cobertura temporal, duplicatas e coerência dos preços.
- Salvar um CSV de candles por corretora, par e intervalo após a validação.
- Calcular retorno de uma hora e distância relativa à média dos últimos 20 fechamentos.
- Continuar a execução quando uma consulta falha, mostrando qual fonte falhou.

**Estágio atual: coleta histórica, validação e primeiras features.** Os candles
são persistidos em CSV. As features são calculadas na memória e exibidas no
terminal; ainda não são gravadas nesses arquivos. Não há banco de dados,
atualização incremental, alvo de previsão, modelo treinado, backtest ou site.

## Arquivos e nomes

| Arquivo | Responsabilidade |
|---|---|
| `coleta.py` | Funções reutilizáveis; importar o arquivo não faz consultas |
| `validacao.py` | Verifica a qualidade de uma série de candles de uma hora |
| `preparacao.py` | Acrescenta as primeiras features a uma cópia da tabela |
| `main.py` | Configura a execução, coleta, valida, salva candles e mostra features |
| `requirements.txt` | Dependências do ambiente |

| Nome | Significado |
|---|---|
| `id_corretora` | Texto que identifica o conector, como `kraken` |
| `corretora` | Objeto que sabe conversar com a API escolhida |
| `par` | Símbolo de um mercado, sem fixar o ativo ou a moeda no nome da variável |
| `intervalo` | Duração de cada candle, como `1h` |
| `quantidade` | Quantidade solicitada em uma chamada |
| `inicio_ms` | Início desejado em milissegundos UTC; omitido, usa o padrão da API |
| `fim_ms` | Limite final do histórico em milissegundos UTC |
| `mercados` | Catálogo de mercados, não o histórico de todos eles |
| `candles` | Lista recebida da API, dentro de `buscar_candles` |
| `tabela` | Dados organizados em um DataFrame do pandas |
| `lotes` | Tabelas reunidas por `buscar_historico` durante a paginação |
| `dados` | Cópia da tabela com as features acrescentadas |

`buscar_candles` devolve `tabela`. O chamador guarda esse retorno em sua própria
variável `tabela`. Os nomes são neutros e permanecem iguais para qualquer par.

## Como executar

Na pasta do projeto, usando PowerShell:

```powershell
# Apenas na preparação inicial do ambiente:
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt

# Para executar a coleta e a preparação:
.\venv\Scripts\python.exe main.py
```

As configurações ficam no início de `main.py`. A seleção atual é:

```python
CORRETORAS_ALVO = ["bybit"]
PARES_ALVO = ["BTC/BRL", "BTC/USDT"]
INTERVALO = "1h"
QUANTIDADE = 500
DATA_INICIO = "2026-08-01T00:00:00Z"
DATA_FIM = "2026-09-01T00:00:00Z"
```

`QUANTIDADE` é o limite solicitado por lote, não o total de candles nem a
quantidade de arquivos. O período inclui 1º de agosto às 00:00 e termina antes
de 1º de setembro às 00:00 UTC. Com cobertura completa, são 744 candles por par.
BTC/BRL e BTC/USDT são mercados distintos do mesmo ativo; USDT não é USD.

O programa gera `bybit_BTC_BRL_1h.csv` e `bybit_BTC_USDT_1h.csv` após validar o
histórico coletado. Executar o programa substitui arquivos de mesmo nome na
pasta atual do terminal, sem acumular execuções. Eles contêm identificação,
timestamp e OHLCV, sem as features. Execute na pasta do projeto para mantê-los ali.

`listar_corretoras()` usa o catálogo local do CCXT. Estar nessa lista não garante
que a API esteja acessível ou que ofereça candles. `listar_mercados()` usa a
internet para consultar a API da corretora e mantém os tipos de mercado e o
estado de atividade fornecidos pela fonte. Estado desconhecido não é garantia
de atividade. Descobrir os mercados não significa baixar o histórico de todos.

Cada conector reutiliza seu controle de frequência de consultas. Quantidades,
intervalos, acesso e profundidade histórica dependem da corretora. Um lote pode
conter menos registros que o solicitado. O código não promete cobertura de 100%
dos mercados nem consulta todas as corretoras de uma vez.

## Validação e features

`verificar_dados` compara os horários recebidos com todas as horas esperadas no
período, incluindo suas extremidades. O relatório conta horários inválidos,
faltantes, inesperados e duplicados; ordem incorreta; números ausentes ou não
finitos; preços não positivos ou incoerentes; e volumes negativos. Cada chamada
verifica apenas uma corretora, par e intervalo. Qualquer contagem diferente de
zero impede a gravação daquela consulta; um CSV anterior permanece no disco.

A validação examina a tabela final: duplicatas removidas na paginação não
aparecem no relatório. Um resultado sem problemas indica consistência segundo
essas regras, não uma confirmação independente dos preços fornecidos pela API.

| Feature | Cálculo | Significado |
|---|---|---|
| `retorno_1h` | fechamento atual / anterior - 1 | Variação relativa na última hora |
| `distancia_media20` | fechamento atual / média dos 20 últimos fechamentos - 1 | Posição relativa à média recente |

Um retorno de `0.02` representa 2%. O primeiro retorno e as primeiras 19
distâncias à média ficam ausentes por falta de histórico anterior. Esses valores
não são preenchidos com zero. A média inclui o candle da própria linha: as
features pressupõem uma previsão feita depois que esse candle fecha.

## Limites atuais

- O fluxo de histórico e validação aceita apenas `1h`. O filtro de fechamento
  em `buscar_candles` também usa uma hora, mesmo que a função receba outro intervalo.
- Uma fonte pode devolver um histórico parcial; a paginação não cria dados
  ausentes. A validação impede salvar séries incompletas para o período solicitado.
- A coleta usa o relógio local em UTC para filtrar candles abertos.
- As features pressupõem dados numéricos, ordenados e validados de uma única série.
- Os CSVs são substituídos, sem retomada ou atualização incremental.
- Um mês é uma amostra para verificar o funcionamento; não demonstra capacidade
  preditiva ou desempenho de uma estratégia.

## Caminho até o primeiro treinamento

1. **Entradas e alvo:** conferir e completar poucas features, definir o horizonte
   e construir a resposta. No piloto, alta no próximo fechamento pode ser `1`;
   queda ou empate, `0`. O último exemplo fica sem rótulo enquanto o próximo
   candle não fechar. Tratar separadamente esse caso e o início sem features.
2. **Base de treinamento:** ampliar o período histórico, validar a cobertura e
   persistir os dados preparados separadamente dos candles de origem.
3. **Primeiro treinamento:** testar regressão logística ou Random Forest,
   comparando com uma regra simples e usando avaliação temporal walk-forward.
4. **Simulação:** definir quando seria possível executar cada decisão, incluir
   custos e slippage e registrar limitações do resultado.
5. **Expansão:** permitir atualização incremental e armazenamento em banco,
   ampliar intervalos, ativos e fontes, comparar modelos e construir o site.

O primeiro treino depende de uma amostra histórica utilizável, não de coletar o
mundo inteiro. Uma meta de estudo é começar com alguns ativos e meses de candles
de uma hora, ajustando o recorte conforme a cobertura das fontes. A quantidade
de dados por si só não garante poder preditivo nem significância estatística.

## Princípios

- Features usam informações disponíveis no instante da previsão.
- Rótulos representam resultados posteriores; cada treinamento utiliza apenas
  exemplos cujos rótulos já seriam conhecidos na sua data de corte.
- Pré-processamento e escolha do modelo respeitam os conjuntos de treino,
  validação e teste, sem aprender com dados reservados para avaliação final.
- Desempenho precisa ser verificado por mercado e período; sucesso em um ativo
  não demonstra automaticamente sucesso nos demais.
- A coleta continua separada dos modelos, permitindo acrescentar outras fontes.
- Deep Learning será avaliado quando houver motivo e comparação com baselines.

## Licença

MIT — veja [LICENSE](./LICENSE).
