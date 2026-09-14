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
- Buscar um lote de candles de um par e intervalo escolhidos.
- Devolver uma tabela com corretora, par, intervalo e horário UTC, além de OHLCV.
- Continuar a execução quando uma consulta falha, mostrando qual fonte falhou.

**Estágio atual: coleta exploratória e padronização.** Os dados ficam na memória
durante a execução. Ainda não há banco de dados, histórico paginado, indicadores,
modelo treinado, previsões, backtest ou site. Os candles coletados podem incluir
um candle aberto e lacunas; essa amostra ainda não está pronta para treinamento.

## Arquivos e nomes

| Arquivo | Responsabilidade |
|---|---|
| `coleta.py` | Funções reutilizáveis; importar o arquivo não faz consultas |
| `main.py` | Configura um teste pequeno, chama as funções e mostra os resultados |
| `requirements.txt` | Dependências do ambiente |

| Nome | Significado |
|---|---|
| `id_corretora` | Texto que identifica o conector, como `kraken` |
| `corretora` | Objeto que sabe conversar com a API escolhida |
| `par` | Símbolo de um mercado, sem fixar o ativo ou a moeda no nome da variável |
| `intervalo` | Duração de cada candle, como `1h` |
| `quantidade` | Quantidade solicitada em uma chamada |
| `inicio_ms` | Início desejado em milissegundos UTC; omitido, usa o padrão da API |
| `mercados` | Catálogo de mercados, não o histórico de todos eles |
| `candles` | Lista recebida da API, dentro de `buscar_candles` |
| `tabela` | Dados organizados em um DataFrame do pandas |

`buscar_candles` devolve `tabela`. O chamador guarda esse retorno em sua própria
variável `tabela`. Os nomes são neutros e permanecem iguais para qualquer par.

## Como executar

Na pasta do projeto, usando PowerShell:

```powershell
# Apenas na preparação inicial do ambiente:
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt

# Para executar o teste de coleta:
.\venv\Scripts\python.exe main.py
```

As configurações ficam no início de `main.py`. O teste inicial consulta os
catálogos de Binance e Kraken e solicita cinco candles de BTC/USDT e ETH/USDT
em cada uma. São exemplos para exercitar mais de uma fonte e ativo; os mercados
e recursos efetivamente disponíveis são conferidos durante a consulta.

`listar_corretoras()` usa o catálogo local do CCXT. Estar nessa lista não garante
que a API esteja acessível ou que ofereça candles. `listar_mercados()` usa a
internet para consultar a API da corretora e mantém os tipos de mercado e o
estado de atividade fornecidos pela fonte. Estado desconhecido não é garantia
de atividade. Descobrir os mercados não significa baixar o histórico de todos.

Cada conector reutiliza seu controle de frequência de consultas. Quantidades,
intervalos, acesso e profundidade histórica dependem da corretora. Um lote pode
conter menos registros que o solicitado. O código não promete cobertura de 100%
dos mercados nem consulta todas as corretoras de uma vez.

## Caminho até o primeiro treinamento

1. **Histórico e armazenamento:** buscar períodos definidos em lotes, gravar em
   banco local e permitir retomar atualizações sem duplicar registros.
2. **Qualidade:** ordenar por fonte, par e horário; verificar duplicatas, lacunas
   e candles incompletos; distinguir dados ausentes de períodos sem negociações.
3. **Entradas e alvo:** calcular poucos indicadores com dados passados e definir
   a resposta. No piloto, alta no próximo candle pode ser `1`; queda ou empate,
   `0`. O último exemplo fica sem rótulo enquanto o próximo candle não fechar.
4. **Primeiro treinamento:** testar regressão logística ou Random Forest,
   comparando com uma regra simples e usando avaliação temporal walk-forward.
5. **Simulação:** definir quando seria possível executar cada decisão, incluir
   custos e slippage e registrar limitações do resultado.
6. **Expansão:** aumentar ativos e fontes, comparar modelos por ativo ou
   compartilhados e, depois, construir a plataforma web.

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
