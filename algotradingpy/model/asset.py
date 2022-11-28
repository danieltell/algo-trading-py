# -*- coding: utf-8 -*-
u"""
Description: Classe Modelo para representar um ativo que possui dados de candlestick ou de negociações.
File name: asset.py
Author: Daniel Tell <daniel.tell@gmail.com>
Date created: 02/10/2021
Date last modified: 30/09/2022
"""
import pandas as pd
from datetime import datetime
import algotradingpy.view.console as console
import json


class Asset:
    candles = pd.DataFrame([])  # dados históricos de candlestck / negociações
    trades = pd.DataFrame([])  # dados históricos de negociações
    last_update: datetime = None  # datetime da última atualização de candles/trades

    def __init__(self, ptype, symbol, description, time_frame, data):
        r"""Construtor de Asset que inicializa os dados de candles/trades dependendo do parâmetro ptype.

        :param ptype: tipo de conteúdo em 'data': candlestick ou trade
        :param symbol: símbolo do ativo
        :param description: descrição do símbolo do ativo
        :param time_frame: período de tempo de cada candlestick (1m, 5m, 15m, etc)
        :param data: um DataFrame com os dados
        """
        self._type = ptype
        self.symbol = symbol
        self.description = description
        self.time_frame = time_frame
        self.last_update = datetime.now()
        self.updated = True

        if ptype == "candlestick":
            self.candles = data
        elif ptype == "trade":
            self.trades = data
        else:
            console.show_warning(f"Tipo {ptype} para o símbolo {symbol} é inválido!" 
                                 f" São aceitos apenas os tipos \"candlestick\" ou \"trade\".")

    def get_type(self):
        return self._type

    def get_json_data(self):
        if self.get_type() == "candlestick":
            df_copy = self.candles.reset_index()
        else:
            df_copy = self.trades.reset_index()
        df_copy.rename(columns={"time": "date"}, inplace=True)
        df_copy['date'] = df_copy['date'].dt.strftime("%Y-%m-%d %H:%M:%S")
        jsonfiles = json.loads(df_copy.to_json(orient='records'))

        return jsonfiles

    """def get_json_symbols(self):
        jsonfiles = json.loads(self.symbols.to_json(orient='records', date_unit='ms'))
        return jsonfiles"""

