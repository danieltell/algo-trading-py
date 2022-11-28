# -*- coding: utf-8 -*-
u"""
Description: Classe Modelo para representar um setup de negociação/backtest de negociação.
File name: asset.py
Author: Daniel Tell <daniel.tell@gmail.com>
Date created: 21/09/2022
Date last modified: 24/10/2022
"""
import algotradingpy.utils.util as util
import json


class Setup:

    strategy: str = None
    start_money: float = None
    start_date: str = None
    end_date: str = None
    last_update = None  # datetime de quando o setup foi atualizado
    returns = 0
    accuracy = 0

    def __init__(self, strategy, start_money=500, short=5, long=15, stop_gain=3, stop_loss=-3, trailing_stop=False,
                 rsi_min=30, rsi_max=70, rsi_period=14, buy_increase=0.0, sell_decrease=0.0):
        r""" Constrói um setup inicializado com parâmetros

         :param str strategy: a estratégia pode ser uma das 6 contidas em util.STRATEGIES
         :param float start_money: saldo inicial da carteira
         :param float stop_gain: porcentagem na valorização do preço para disparar o gatilho de 'parada de ganho'
         :param float stop_loss: porcentagem na desvalorização do preço para disparar o gatilho de 'parada de perda'
         :param bool trailing_stop: indica se aplica ou não a técnica de 'stop móvel'
         :param int short: número de amostras para média móvel curta
         :param int long: int número de amostras para média móvel longa
         :param int rsi_min: limite inferior (sobrevenda) do índice de força relativa (RSI)
         :param int rsi_max:  limite superior (sobrecompra) do índice de força relativa (RSI)
         :param float buy_increase: porcentagem a acrescentar no valor de compra do ativo Ex.: 0.15
         :param float sell_decrease: porcentagem a decrementar no valor de venda do ativo. Ex.: -0.1
         :rtype: Setup
         """

        self.set_strategy(strategy)
        self.set_start_money(start_money)
        self.buy_increase = buy_increase
        self.sell_decrease = sell_decrease
        self.stop_loss = float(f"{stop_loss:.2f}")
        self.stop_gain = float(f"{stop_gain:.2f}")
        self.trailing_stop = trailing_stop
        self.short = int(short)
        self.long = int(long)
        self.rsi_min = float(f"{rsi_min:.2f}")
        self.rsi_max = float(f"{rsi_max:.2f}")
        self.rsi_period = rsi_period

    def set_strategy(self, strategy):
        if strategy in util.STRATEGIES:
            self.strategy = strategy
        else:
            raise Exception(f"Valor de strategy é inválido! Valores aceitos: {util.STRATEGIES}")

    def get_strategy(self):
        return self.strategy

    def set_start_money(self, value):
        if value > 0:
            self.start_money = value
        else:
            raise Exception("Valor de start_money não pode ser zero ou negativo!")

    def set_parameters(self, **kwargs):
        r""" Atualiza um ou mais parâmetros do setup

            :param kwargs: start_money, buy_increase, sell_decrease. stop_gain, stop_loss, trailing_stop,
            short, long, returns, start_date, end_date, last_update, rsi_min, rsi_max, rsi_period, accuracy"""
        if kwargs.get("start_money") is not None:
            self.set_start_money(kwargs.get("start_money"))
        if kwargs.get("buy_increase") is not None:
            self.buy_increase = kwargs.get("buy_increase")
        if kwargs.get("sell_decrease") is not None:
            self.sell_decrease = kwargs.get("sell_decrease")
        if kwargs.get("stop_gain") is not None:
            stop_gain = kwargs.get("stop_gain")
            self.stop_gain = float(f"{stop_gain:.2f}")
        if kwargs.get("stop_loss") is not None:
            stop_loss = kwargs.get("stop_loss")
            self.stop_loss = float(f"{stop_loss:.2f}")
        if kwargs.get("trailing_stop") is not None:
            self.trailing_stop = kwargs.get("trailing_stop")
        if kwargs.get("short") is not None:
            self.short = kwargs.get("short")
        if kwargs.get("long") is not None:
            self.long = kwargs.get("long")
        if kwargs.get("returns") is not None:
            self.returns = kwargs.get("returns")
        if kwargs.get("start_date") is not None:
            self.start_date = kwargs.get("start_date")
        if kwargs.get("end_date") is not None:
            self.end_date = kwargs.get("end_date")
        if kwargs.get("last_update") is not None:
            self.last_update = kwargs.get("last_update")
        if kwargs.get("rsi_min") is not None:
            rsi_min = kwargs.get("rsi_min")
            self.rsi_min = float(f"{rsi_min:.2f}")
        if kwargs.get("rsi_max") is not None:
            rsi_max = kwargs.get("rsi_max")
            self.rsi_max = float(f"{rsi_max:.2f}")
        if kwargs.get("rsi_period") is not None:
            self.rsi_period = kwargs.get("rsi_period")
        if kwargs.get("accuracy") is not None:
            acuracy = kwargs.get("accuracy")
            self.accuracy = float(f"{acuracy:.2f}")

    def set_json(self, jsonsetup, last_update):
        try:
            self.last_update = last_update
            params = json.loads(jsonsetup)
            self.set_strategy(params["strategy"])
            self.set_parameters(returns=params["returns"], start_date=params["start_date"], end_date=params["end_date"],
                                start_money=params["start_money"], buy_increase=params["buy_increase"],
                                sell_decrease=params["sell_decrease"], accuracy=params["accuracy"])
            if str(self.get_strategy()).startswith("RSI"):
                self.set_parameters(rsi_min=params["rsi_min"], rsi_max=params["rsi_max"],
                                    rsi_period=params["rsi_period"])
            else:
                self.set_parameters(stop_gain=params["stop_gain"], stop_loss=params["stop_loss"],
                                    short=params["short"], long=params["long"],
                                    trailing_stop=params["trailing_stop"])
        except KeyError as e:
            raise KeyError(f"Chave {e} faltando.")
        except Exception as e:
            raise e

    def get_json(self):
        try:
            params = {"strategy": self.strategy, "returns": self.returns, "start_date": self.start_date,
                      "end_date": self.end_date, "start_money": self.start_money, "buy_increase": self.buy_increase,
                      "sell_decrease": self.sell_decrease}
            if str(self.get_strategy()).startswith("RSI"):
                params["rsi_min"] = self.rsi_min
                params["rsi_max"] = self.rsi_max
                params["rsi_period"] = self.rsi_period
            else:
                params["short"] = self.short
                params["long"] = self.long
                params["stop_gain"] = self.stop_gain
                params["stop_loss"] = self.stop_loss
                params["trailing_stop"] = self.trailing_stop

            params["accuracy"] = self.accuracy
            jsonfiles = json.dumps(params)

        except Exception:
            raise Exception("Erro ao transformar um objeto Setup em objeto JSON")

        return jsonfiles

    def get_json_ptbr(self):
        jsonfiles = self.get_json()
        json_ptbr = jsonfiles.replace("strategy", "estratégia")
        json_ptbr = json_ptbr.replace("returns", "retorno_%")
        json_ptbr = json_ptbr.replace("start_date", "data_inicial")
        json_ptbr = json_ptbr.replace("end_date", "data_final")
        json_ptbr = json_ptbr.replace("start_money", "saldo_inicial")
        json_ptbr = json_ptbr.replace("buy_increase", "aumento_compra_%")
        json_ptbr = json_ptbr.replace("sell_decrease", "decremento_venda_%")
        json_ptbr = json_ptbr.replace("rsi_min", "ifr_sobrevenda")
        json_ptbr = json_ptbr.replace("rsi_max", "ifr_sobrecompra")
        json_ptbr = json_ptbr.replace("rsi_period", "ifr_períodos")
        json_ptbr = json_ptbr.replace("short", "média_curta")
        json_ptbr = json_ptbr.replace("long", "média_longa")
        json_ptbr = json_ptbr.replace("stop_loss", "parar_perda")
        json_ptbr = json_ptbr.replace("stop_gain", "parar_ganho")
        json_ptbr = json_ptbr.replace("trailing_stop", "stop_móvel")
        json_ptbr = json_ptbr.replace("accuracy", "precisão_%")
        params = json.loads(json_ptbr)
        return params

