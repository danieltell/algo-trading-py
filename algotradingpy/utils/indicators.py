u"""
Created on 2021-10-23
Updated on 2021-11-12

@author: Daniel Tell
"""

import pandas as pd
import algotradingpy.view.console as console
import numpy as np
import algotradingpy.utils.util as util


def calc_ema(values, period):
    #return values.ewm(span=period, adjust=False, min_periods=1).mean()
    return values.ewm(span=period, adjust=False).mean()


def calc_sma(values, period):
    #return values.rolling(window=period, min_periods=1).mean()
    return values.rolling(window=period).mean()


def calc_crossover(short_ema, long_ma, start_date, end_date):
    r""" Faz o cruzamento das médias móveis curtas e longas. Faz a diferença entre elas para determinar se a média
    curta cruzou de cima para baixo ou vice-versa.

   :param pd.DataFrame df_short_ema: as médias móveis curtas do preço de fechamento dos candles
   :param pd.DataFrame df_long_sma: as médias móveis longas do preço fechamento dos candles
   :param str start_date: data inicial dos registros de candles
   :param str end_date: data final dos registros de candles
   :return: um DataFrame com os valores 1, -1 ou 0 indicando quando houve cruzamento entre as médias.
   :rtype: pd.DataFrame
   """
    trading_pos_raw = short_ema[start_date:end_date] - long_ma[start_date:end_date]  # faz a diferença entre as médias
    trading_positions = trading_pos_raw.apply(np.sign)  # aplica o sinal da diferença com o numpy
    trading_positions_final = trading_positions.shift(1)  # atrasa os sinais de negociação em um período
    return trading_positions_final


def calc_rsi(values, start_date, end_date, period):
    r""" Calcula o Índice de Força Relativa (IFR/RSI)

      :param pd.DataFrame values: valores de preços de fechamento (close) do candle no período de start_date a end_date
      :param str start_date: data inicial dos registros de values
      :param str end_date: data final dos registros de values
      :param int period: periodos que serão utilizados para calcular o IFR
      :return: uma Serie contendo os valores de IFR
      :rtype: pd.Series
      """
    df_tmp = values.loc[start_date: end_date, :]
    close = df_tmp['close']
    delta = close.diff()  # Obtendo a diferença de preço no fechamento do candle
    delta = delta[1:]  # Elimina a primeira linha
    up, down = delta.copy(), delta.copy()  # Faz as séries dos ganhos positivos (up) e ganhos negativos (down)
    up[up < 0] = 0  # Faz as séries dos ganhos positivos (up)
    down[down > 0] = 0  # Faz as séries dos ganhos negativos (down)
    roll_up = up.ewm(span=int(period), adjust=False).mean()  # Calculando a média móvel exponencial (EMA)
    roll_down = down.abs().ewm(span=int(period), adjust=False).mean()
    rs = roll_up / roll_down  # Calcule a RSI com base na EMA
    rsi = 100.0 - (100.0 / (1.0 + rs))
    rsi = rsi.loc[start_date: end_date]
    return rsi


def get_rsi_thresholds(rsi, strategy):
    r"""Calcula o limite inferior e superior para cada uma das 3 estratégias de RSI em util.STRATEGIES.

       :param pd.Series rsi:
       :param int strategy: tipo de
       :return: uma tupla de dois valores inteiros: limite inferior e limite superior
       :rtype: tuple
       """
    rsi_min = 0
    rsi_max = 0
    if strategy in util.STRATEGIES:
        option = util.STRATEGIES[strategy]
        # Estratégias: 4 = pelos quartis; 5=pelos discrepantes (I/S); 6=pela média de quartis e discrepantes

        if option == 4:
            rsi_min = rsi.quantile(.25)
            rsi_max = rsi.quantile(.75)
        if option == 5:
            rsi_min, rsi_max = get_rsi_outliers(rsi)
            # Caso não tenha outlier inferior ou superior utilizar: Min + (Max - Min)*0.1
            if rsi_min is None or rsi_max is None:
                rsi_min = rsi.min() + ((rsi.max() - rsi.min()) * 0.1)
                rsi_max = rsi.max() - ((rsi.max() - rsi.min()) * 0.1)
        if option == 6:
            oi, os = get_rsi_outliers(rsi)
            # Caso não tenha outlier inferior ou superior utilizar: Min + (Max - Min)*0.1
            if oi is None or os is None:
                # oi = rsi.min()
                # os = rsi.max()
                oi = rsi.min() + ((rsi.max() - rsi.min()) * 0.1)
                os = rsi.max() - ((rsi.max() - rsi.min()) * 0.1)
            rsi_min = (rsi.quantile(.25) + oi) / 2
            rsi_max = (rsi.quantile(.75) + os) / 2

    return rsi_min, rsi_max


def get_rsi_outliers(rsi):
    r"""Encontra e retorna uma tupla com o primeiro menor outlier inferior e o maior outlier superior
       :param pd.DataFrame rsi:
       :return: uma tupla de dois valores inteiros: outlier inferior e outlier superior
       :rtype: tuple
       """
    q1 = rsi.quantile(0.25)
    q3 = rsi.quantile(0.75)
    iqr = q3 - q1
    console.debug(f'IQR= {iqr} - OutI < {(q1 - 1.5 * iqr)} - OutS > {(q3 + 1.5 * iqr)}')
    df_outliers_i = rsi.loc[rsi < (q1 - 1.5 * iqr)]
    df_outliers_s = rsi.loc[rsi > (q3 + 1.5 * iqr)]
    console.debug(f"Total Registros= {len(rsi)} - Outliers Inferiores= {len(df_outliers_i)} - "
                  f"Outliers Superiores= {len(df_outliers_s)}")

    if len(df_outliers_i) > 0:
        df_outliers_i = df_outliers_i.sort_values(ascending=False)
        df_outliers_i = df_outliers_i.head(1)
        oi = df_outliers_i.iat[0]
    else:
        oi = None
    if len(df_outliers_s) > 0:
        df_outliers_s = df_outliers_s.sort_values(ascending=True)
        df_outliers_s = df_outliers_s.head(1)
        os = df_outliers_s.iat[0]
    else:
        os = None
    return oi, os





