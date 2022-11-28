# -*- coding: utf-8 -*-
u"""
Description: Classe para modelo que representa o resultado de um backtest.
File name: btresult.py
Author: Daniel Tell <daniel.tell@gmail.com>
Date created: 19/09/2022
Date last modified: 19/09/2022
"""
from algotradingpy.model.signal import Signal
from pandas import DataFrame


class BacktestResult:

    def __init__(self, trade_returns, buy_and_hold_returns, accuracy, df_wallet, signal):
        r"""Construtor de BacktestResult que inicializa os dados .

        :param float trade_returns: retorno em % se usar a estrategia trading
        :param float buy_and_hold_returns: retorno em % se usar a estrategia buy and hold
        :param float accuracy: precisão de 0 a 100% da estrategia de trade
        :param DataFrame df_wallet: data frame contendo o saldo na carteira por dia, onde o primeiro registro é o 'start_money'
        :param Signal signal: um objeto contendo todos os sinais de compra/venda durante o back test
        :rtype: BacktestResult
        """
        self.trade_returns = trade_returns
        self.buy_and_hold_returns = buy_and_hold_returns
        self.accuracy = accuracy
        self.df_wallet = df_wallet
        self.signal = signal

    def get_trade_returns(self):
        return self.trade_returns

    def get_buy_and_hold_returns(self):
        return self.buy_and_hold_returns

    def get_accuracy(self):
        return self.accuracy

    def get_df_wallet(self):
        return self.df_wallet

    def get_signal(self) -> Signal:
        return self.signal
