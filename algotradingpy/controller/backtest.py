# -*- coding: utf-8 -*-
u"""
Description: Módulo com classes que para aplicar as estratégias de backtesting.
File name: backtest.py
Author: Daniel Tell <daniel.tell@gmail.com>
Date created: 02/10/2021
Date last modified: 24/10/2022
"""
import pandas as pd
import numpy as np
import algotradingpy.utils.indicators as indicators
import algotradingpy.view.console as console
from algotradingpy.model.setup import Setup
from algotradingpy.model.asset import Asset
from algotradingpy.model.signal import Signal
from algotradingpy.model.btresult import BacktestResult
import algotradingpy.utils.util as util
from datetime import datetime, timedelta
import json


class BackTest:

    asset: Asset = None
    __short_ema: pd.DataFrame = None
    __short_sma: pd.DataFrame = None
    __long_sma: pd.DataFrame = None
    __rsi: pd.Series = None
    signal: Signal = None
    bt_result: BacktestResult = None

    def __init__(self, asset: Asset, setup: Setup, days: int):

        self.setup = setup
        self.days = days
        self.asset = asset
        self.update()

    def get_symbol(self):
        return self.asset.symbol

    def get_time_frame(self):
        return self.asset.time_frame

    def get_strategy(self):
        return self.setup.get_strategy()

    def get_signal(self) -> Signal:
        return self.signal

    def get_last_update(self):
        if self.asset.last_update is None:
            return datetime.strptime("1970-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")  # se for None retorna epoch
        else:
            return self.asset.last_update

    def get_setup_update(self):
        if self.setup.last_update is None:
            return datetime.strptime("1970-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")  # se for None retorna epoch
        else:
            return self.setup.last_update

    def _get_start_date(self):
        index = self.asset.candles.head(1).index.strftime("%Y-%m-%d %H:%M:%S")[0]  # primeiro indice do DataFrame candles
        start_date = datetime.strptime(index, "%Y-%m-%d %H:%M:%S")
        return start_date.strftime("%Y-%m-%d")

    def _get_start_date_bt(self):
        index = self.asset.candles.tail(1).index.strftime("%Y-%m-%d %H:%M:%S")[0]  # último indice do DataFrame candles
        end_date = datetime.strptime(index, "%Y-%m-%d %H:%M:%S")
        start_date = end_date - timedelta(days=self.days)
        return start_date.strftime("%Y-%m-%d")

    def _get_end_date(self):
        index = self.asset.candles.tail(1).index.strftime("%Y-%m-%d %H:%M:%S")[0]
        end_date = datetime.strptime(index, "%Y-%m-%d %H:%M:%S")
        return end_date.strftime("%Y-%m-%d")

    def get_rsi_series(self):
        return self.__rsi

    def get_short_ema(self):
        return self.__short_ema

    def get_long_sma(self):
        return self.__long_sma

    def update(self):
        r"""Atualiza as médias móveis/rsi e executa um backtest atualizando o atributo signal e o atributo 'returns'
        de setup.
        :param Asset asset:
        :return: True se o backtest foi atualizado, ou seja, asset possui dados novos, caso contrario retorna False.
        :rtype: bool
        """
        if self.asset is None:
            return False

        if self.asset.updated:
            self.asset.updated = False

            if self.setup.get_strategy().startswith("RSI"):
                self._update_rsi(self._get_start_date(), self._get_end_date())
            else:
                self._update_moving_averages()

            bt_result = self.run(self._get_start_date_bt(), self._get_end_date())
            if bt_result is not None:
                self.bt_result = bt_result
                self.setup.set_parameters(returns=bt_result.get_trade_returns(), accuracy=bt_result.get_accuracy(),
                                          start_date=self._get_start_date_bt(), end_date=self._get_end_date())
                if self.signal is None:
                    self.signal = bt_result.get_signal()
                else:
                    list_signals = bt_result.get_signal().get_signals()
                    for sig in list_signals:
                        self.signal.insert_signal(sig["date"], sig["price"], sig["action"], sig["strategy"], sig["obs"],
                                                  sig["rsi"])
            return True
        else:
            return False

    def _update_moving_averages(self):
        r"""Atualiza as médias móveis"""
        try:
            self.__short_ema = indicators.calc_ema(self.asset.candles, self.setup.short)
            self.__short_sma = indicators.calc_sma(self.asset.candles, self.setup.short)
            self.__long_sma = indicators.calc_sma(self.asset.candles, self.setup.long)
        except Exception as e:
            console.show_error(f"Erro ao atualizar as médias móveis de {self.get_symbol()}: "
                               f"short {self.setup.short} long {self.setup.long}", e)

    def _update_rsi(self, start_date, end_date):
        r"""Atualiza o índice de força relativa (RSI) do ativo."""

        self.__rsi = indicators.calc_rsi(values=self.asset.candles, start_date=start_date, end_date=end_date,
                                         period=self.setup.rsi_period)

    def run(self, start_date, end_date) -> BacktestResult:
        r"""Executa um back test de acordo com a estratégia do atributo setup.

          :param start_date: data inicial dos registros de candles
          :param end_date: data final dos registros de candles
          :return: um objeto BacktestResult
          :rtype: BacktestResult
          """
        bt_result = None
        try:
            strategy = util.STRATEGIES[self.setup.get_strategy()]
            if strategy == 1:  # MA x MA
                bt_result = trading_crossover(setup=self.setup, df_candles=self.asset.candles,
                                              df_short_ema=self.__short_ema, df_long_sma=self.__long_sma,
                                              start_date=start_date, end_date=end_date)
            elif strategy == 2:  # MA x Price
                bt_result = trading_crossover(setup=self.setup, df_candles=self.asset.candles,
                                              df_short_ema=self.asset.candles, df_long_sma=self.__short_ema,
                                              start_date=start_date, end_date=end_date)
            elif strategy == 3:  # RSI: Min, Max
                bt_result = trading_rsi(df_candles=self.asset.candles, rsi_series=self.__rsi, start_date=start_date,
                                        end_date=end_date, setup=self.setup)
            elif 4 <= strategy <= 6:  # RSI: 4=quartis. 5=pelos discrepantes, 6=pela média de quartis e discrepantes
                rsi_min, rsi_max = indicators.get_rsi_thresholds(self.__rsi, self.setup.get_strategy())
                self.setup.rsi_min = rsi_min
                self.setup.rsi_max = rsi_max
                bt_result = trading_rsi(df_candles=self.asset.candles, rsi_series=self.__rsi, start_date=start_date,
                                        end_date=end_date, setup=self.setup)

        except Exception as e:
            console.show_error(f"Erro ao executar backtest de {self.setup.get_strategy()} para {self.get_symbol()}", e)

        return bt_result

    def get_json_signal(self, obs_only=False, limit=0):
        jsonstr = ""
        if self.signal is not None:
            df_signal = pd.DataFrame(self.signal.get_signals())
            if obs_only:
                df_signal = df_signal[df_signal.obs != ""]

            if limit > 0:
                df_signal = df_signal.sort_values(by=["date"], ascending=False)
                df_signal = df_signal[:limit]

            df_signal = df_signal.sort_values(by=["date"], ascending=True)

            df_signal['date'] = df_signal['date'].dt.strftime("%Y-%m-%d %H:%M:%S")
            jsonstr = json.loads(df_signal.to_json(orient="records"))

            if jsonstr is None:
                jsonstr = ""
        return jsonstr


def trading_crossover(df_candles, df_short_ema, df_long_sma, start_date, end_date, setup):
    r"""Back-testing utilizando a estratégia de cruzamento entre as médias móveis de menor e maior período
    ou preço X média. Onde a entrada é no cruzamento e a saída: no stop gain/loss.

   :param Setup setup: setup inicial do simulador
   :param pd.DataFrame df_candles: contém os preços de abertura, fechamento, minima, maxima e volume
   :param pd.DataFrame df_short_ema: as médias móveis curtas do preço de fechamento dos candles
   :param pd.DataFrame df_long_sma: as médias móveis longas do preço fechamento dos candles
   :param str start_date: data inicial dos registros de candles
   :param str end_date: data final dos registros de candles
   :return: objeto da classe BacktestResult
   :rtype: BacktestResult
   """
    my_wallet_usd = setup.start_money
    my_wallet_coins = buy_and_hold = 0
    accuracy = total_gains = total_losses = 0  # métricas para medir a precisão da estratégia
    price_position = price_position_real = price_sell = price_buy = price = time_position = 0
    last_row = last_balance = 0
    wallet_per_day = []  # lista que mantém o saldo da carteira em USD por dia
    signal = Signal()
    console.debug("Saldo inicial da carteira \033[1m(USD): {:.2f}\033[m".format(my_wallet_usd))
    df_cross = indicators.calc_crossover(df_short_ema, df_long_sma, start_date, end_date)  # dataframe com os cruzamentos de média ou preço x média

    for row in df_cross.itertuples():
        price = df_candles.loc[row.Index, "close"]  # preço verdadeiro
        price_buy = price + (price * setup.buy_increase / 100)  # preço com incremento de 'buy_increase'% ao comprar
        price_sell = price + (price * setup.sell_decrease / 100)  # preço com decremento de 'sell_decrease'% ao vender
        time = row.Index.strftime("%d/%m/%Y %H:%M")

        if buy_and_hold == 0:
            buy_and_hold = my_wallet_usd / price_buy  # inicializa estrategia buy and hold
        if last_row == 0:
            last_row = row
            wallet_per_day.append([last_row.Index, my_wallet_usd])  # primeiro registro de saldo na carteira

        if my_wallet_usd > 0 and last_row.close < 0 < row.close:  # se houver cruzamento indicando compra
            my_wallet_coins = my_wallet_usd / price_buy  # atualiza a quantidade moedas na carteira
            my_wallet_usd = 0  # atualiza a quantidade de USD na carteira
            price_position = price_buy  # para o preço flutuante (se trailing_stop=True)
            price_position_real = price_buy
            signal.insert_signal(date=row.Index, price=price_buy, action=1, strategy=setup.get_strategy(),
                                 obs="Comprou")  # sinal compra simulação
            if time_position == 0:  # primeira compra
                console.debug(f"\033[1;34mPrimeira compra em {time} ({my_wallet_coins:.8f} moedas ao preço de "
                              f"{price_buy:.5f} dólares \033[m)")
            else:
                interval = int((row.Index - time_position).total_seconds())
                h = interval // 3600
                m = (interval % 3600) // 60
                console.debug(
                    f"\033[1;34mPosição de compra em {time}, após {h:02d}h{m:02d}m ({my_wallet_coins:.8f} "
                    f"moedas ao preço de {price_buy:.5f} dólares).\033[m")
            time_position = row.Index  # atualiza o momento que fez a última operação, nesse caso foi compra
        elif my_wallet_coins > 0:  # se estiver em posicao comprado
            porc_price = ((price_sell / price_position) * 100) - 100

            if porc_price < setup.stop_loss:  # quando o preço cair abaixo do stop loss, vende o ativo
                porc_price_real = ((price_sell / price_position_real) * 100) - 100  # % preço no momento da compra
                if porc_price_real < 0:
                    color = 31  # vermelho
                    total_losses += 1
                else:
                    color = 32  # verde
                    total_gains += 1
                interval = int((row.Index - time_position).total_seconds())
                h = interval // 3600
                m = (interval % 3600) // 60
                console.debug(f"\033[1;{color}mGatilho Stop Loss atingido em {time}, após {h:02d}h{m:02d}m "
                              f"(stop {price_position:.5f}, compra {price_position_real:.5f}, venda {price_sell:.5f}, "
                              f"var. stop {porc_price:.2f}%, var. real {porc_price_real:.2f}%).\033[m")
                my_wallet_usd = my_wallet_coins * price_sell  # atualiza a quantidade moedas na carteira
                my_wallet_coins = 0
                time_position = row.Index
                price_position = price_sell
                signal.insert_signal(date=row.Index, price=price_sell, action=-1, strategy=setup.get_strategy(),
                                     obs=f"Vendeu por stop loss={porc_price:.2f}%")  # sinal venda simulação

            elif porc_price > setup.stop_gain:  # quando o preço subir e ultrapassar o stopgain
                interval = int((row.Index - time_position).total_seconds())
                h = interval // 3600
                m = (interval % 3600) // 60
                if setup.trailing_stop:  # atualiza o preço da última compra
                    console.debug(
                        f"\033[7;32mGatilho Trailing Stop em {time} (preço comprado {price_position:.5f}, "
                        f"preço atual {price_buy:.5f}, aumento de {porc_price:.2f}%).\033[m")
                    price_position = price_buy
                else:  # vende o ativo
                    console.debug(
                        f"\033[1;32mGatilho Stop Gain atingido em {time}, após {h:02d}h{m:02d}m (preço comprado "
                        f"{price_position:.5f}, preço vendido {price_sell:.5f}, variação de {porc_price:.2f}%).\033[m")
                    my_wallet_usd = my_wallet_coins * price_sell
                    my_wallet_coins = 0
                    time_position = row.Index
                    price_position = price_sell
                    total_gains += 1
                    signal.insert_signal(date=row.Index, price=price_sell, action=-1, strategy=setup.get_strategy(),
                                         obs=f"Vendeu por stop gain={porc_price:.2f}%")  # sinal venda simulação (stop_gain)

            if row.close < 0 < last_row.close:  # se houver cruzamento indicando venda
                signal.insert_signal(date=row.Index, price=price_sell, action=-1, strategy=setup.get_strategy())
            elif last_row.close < 0 < row.close:  # se houver cruzamento indicando compra
                signal.insert_signal(date=row.Index, price=price_buy, action=1, strategy=setup.get_strategy())  # compra
            #else:
            #    signal.insert_signal(date=row.Index, price=price_sell, action=0, strategy=setup.get_strategy())

        if row.Index.day_name() != last_row.Index.day_name():
            wallet_per_day.append([last_row.Index, last_balance])  # armazena o resultado do dia anterior se mudar o dia
        last_balance = my_wallet_coins * price_sell if my_wallet_coins > 0 else my_wallet_usd  # ternário em Python
        last_row = row
    wallet_per_day.append([last_row.Index, last_balance])  # insere o último valor registrado no saldo diário
    df_wallet = pd.DataFrame(data=wallet_per_day)  # cria o df com a lista por dia
    df_wallet.columns = ("day", "balance")  # altera o nome das duas colunas
    df_wallet.set_index("day", inplace=True)  # cria um índice com a coluna dia (datetime)
    if my_wallet_coins > 0:
        trade_res = f"{((my_wallet_coins * price_sell / setup.start_money) * 100) - 100:.2f}"
        console.debug("Finalizou período na posição comprado com {:.8f} moedas (\033[1mUSD {:.2f} = {}%\033[m)".format(
            my_wallet_coins, my_wallet_coins * price, trade_res))
        if price_buy > price_position_real:  # se o preço subiu depois de comprado
            total_gains += 1  # acertou a previsão
        else:
            total_losses += 1  # errou a previsão
    else:
        trade_res = f"{((my_wallet_usd / setup.start_money) * 100) - 100:.2f}"
        console.debug("Finalizou período na posição vendido com \033[1mUSD {:.2f} = {}%\033[m".format(my_wallet_usd, trade_res))
        if price_position > 0:  # se posicionou pelo menos 1 vez
            if price_sell > price_position_real:  # e o preço subiu depois de vendido
                total_losses += 1  # errou a previsão
            else:
                total_gains += 1  # acertou a previsão
    buy_and_hold_res = ((buy_and_hold * price_sell / setup.start_money) * 100) - 100
    if total_gains > 0 or total_losses > 0:
        accuracy = (total_gains / (total_gains + total_losses)) * 100

    return BacktestResult(trade_returns=float(trade_res), buy_and_hold_returns=buy_and_hold_res, accuracy=accuracy,
                          df_wallet=df_wallet, signal=signal)


def trading_rsi(df_candles, rsi_series, start_date, end_date, setup):
    r"""Back-testing utilizando a estratégia RSI (Índice de Força Relativa), onde a entrada e saída é sinalizada
     pelo indicador de sobrevenda e sobrecompra do ativo.

   :param Setup setup: setup inicial do simulador
   :param pd.DataFrame df_candles: contém os preços de abertura, fechamento, minima, maxima e volume
   :param pd.Series rsi_series: série que contém o Índice de Força Relativa de df_candle no período
   :param str start_date: data inicial dos registros de candles
   :param str end_date: data final dos registros de candles
   :return: objeto da classe BacktestResult
   :rtype: BacktestResult
   """
    my_wallet_usd = setup.start_money
    my_wallet_coins = buy_and_hold = 0
    accuracy = total_gains = total_losses = 0  # métricas para medir a precisão da estratégia
    price_position = time_position = 0
    last_index = last_balance = 0
    wallet_per_day = []  # lista que mantém o saldo da carteira em USD por dia
    signal = Signal()
    console.debug("Saldo inicial da carteira \033[1m(USD): {:.2f}\033[m".format(my_wallet_usd))
    rsi_series = rsi_series.loc[start_date: end_date]
    for index, value in rsi_series.items():
        price = df_candles.loc[index, "close"]
        price_buy = price + (price * setup.buy_increase / 100)  # preço com incremento de 'buy_increase'% ao comprar
        price_sell = price + (price * setup.sell_decrease / 100)  # preço com decremento de 'sell_decrease'% ao vender
        time = index.strftime("%d/%m/%Y %H:%M")

        if buy_and_hold == 0:
            buy_and_hold = my_wallet_usd / price_buy  # inicializa estrategia buy and hold
        if last_index == 0:
            last_index = index
            wallet_per_day.append([index, my_wallet_usd])  # primeiro registro de saldo na carteira
        if value > setup.rsi_max:  # se RSI indicar sobrecompra

            if my_wallet_coins > 0:  # e estiver em posicao comprado
                porc_price = ((price_sell / price_position) * 100) - 100
                if porc_price < 0:
                    cor = 31  # vermelho
                    total_losses += 1
                else:
                    cor = 32  # verde
                    total_gains += 1

                interval = int((index - time_position).total_seconds())
                h = interval // 3600
                m = (interval % 3600) // 60
                console.debug(
                    f"\033[1;{cor}mRSI sobrecomprado em {time}, após {h:02d}h{m:02d}m (RSI: {value:.2f}, "
                    f"vendido a {price_sell:.5f}, preço de compra {price_position:.5f}, {porc_price:.2f}%).\033[m")
                my_wallet_usd = my_wallet_coins * price_sell  # atualiza a quantidade moedas na carteira
                my_wallet_coins = 0  # atualiza a quantidade de USD na carteira
                time_position = index  # atualiza o momento que fez a última operação, nesse caso foi venda
                price_position = price_sell
                signal.insert_signal(date=index, price=price_sell, action=-1, strategy=setup.get_strategy(),
                                     obs=f"Vendeu por sobrecompra RSI={value:.2f}", rsi=value)  # sinal simulador venda

            signal.insert_signal(date=index, price=price_sell, action=-1,
                                 strategy=setup.get_strategy(), rsi=value)  # sinal p/ venda

        elif value <= setup.rsi_min:  # ou se RSI indicar sobrevenda

            if my_wallet_usd > 0:  # estiver em posição vendido
                my_wallet_coins = my_wallet_usd / price_buy
                my_wallet_usd = 0

                if time_position == 0:   # primeira compra não calcular o tempo
                    console.debug(f"\033[1;34mPrimeira compra, RSI sobrevendido em {time} (RSI: {value:.2f}, "
                                  f"comprado {my_wallet_coins:.8f} moedas ao preço de {price_buy:.5f} USD \033[m).")
                else:
                    interval = int((index - time_position).total_seconds())
                    h = interval // 3600
                    m = (interval % 3600) // 60
                    console.debug(f"\033[1;34mRSI sobrevendido em {time}, após {h:02d}h{m:02d}m (RSI: {value:.2f}, "
                                  f"comprado {my_wallet_coins:.8f} moedas ao preço de {price_buy:.5f} USD).\033[m")

                price_position = price_buy
                time_position = index  # atualiza o momento que fez a última operação, nesse caso foi compra
                signal.insert_signal(date=index, price=price_buy, action=1, strategy=setup.get_strategy(),
                                     obs=f"Comprou por sobrevenda RSI={value:.2f}", rsi=value)  # sinal simulador compra

            signal.insert_signal(date=index, price=price_buy, action=1, strategy=setup.get_strategy(), rsi=value)  # sinal compra
        #else:
        #    signal.insert_signal(date=index, price=price, action=0, strategy=setup.get_strategy())  # sinal neutro

        if index.day_name() != last_index.day_name():
            wallet_per_day.append([last_index, last_balance])  # armazena o resultado do dia anterior se mudar o dia
        last_balance = my_wallet_coins * price_sell if my_wallet_coins > 0 else my_wallet_usd  # ternário em Python
        last_index = index

    wallet_per_day.append([last_index, last_balance])  # insere o último valor registrado no saldo diário
    df_wallet = pd.DataFrame(data=wallet_per_day)  # cria o df com a lista por dia
    df_wallet.columns = ("day", "balance")  # altera o nome das duas colunas
    df_wallet.set_index("day", inplace=True)  # cria um índice com a coluna dia (datetime)
    if my_wallet_coins > 0:
        trade_res = f"{((my_wallet_coins * price_sell / setup.start_money) * 100) - 100:.3f}"
        console.debug("Finalizou período na posição comprado com {:.8f} moedas (\033[1mUSD {:.2f} = {}%\033[m)".format(
            my_wallet_coins, my_wallet_coins * price, trade_res))
        if price_sell > price_position:  # e se preço subiu depois de comprado
            total_gains += 1  # acertou a previsão
        else:
            total_losses += 1  # errou a previsão
    else:
        trade_res = f"{((my_wallet_usd / setup.start_money) * 100) - 100:.3f}"
        console.debug("Finalizou período na posição vendido com \033[1mUSD {:.3f} = {}%\033[m".
                      format(my_wallet_usd, trade_res))
        if price_position > 0:  # se se posicionou pelo menos 1 vez
            if price_buy > price_position:  # e se preço subiu depois de vendido
                total_losses += 1  # errou a previsão
            else:
                total_gains += 1  # acertou a previsão

    buy_and_hold_res = ((buy_and_hold * price_sell / setup.start_money) * 100) - 100
    if total_gains > 0 or total_losses > 0:
        accuracy = (total_gains / (total_gains + total_losses)) * 100

    return BacktestResult(trade_returns=float(trade_res), buy_and_hold_returns=buy_and_hold_res, accuracy=accuracy,
                          df_wallet=df_wallet, signal=signal)

