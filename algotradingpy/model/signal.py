
u"""
Created on 2022-02-28
Updated on 2022-02-28

@author: Daniel Tell
"""


class Signal:

    def __init__(self):
        self.last_id = 0
        self.signals = []

    def insert_signal(self, date, price, action, strategy, obs="", rsi=None):
        r"""Insere um sinal na lista com identificador único.

        :param str date: data que o sinal foi detectado
        :param float price: preço do ativo no momento do sinal
        :param int action: indica se o sinal é: compra (1), venda (-1) ou neutro(0)
        :param str strategy: tipo de estratégia executada no backtest que gerou o sinal (MAxMA, RSI_Min_Max, etc)
        :param str obs: observação opcional sobre o detectado
        :param float rsi: indice RSI do sinal, opcional e usado somente quando a estratégia for RSI
        :return: True se conseguiu inserir ou False se o registro já existe
        :rtype bool
        """
        for signal in self.signals:
            if signal["date"] == date and signal["strategy"] == strategy:
                return False
        self.last_id += 1
        signal = {"id": self.last_id,
                  "date": date,
                  "price": price,
                  "action": action,
                  "strategy": strategy,
                  "obs": obs,
                  "rsi": rsi
                  }
        self.signals.append(signal)

        return True

    def get_signals(self) -> list:
        return self.signals
