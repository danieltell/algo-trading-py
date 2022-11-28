#!/usr/bin/env python
# -*- coding: utf-8 -*-
u"""
Description: Classe para realizar testes de simulação com backtest.
File name: test_backtest.py
Author: Daniel Tell <daniel.tell@gmail.com>
Date created: 2021-12-11
Date last modified: 2022-10-05
"""

from datetime import datetime, timedelta
from algotradingpy.controller.backtest import BackTest
from algotradingpy.model.btresult import BacktestResult
from algotradingpy.controller.data import Mysql
from algotradingpy.model.setup import Setup
import algotradingpy.utils.config as config
import algotradingpy.view.console as console
import algotradingpy.utils.util as util

back_test_days = 10
symbol = "xrpusd"
time_frame = '15m'
start_money = 500
buy_increase = 0.1
sell_decrease = -0.1
stop_loss = -2.5
stop_gain = 3.0
trailing_stop = False
short = 9
long = 15

console.log_level = config.get_loglevel()


def test_updated_signal(asset, strategy, test_number):
    assert strategy in util.STRATEGIES

    console.show(f"TESTE #{test_number}: verificando se a atualização dos candles atualizou também os sinais. "
                  f"Estratégia de backtest: {strategy}")

    setup = Setup(strategy=strategy, start_money=start_money, short=short, long=long, stop_loss=stop_loss,
                  stop_gain=stop_gain, trailing_stop=trailing_stop, buy_increase=buy_increase,
                  sell_decrease=sell_decrease)

    index = asset.candles.tail(1).index.strftime("%Y-%m-%d %H:%M:%S")[0]
    last_date = datetime.strptime(index, "%Y-%m-%d %H:%M:%S")
    end_date = last_date - timedelta(days=1)
    start_date = end_date - timedelta(back_test_days)
    asset = data.get_candles(symbol=asset.symbol, time_frame=asset.time_frame, start_date=start_date, end_date=end_date)

    console.show(end_date)
    backtest = BackTest(asset, setup, back_test_days)

    json_before = backtest.get_json_signal()
    backtest.asset = data.update(backtest.asset)
    backtest.update()
    json_after = backtest.get_json_signal()
    assert json_after != json_before
    console.show(f"OK! Os sinais foram atualizados. Tamanho json anterior {len(json_before)}, "
                  f"Tamanho json atual: {len(json_after)}")

    console.show("")


def test_strategy_crossing_ma(asset, setup, strategy, test_number):
    assert strategy in util.STRATEGIES

    console.show(f"TESTE #{test_number}: realizando backetst com estratégia {strategy} para {symbol} ({time_frame})...")

    if setup is None:
        setup = Setup(strategy=strategy, start_money=start_money, short=short, long=long, stop_loss=stop_loss,
                      stop_gain=stop_gain, trailing_stop=trailing_stop, buy_increase=buy_increase,
                      sell_decrease=sell_decrease)

    backtest = BackTest(asset, setup, back_test_days)
    assert isinstance(backtest.bt_result, BacktestResult)

    console.show("-" * 60)
    console.show(
        f"Retorno trade {backtest.bt_result.get_trade_returns():.2f}%, "
        f"buy_hold {backtest.bt_result.get_buy_and_hold_returns():.2f}%; "
        f"Precisão: {backtest.bt_result.get_accuracy():.2f}% ")
    console.show("-" * 60)
    console.show("")


def test_strategy_rsi_min_max(asset, strategy, test_number):
    assert strategy in util.STRATEGIES

    console.show(f"TESTE #{test_number}: realizando backetst com estratégia {strategy} para {symbol} ({time_frame})...")
    setup = Setup(strategy=strategy, start_money=start_money, buy_increase=buy_increase, sell_decrease=sell_decrease,
                  rsi_min=30, rsi_max=70, rsi_period=14)

    assert setup.rsi_min == 30
    assert setup.rsi_max == 70
    assert setup.rsi_period == 14

    backtest = BackTest(asset, setup, back_test_days)
    assert isinstance(backtest.bt_result, BacktestResult)

    console.show("-" * 60)
    console.show(
        f"Retorno trade {backtest.bt_result.get_trade_returns():.2f}%, "
        f"buy_hold {backtest.bt_result.get_buy_and_hold_returns():.2f}%; "
        f"Precisão: {backtest.bt_result.get_accuracy():.2f}% ")
    console.show(
        f"Último sinal: {backtest.get_json_signal(False, 1)}")
    console.show("-" * 60)
    console.show("")


def test_backtest_not_changed(test_number):
    asset_xrp = data.get_candles(symbol="xrpusd", time_frame="15m", start_date="2020-09-25", end_date="2020-09-30")
    console.show(f"TESTE #{test_number}: validando se todas funções de backtesting não foram modificadas "
                 f"{symbol} ({time_frame}) com os dados do período de 25/09/2020 a 30/09/2020..")

    setup = Setup(strategy="MAxMA", start_money=500, short=4, long=9, stop_loss=-2.5, stop_gain=2, trailing_stop=False,
                  buy_increase=0.1, sell_decrease=-0.1)
    backtest = BackTest(asset_xrp, setup, 5)
    assert backtest.bt_result.get_trade_returns() == 1.48  # 3.94 (indicators.calc_sma/calc_ema -->  min_periods=1)

    setup = Setup(strategy="MAxPrice", start_money=500, short=6, stop_loss=-2.2, stop_gain=1.4, trailing_stop=False,
                  buy_increase=0.1, sell_decrease=-0.1)
    asset_xrp.updated = True
    backtest = BackTest(asset_xrp, setup, 5)
    assert backtest.bt_result.get_trade_returns() == 1.63# 6.82(utilizando média móvel curta simples(sma))

    setup = Setup(strategy="RSI_Min_Max", start_money=500, rsi_min=30, rsi_max=70, rsi_period=14, buy_increase=0.1,
                  sell_decrease=-0.1)
    asset_xrp.updated = True
    backtest = BackTest(asset_xrp, setup, 5)
    assert backtest.bt_result.get_trade_returns() == 1.635

    setup = Setup(strategy="RSI_Quartiles", start_money=500, rsi_period=14, buy_increase=0.1,
                  sell_decrease=-0.1)
    asset_xrp.updated = True
    backtest = BackTest(asset_xrp, setup, 5)
    assert backtest.bt_result.get_trade_returns() == 0.705

    setup = Setup(strategy="RSI_Outliers", start_money=500, rsi_period=14, buy_increase=0.1,
                  sell_decrease=-0.1)
    asset_xrp.updated = True
    backtest = BackTest(asset_xrp, setup, 5)
    assert backtest.bt_result.get_trade_returns() == -0.291

    setup = Setup(strategy="RSI_AVG", start_money=500, rsi_period=14, buy_increase=0.1,
                  sell_decrease=-0.1)
    asset_xrp.updated = True
    backtest = BackTest(asset_xrp, setup, 5)
    assert backtest.bt_result.get_trade_returns() == 3.173

    console.show(f"OK! Retornou o esperado em todos os backtests.")
    console.show("")


if __name__ == "__main__":
    data = Mysql(db_host=config.get_db_host(), db_port=config.get_db_port(), db_user=config.get_db_user(),
                 db_pass=config.get_db_pass(), db_name=config.get_db_name())

    asset = data.get_candles_days(symbol=symbol, time_frame=time_frame, days=back_test_days)

    console.show("")
    console.show(f"TESTE #1: Valida se conseguiu instanciar o objeto Asset.")
    assert asset is not None
    console.show(f"OK! Asset foi instanciado com {len(asset.candles)} registros.")
    console.show("")
    #test_backtest_not_changed(2)
    asset.updated = True
    test_strategy_crossing_ma(asset, None, "MAxMA", 3)
    #setup = data.get_setup(symbol, time_frame)
    #console.show(setup.get_json_ptbr())
    asset.updated = True
    test_strategy_crossing_ma(asset, None, "MAxPrice", 4)
    asset.updated = True
    test_strategy_rsi_min_max(asset, "RSI_Min_Max", 5)
    asset.updated = True
    test_strategy_rsi_min_max(asset, "RSI_Quartiles", 6)
    asset.updated = True
    test_strategy_rsi_min_max(asset, "RSI_Outliers", 7)
    asset.updated = True
    test_strategy_rsi_min_max(asset, "RSI_AVG", 8)
    asset.updated = True
    test_updated_signal(asset, "MAxMA", 9)




