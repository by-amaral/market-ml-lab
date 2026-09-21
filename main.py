import ccxt

from coleta import buscar_historico, criar_corretora, listar_corretoras, listar_mercados
from validacao import verificar_dados
from preparacao import adicionar_features, adicionar_alvo
from treinamento import mostrar_resultados, salvar_resultados, treinar_avaliar

CORRETORAS_ALVO = ["bybit"]
PARES_ALVO = ["BTC/BRL", "BTC/USDT"]
INTERVALO = "1h"
QUANTIDADE = 500
DATA_INICIO = "2026-08-01T00:00:00Z"
DATA_FIM = "2026-09-01T00:00:00Z"
PAR_TREINAMENTO = "BTC/USDT"


def main():
    ids_corretoras = listar_corretoras()
    print(f"Conectores conhecidos pelo CCXT instalado: {len(ids_corretoras)}")
    print(", ".join(ids_corretoras))
    print("Nesta execução, consultaremos:", ", ".join(CORRETORAS_ALVO))

    consultas_com_dados = 0
    treinamentos_concluidos = 0
    falha_treinamento = False
    for id_corretora in CORRETORAS_ALVO:
        try:
            corretora = criar_corretora(id_corretora)
            mercados = listar_mercados(corretora)
        except (ccxt.BaseError, ValueError) as erro:
            print(f"Falha no catálogo de {id_corretora}: {erro}")
            continue

        print(f"\n{id_corretora}: {len(mercados)} mercados no catálogo do conector.")
        print(mercados.head(5).to_string(index=False))

        for par in PARES_ALVO:
            try:
                inicio_ms = corretora.parse8601(DATA_INICIO)
                fim_ms = corretora.parse8601(DATA_FIM)

                tabela = buscar_historico(
                    corretora,
                    par,
                    inicio_ms=inicio_ms,
                    fim_ms=fim_ms,
                    intervalo=INTERVALO,
                    quantidade=QUANTIDADE,
                )

                relatorio = verificar_dados(tabela, DATA_INICIO, DATA_FIM)
                print(f"Verificação de {id_corretora} / {par}: {relatorio}")

                if any(relatorio.values()):
                    print("Histórico com problemas. CSV não será salvo nesta consulta.")
                    continue

            except (ccxt.BaseError, ValueError) as erro:
                print(f"Falha ao consultar {id_corretora} / {par}: {erro}")
                continue

            print(f"\n{id_corretora} / {par}: {len(tabela)} candles recebidos.")
            if tabela.empty:
                print("A consulta não retornou candles.")
            else:
                consultas_com_dados += 1
                print("Primeiro candle:", tabela["timestamp"].min())
                print("Último candle:", tabela["timestamp"].max())
                caminho = f"{id_corretora}_{par.replace('/', '_')}_{INTERVALO}.csv"
                tabela.to_csv(caminho, index=False)
                print(f"Arquivo salvo: {caminho}")

                dados = adicionar_features(tabela)
                dados = adicionar_alvo(dados)
                print(
                    dados[["timestamp", "fechamento", "alvo_alta"]]
                    .tail(5)
                    .to_string(index=False)
                )

                if par == PAR_TREINAMENTO:
                    try:
                        resultado = treinar_avaliar(tabela, DATA_INICIO, DATA_FIM)
                        destino = salvar_resultados(resultado)
                    except (ValueError, OSError) as erro:
                        falha_treinamento = True
                        print(f"Falha no treinamento de {id_corretora} / {par}: {erro}")
                    else:
                        treinamentos_concluidos += 1
                        mostrar_resultados(resultado)
                        print(f"Resultados salvos em: {destino}")

    if consultas_com_dados == 0:
        print("Nenhum histórico válido foi salvo; confira as mensagens acima.")
        return 1
    if treinamentos_concluidos == 0:
        print(f"Nenhum treinamento concluído para {PAR_TREINAMENTO}.")
        return 1
    return 1 if falha_treinamento else 0


if __name__ == "__main__":
    raise SystemExit(main())
