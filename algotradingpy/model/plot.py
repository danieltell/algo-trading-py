u"""
Created on 2021-10-23
Updated on 2021-11-12

@author: Daniel Tell
"""

import matplotlib.pyplot as plt
from mpl_finance import candlestick_ohlc
import datetime
import matplotlib.dates as mdates
import pandas as pd

from algotradingpy.controller.backtest import BackTest
from algotradingpy.view import console


def plot(x, y, ax, title, y_label):
    ax.set_title(title)
    ax.set_ylabel(y_label)
    ax.plot(x, y)
    ax.margins(x=0, y=0)

def get_date_format(start_date, end_date):
    # definindo as formações para as datas
    hour_minute_fmt = mdates.DateFormatter('%H:%M')
    day_hour_fmt = mdates.DateFormatter('%d/%m %H:%M')
    day_month_fmt = mdates.DateFormatter('%d/%m')
    year_month_fmt = mdates.DateFormatter('%m/%y')
    # Ajusta a formatação de data de acordo com o período escolhido

    start = datetime.datetime.strptime(start_date + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
    end = datetime.datetime.strptime(end_date + ' 00:00:00', '%Y-%m-%d %H:%M:%S')

    days = (end - start).total_seconds() // 3600 // 24
    if days == 0:
        return hour_minute_fmt
    elif days <= 7:
        return day_hour_fmt
    elif days <= 90:
        return day_month_fmt
    else:
        return year_month_fmt


class TimeSeries:

    def __init__(self, backtest: BackTest):

        self.backtest = backtest

    def time_series_all(self, start_date, end_date, ema_short, sma_long, short_periods, long_periods):
        r"""Plota as séries temporais de preço e médias móveis curtas e
        longas calculadas no período de start_date a end_date

            @param start_date: Data inicial no formato yyyy-mm-dd
            @type start_date: str
            @param end_date: Data final no formato yyyy-mm-dd
            @type end_date: str
            @param ema_short: Médias móveis curtas exponenciais
            @type ema_short: DataFrame
            @param sma_long: Médias móveis longas simples
            @type sma_long: DataFrame
            @param short_periods: Número de períodos usados no cálculo das médias curtas
            @type short_periods: str
            @param long_periods: Número de períodos usados no cálculo das médias longas
            @type long_periods: str
        """
        console.show('Estratégia Média Curta Exponencial X Média Longa Simples:')
        date_format = get_date_format(start_date, end_date)
        fig, ax1 = plt.subplots(figsize=(16, 9))
        ax1.plot(self.backtest.asset.candles.loc[start_date:end_date, :].index, self.backtest.asset.candles.loc[start_date:end_date, 'close'], label='Preço (Close)')
        ax1.plot(ema_short.loc[start_date:end_date, :].index, ema_short.loc[start_date:end_date, 'close'],
                 label=short_periods + '-amostras Média Móvel Exp.')
        ax1.plot(sma_long.loc[start_date:end_date, :].index, sma_long.loc[start_date:end_date, 'close'],
                 label=long_periods + '-amostras Média Móvel Simples')
        ax1.xaxis_date()  # interpreta os valores do eixo x como data
        fig.autofmt_xdate()  # rotaciona os rótulos do eixo x
        ax1.legend(loc='best')
        ax1.set_ylabel('Preço ' + self.backtest.asset.description)
        ax1.xaxis.set_major_formatter(date_format)
        symbol = str(self.backtest.asset.symbol).replace(':', '')
        self._draw_annotations()# Desenha setas com texto indicando a compra ou a venda
        plt.savefig(f'{symbol}_ema_{short_periods}_x_sma_{long_periods}_period_{start_date}_a_{end_date}.svg',
                    bbox_inches='tight')
        plt.show()

    # Plota as séries temporais de preço e médias móveis curta calculadas no período de start_date a end_date
    def time_series_short(self, start_date, end_date, sma_short, short_periods):
        r"""Plota as séries temporais de preço e médias móveis curtas no período de start_date a end_date

           @param start_date: Data inicial no formato yyyy-mm-dd
           @type start_date: str
           @param end_date: Data final no formato yyyy-mm-dd
           @type end_date: str
           @param sma_short: Médias móveis curtas simples
           @type sma_short: DataFrame
           @param short_periods: Número de períodos usados no cálculo das médias curtas
           @type short_periods: str
       """
        console.show('Estratégia Média Curta Simples X Preço:')
        date_format = get_date_format(start_date, end_date)
        fig, ax1 = plt.subplots(figsize=(16, 9))
        ax1.plot(self.backtest.asset.candles.loc[start_date:end_date, :].index, self.backtest.asset.candles.loc[start_date:end_date, 'close'], label='Preço (Close)')
        ax1.plot(sma_short.loc[start_date:end_date, :].index, sma_short.loc[start_date:end_date, 'close'],
                 label=short_periods + '-amostras Média Móvel Exp.')
        # ax1.plot(df.loc[start_date+' 00:00:00':end_date + ' 01:00:00', :].index, df.loc[start_date+' 00:00:00':end_date + ' 01:00:00', 'close'], label='Preço (Close)')
        # ax1.plot(ma_short.loc[start_date+' 00:00:00':end_date + ' 01:00:00', :].index, ma_short.loc[start_date+' 00:00:00':end_date + ' 01:00:00', 'close'], label = short_price_txt.value + '-amostras Média Móvel Curta.')

        ax1.xaxis_date()  # interpreta os valores do eixo x como data
        fig.autofmt_xdate()  # rotaciona os rótulos do eixo x
        ax1.legend(loc='best')
        ax1.set_ylabel('Preço ' + self.backtest.asset.description)
        ax1.xaxis.set_major_formatter(date_format)
        symbol = str(self.backtest.asset.symbol).replace(':', '')
        self._draw_annotations()# Desenha setas com texto indicando a compra ou a venda
        plt.savefig(f'{symbol}_ema_{short_periods}_x_price_{start_date}_a_{end_date}.svg', bbox_inches='tight')
        plt.show()

    # Plota o saldo da carteira em USD no período de start_date a end_date mensalmente
    def wallet_balance(self, start_date, end_date, df_wallet_ma, df_wallet_price, df_wallet_rsi):
        r"""Plota as séries temporais de preço e médias móveis curtas no período de start_date a end_date

           @param start_date: Data inicial no formato yyyy-mm-dd
           @type start_date: str
           @param end_date: Data final no formato yyyy-mm-dd
           @type end_date: str
           @param df_wallet_ma: DataFrame contendo o saldo da carteira no backtest cruzamento de médias móveis
           @type df_wallet_ma: DataFrame
           @param df_wallet_price: DataFrame contendo o saldo da carteira no backtest cruzamento preço x média
           @type df_wallet_price: DataFrame
           @param df_wallet_rsi: DataFrame contendo o saldo da carteira no backtest RSI
           @type df_wallet_rsi: DataFrame
       """
        if df_wallet_ma is not None and df_wallet_price is not None:
            console.show('Saldo na carteira para cada estratégia:')
            date_format = get_date_format(start_date, end_date)

            fig, ax1 = plt.subplots(figsize=(16, 9))
            ax1.plot(df_wallet_ma.loc[start_date:end_date, :].index, df_wallet_ma.loc[start_date:end_date, 'balance'],
                     label='Saldo MA x MA(USD)')
            ax1.plot(df_wallet_price.loc[start_date:end_date, :].index,
                     df_wallet_price.loc[start_date:end_date, 'balance'], label='Saldo MA x Preço (USD)')
            ax1.plot(df_wallet_rsi.loc[start_date:end_date, :].index, df_wallet_rsi.loc[start_date:end_date, 'balance'],
                     label='Saldo RSI Fixo (USD)')
            ax1.xaxis_date()  # interpreta os valores do eixo x como data
            fig.autofmt_xdate()  # rotaciona os rótulos do eixo x
            ax1.legend(loc='best')
            ax1.set_ylabel('Saldo em USD')
            ax1.xaxis.set_major_formatter(date_format)
            plt.show()

    # Plota o saldo da carteira em USD no período de start_date a end_date mensalmente
    def wallet_balance_rsi(self, df_wallet_1, df_wallet_2, df_wallet_3, **kwargs):
        # rsi_thresholds_1, rsi_thresholds_2, rsi_thresholds_3,  start_date, end_date, date_format
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')
        date_format = get_date_format(start_date, end_date)
        fig, ax1 = plt.subplots(figsize=(16, 9))
        if df_wallet_1 is not None:
            ax1.plot(df_wallet_1.loc[start_date:end_date, :].index, df_wallet_1.loc[start_date:end_date, 'balance'],
                     label='Saldo RSI QI/QS (USD) [{:.2f}/{:.2f}]'.format(kwargs.get('rsi_thresholds_1_min'), kwargs.get('rsi_thresholds_1_max')))
        if df_wallet_2 is not None:
            ax1.plot(df_wallet_2.loc[start_date:end_date, :].index, df_wallet_2.loc[start_date:end_date, 'balance'],
                     label='Saldo Outlier-I/Outlier-S (USD) [{:.2f}/{:.2f}]'.format(kwargs.get('rsi_thresholds_2_min'), kwargs.get('rsi_thresholds_2_max')))
            # ax1.plot(df_wallet_2.loc[start_date:end_date, :].index, df_wallet_2.loc[start_date:end_date, 'balance'], label='Saldo MA x MA(USD)')
        if df_wallet_3 is not None:
            ax1.plot(df_wallet_3.loc[start_date:end_date, :].index, df_wallet_3.loc[start_date:end_date, 'balance'],
                     label='Saldo QI+Out-I/QS+Out-S (USD) [{:.2f}/{:.2f}]'.format(kwargs.get('rsi_thresholds_3_min'), kwargs.get('rsi_thresholds_3_max')))
            # ax1.plot(df_wallet_3.loc[start_date:end_date, :].index, df_wallet_3.loc[start_date:end_date, 'balance'], label='Saldo MA x Preço (USD)')
        ax1.xaxis_date()  # interpreta os valores do eixo x como data
        fig.autofmt_xdate()  # rotaciona os rótulos do eixo x
        ax1.legend(loc='best')
        ax1.set_ylabel('Saldo em USD')
        ax1.xaxis.set_major_formatter(date_format)
        plt.show()

    # Plota o o gráfico IFR (Índice de força relativa) sendo cortado pelos limites de inferior (sobrevenda) e superior (sobrecompra)
    def rsi_series(self, start_date, end_date, rsi_min, rsi_max, rsi_period, rsi_series):
        console.show('Índice de Força Relativa no período:')
        date_format = get_date_format(start_date, end_date)
        fig, ax1 = plt.subplots(figsize=(16, 9))
        df_rsi_min = pd.DataFrame(data=[[rsi_series.loc[start_date:end_date].index.values[0],
                                      rsi_min], [rsi_series.loc[start_date:end_date].index.values[-1], rsi_min]])
        df_rsi_min.columns = ('time', 'rsi_min')  # altera o nome das duas colunas
        df_rsi_min.set_index('time', inplace=True)  # cria um índice com a coluna dia (datetime)
        df_rsi_max = pd.DataFrame(data=[[rsi_series.loc[start_date:end_date].index.values[0],
                                      rsi_max], [rsi_series.loc[start_date:end_date].index.values[-1], rsi_max]])
        df_rsi_max.columns = ('time', 'rsi_max')  # altera o nome das duas colunas
        df_rsi_max.set_index('time', inplace=True)  # cria um índice com a coluna dia (datetime)
        ax1.plot(rsi_series.loc[start_date:end_date, ].index, rsi_series.loc[start_date:end_date],
                 label='RSI de ' + rsi_period + '-periodos.')
        ax1.plot(df_rsi_max.loc[start_date:end_date, ].index, df_rsi_max.loc[start_date:end_date],
                 label='Limite Superior: {:.2f}'.format(rsi_max))
        ax1.plot(df_rsi_min.loc[start_date:end_date, ].index, df_rsi_min.loc[start_date:end_date],
                 label='Limite Inferior: {:.2f}'.format(rsi_min))
        ax1.xaxis_date()  # interpreta os valores do eixo x como data
        fig.autofmt_xdate()  # rotaciona os rótulos do eixo x
        ax1.legend(loc='best')
        ax1.set_ylabel('RSI - ' + self.backtest.asset.description)
        ax1.xaxis.set_major_formatter(date_format)
        symbol = str(self.backtest.asset.symbol).replace(':', '')
        self._draw_annotations()# Desenha setas com texto indicando a compra ou a venda
        plt.savefig(f'{symbol}_rsi_{rsi_min}_{rsi_max}_period_{start_date}_a_{end_date}.svg', bbox_inches='tight')

    def _draw_annotations(self):
        # Desenha setas e textos indicando a compra ou a venda
        df_signals = pd.DataFrame(self.backtest.get_json_signal(True, 0))
        df_signals.date = pd.to_datetime(df_signals.date)
        min_price = self.backtest.asset.candles.min().close
        max_price = self.backtest.asset.candles.max().close
        if 'RSI' in self.backtest.setup.strategy:
            min_price = 0
            max_price = 100

        for row in df_signals.itertuples():  # itera sobre cada linha do dataframe
            obs = 'Compra'
            y_text = min_price
            color = 'g'
            value = row.price
            if 'RSI' in self.backtest.setup.strategy:
                value = row.rsi
            if 'Vendeu' in row.obs:
                obs = 'Venda'
                y_text = max_price
                color = 'r'
                # console.show(f'{row.date}, {row.price}, {row.obs}')

            plt.annotate(obs, xy=(row.date, value),
                         xytext=(row.date, y_text),
                         arrowprops={'width': 1, 'headwidth': 5, 'headlength': 5, 'color': color},
                         horizontalalignment='center', fontsize=8)

class Candlestick:

    def candle_stick(self, values, ema_short, sma_long, **kwargs):
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')
        time_frame = kwargs.get('time_frame')
        fig, ax = plt.subplots(figsize=(16, 9))
        number = int(''.join(filter(str.isdigit, time_frame)))
        if number == 0:
            number = 1
        if 'm' in time_frame:
            w = 0.5 / (24 * 60 / number)
        elif 'h' in time_frame:
            w = 0.5 / (24 / number)
        else:
            w = 0.5

        # Cria o gráfico de candles para o período (usar time2 como eixo x, que é a data no formato float)

        df_period = values.loc[start_date:end_date, :]
        tuples = [tuple(x) for x in df_period[['time2', 'open', 'high', 'low', 'close']].values]
        candlestick_ohlc(ax, tuples, width=w, colorup='g', alpha=0.4)
        # Médias móveis
        ax.plot(ema_short.loc[start_date:end_date, :].index, ema_short.loc[start_date:end_date, 'close'],
                label=kwargs.get('short_periods') + '-amostras Média Móvel Exp.')
        ax.plot(sma_long.loc[start_date:end_date, :].index, sma_long.loc[start_date:end_date, 'close'],
                label=kwargs.get('long_periods') + '-amostras Média Móvel Simples')
        #
        fig.autofmt_xdate()
        fig.tight_layout()
        ax.xaxis.set_major_formatter(kwargs.get('date_format'))
        # ax.grid(True)
        ax.legend(loc='best')
        plt.xlabel('Timeframe: {} '.format(time_frame))
        plt.ylabel("Preço")
        plt.title(kwargs.get('description'))

