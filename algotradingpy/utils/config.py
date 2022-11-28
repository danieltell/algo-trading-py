#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
u"""
Description: Módulo para tratar as configurações
File name: config.py
Author: Daniel Tell <daniel.tell@gmail.com>
Created on 2022-09-18
Updated on 2022-09-18
"""

import os
import json
import algotradingpy.view.console as console
import algotradingpy.utils.util as util

config_example = '''{
   "Geral":{
      "loglevel":"debug"
   },
   "Coleta":{
      "symbols":{
         "btcusd":"Bitcoin/US Dólar",
         "btgusd":"Bitcoin Gold/US Dólar",
         "babusd":"Bitcoin Cash/US Dólar",
         "xrpusd":"Ripple/US Dólar",
         "neousd":"NEO/US Dólar",
         "ethusd":"Etherium/US Dólar",
         "iotusd":"IOTA/US Dólar",
         "xmrusd":"Monero/US Dólar",
         "ltcusd":"Litecoin/US Dólar",
         "dshusd":"Dash/US Dólar",
         "zecusd":"Zcash/US Dólar",
         "eosusd":"EOS/US Dólar",
         "trxusd":"TRON/US Dólar"
      },
      "timeframes": ["1m", "5m", "15m", "30m", "1h", "3h", "6h", "12h", "1D", "7D", "14D", "1M"],
      "limit": 5000,
      "interval": 10,
      "past": "2022-01-01 00:00:00"
   },
   "Banco":{
      "host":"",
      "port":3306,
      "username":"",
      "password":"",
      "database":""
   }
}'''

file = "config.json"
config = None
json_file = None


def set_file(config_file):
    global config, file, json_file
    file = config_file
    try:
        if not os.path.exists(config_file):
            with open(config_file, "w") as json_file:
                json_file.write(config_example)
                console.show_warning(
                    f'O arquivo de configuração \"{os.path.abspath(config_file)}\" não existia e foi criado. '
                    f'Por favor abra e edite este arquivo.')
                json_file.close()
        else:
            with open(config_file, "r") as json_file:
                config = json.load(json_file)

    except Exception as e:
        console.show_error("Erro: o arquivo \"{}\" não pode ser lido e nem criado.".format(config_file), e)


def get_conf_file_default():
    global file
    conf_path = util.get_config_path_default()
    return f'{conf_path}/{file}'


def get_loglevel():
    return __get_config('Geral', 'loglevel')


def get_symbols():
    return __get_config('Coleta', 'symbols')


def get_timeframes():
    return __get_config('Coleta', 'timeframes')


def get_past():
    return __get_config('Coleta', 'past')


def get_limit():
    return __get_config('Coleta', 'limit')


def get_interval() -> int:
    try:
        return int(__get_config('Coleta', 'interval'))
    except:
        console.show_error("Valor {} em 'interval' na configuração deve ser um número. Por favor corrija.".
                             format(__get_config('Coleta', 'interval')))


def get_db_host():
    return __get_config('Banco', 'host')


def get_db_user():
    return __get_config('Banco', 'username')


def get_db_pass():
    return __get_config('Banco', 'password')


def get_db_port() -> int:
    try:
        return int(__get_config('Banco', 'port'))
    except:
        console.show_error("Valor {} em 'port' na configuração deve ser um número. Por favor corrija.".
                           format(__get_config('Banco', 'port')))


def get_db_name():
    return __get_config('Banco', 'database')


def __get_config(section, subsection) :
    if config is None:
        set_file(file)
    try:
        return config[section][subsection]
    except Exception as e:
        console.show_error(f"Erro ao carregar configuração de '{section}': '{subsection}'", e)
        return ""
