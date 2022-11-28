#!/usr/bin/env python
# -*- coding: utf-8 -*-
u"""
Created on 2021-12-11
Updated on 2021-12-11

@author: Daniel Tell
"""
from algotradingpy.controller.data import Mysql
import algotradingpy.utils.config as config
import algotradingpy.view.console as console

back_test_days = 5
symbol = 'xrpusd'
time_frame = '15m'
console.log_level = config.get_loglevel()


def test_run(main=False):
    data = Mysql(db_host=config.get_db_host(), db_port=config.get_db_port(), db_user=config.get_db_user(),
                 db_pass=config.get_db_pass(), db_name=config.get_db_name())
    asset = data.get_candles_days(symbol=symbol, time_frame=time_frame, days=7)
    assert asset is not None
    #console.debug(f'Dados da moeda {asset.description}')
    #console.debug(asset.get_json_data())


if __name__ == '__main__':
    test_run(main=True)
