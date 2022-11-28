# -*- coding: utf-8 -*-
u"""
Description: módulo com constantes e métodos úteis para ser utilizado em toda a biblioteca.
File name: util.py
Author: Daniel Tell <daniel.tell@gmail.com>
Date created: 03/10/2021
Date last modified: 30/09/2022
"""

import math
import os
from distutils.util import strtobool

# Instruções Create SQL para todas as tabelas necessárias
CREATE_TBL_COINS = '''CREATE TABLE IF NOT EXISTS coins(
    cid SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    symbol VARCHAR(10) NOT NULL,
    description VARCHAR(30) NOT NULL COMMENT 'Descrição detalhada para cada simbolo. Ex.: Bitcoin/US Dólar',
    type ENUM('cryptocurrency', 'stockmarket') NOT NULL COMMENT 'O tipo de ativo (criptomoeda ou ações)',
    lastintrade timestamp NOT NULL COMMENT 'Data e hora do último registro do simbolo na tabela trades_raw',
    lastincandle timestamp NOT NULL COMMENT 'Data e hora do último registro do simbolo na tabela candles_raw',
    PRIMARY KEY (cid), 
    UNIQUE KEY unique_symbol (symbol)
    )ENGINE=MyISAM;'''

CREATE_TBL_TRADES_RAW = '''CREATE TABLE IF NOT EXISTS trades_raw(
    tid INT NOT NULL COMMENT 'Identificador da transação',
    time timestamp NOT NULL COMMENT 'Data e hora da transação',
    amount DECIMAL(16,8) NOT NULL COMMENT 'How much was bought (positive) or sold (negative)',
    price DECIMAL(19,5) NOT NULL COMMENT 'Price at which the trade was executed',
    exchange ENUM('bitfinex', 'null', ''),
    type ENUM('sell', 'buy', '') NOT NULL COMMENT 'sell or buy (can be '' if undetermined)',
    cid SMALLINT NOT NULL,
    created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX (time, type, cid),
    PRIMARY KEY (tid)
    ) ENGINE=MyISAM;'''

CREATE_TBL_CANDLES_RAW = '''CREATE TABLE IF NOT EXISTS candles_raw(
    time timestamp NOT NULL,
    open FLOAT NOT NULL COMMENT 'First execution during the time frame',
    close FLOAT NOT NULL COMMENT 'Last execution during the time frame',
    high FLOAT NOT NULL  COMMENT 'Highest execution during the time frame',
    low FLOAT NOT NULL COMMENT 'Lowest execution during the timeframe',
    volume FLOAT NOT NULL COMMENT 'Quantity of symbol traded within the timeframe',
    cid SMALLINT NOT NULL COMMENT 'Chave do symbol na tabela coins',
    timeframe ENUM('1m', '5m', '15m', '30m', '1h', '3h', '6h', '12h', '1D', '7D', '14D', '1M') CHARACTER SET latin1 COLLATE latin1_general_cs NOT NULL,
    created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX (cid, timeframe),
    PRIMARY KEY (time, cid, timeframe)
    ) ENGINE=MyISAM;'''

CREATE_TBL_SETUPS = '''CREATE TABLE IF NOT EXISTS setups(
    id INT NOT NULL AUTO_INCREMENT COMMENT 'Identificador único do Setup',
    cid SMALLINT NOT NULL COMMENT 'Identificador da moeda',
    timeframe ENUM('1m', '5m', '15m', '30m', '1h', '3h', '6h', '12h', '1D', '7D', '14D', '1M') CHARACTER SET latin1 COLLATE latin1_general_cs NOT NULL,  
    startdate DATE NOT NULL COMMENT 'Data inicial do período que foi feita a simulação.', 
    enddate DATE NOT NULL COMMENT 'Data final do período que foi feita a simulação.', 
    returns FLOAT NOT NULL COMMENT 'Retorno (em porcentagem) que este setup obteve durante o backtest',
    jsonsetup VARCHAR(500) NOT NULL COMMENT 'Objeto JSON que representa um objeto Setup', 
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp NULL,
    INDEX(cid, timeframe, deleted_at),
    PRIMARY KEY (id)
    )ENGINE=InnoDB;'''

CREATE_TABLES = {"coins": CREATE_TBL_COINS, "candles_raw": CREATE_TBL_CANDLES_RAW, "trades_raw" : CREATE_TBL_TRADES_RAW,
                 "setups": CREATE_TBL_SETUPS}

# Número máximo de registros
API_TIME_FRAMES = ('1m', '5m', '15m', '30m', '1h', '3h', '6h', '12h', '1D', '1W', '14D', '1M')
API_GET_SYMBOLS = 'https://api.bitfinex.com/v1/symbols'
API_GET_TRADES_V1 = 'https://api.bitfinex.com/v1/trades/{}?limit_trades={}&type=buy&timestamp={}'
API_GET_TRADES_V2 = 'https://api-pub.bitfinex.com/v2/trades/t{}/hist?limit={}&start={}&end={}&sort=1'
API_GET_CANDLES = 'https://api.bitfinex.com/v2/candles/trade:{}:t{}/hist?limit={}&start={}&end={}&sort=1'

# Instruções Insert SQL
INSERT_TBL_COINS = '''INSERT IGNORE INTO coins (symbol, description, type, lastintrade, lastincandle) 
    VALUES (%s,%s, %s, (SELECT FROM_UNIXTIME(1)), (SELECT FROM_UNIXTIME(1)))'''
INSERT_TBL_TRADES= '''INSERT IGNORE INTO trades_raw (tid, time, price, amount, exchange, type, cid)  
    VALUES (%s,(SELECT FROM_UNIXTIME(%s  * 0.001)),%s,%s,%s,%s,%s)'''
INSERT_TBL_CANDLES = '''INSERT IGNORE INTO candles_raw (time, open, close, high, low, volume, cid, timeframe) 
    VALUES ( (SELECT FROM_UNIXTIME(%s * 0.001)),%s, %s, %s, %s, %s, %s, %s)'''

# Instruções Update SQL
UPDATE_DESCRIPTION_TBL_COINS = 'UPDATE coins SET description=%s WHERE cid = %s'
UPDATE_LASTINTRADE_TBL_COINS = 'UPDATE coins SET lastintrade=(SELECT FROM_UNIXTIME(%s * 0.001)) WHERE cid = %s'
UPDATE_LASTINCANDLE_TBL_COINS = 'UPDATE coins SET lastincandle=(SELECT FROM_UNIXTIME(%s * 0.001)) WHERE cid = %s'

# Consultas SQL
SELECT_ALL_COINS = "SELECT cid, symbol, description FROM coins WHERE type='cryptocurrency' "
SELECT_LAST_IN_CANDLE = "SELECT IFNULL(Max( UNIX_TIMESTAMP(time)), %s) FROM candles_raw " \
                        "WHERE cid = (SELECT cid FROM coins WHERE symbol = %s LIMIT 1) AND timeframe = %s "
SELECT_LAST_IN_TRADE = "SELECT cid, lastintrade FROM coins WHERE symbol = %s AND type = %s LIMIT 1"

# Configurações gerais
STRATEGIES = {"MAxMA": 1, "MAxPrice": 2, "RSI_Min_Max": 3, "RSI_Quartiles": 4, "RSI_Outliers": 5, "RSI_AVG": 6}
#KIND = {"Short_MA": 1, "Long_MA": 2, "RSI_Min_Max": 3, "RSI_Quartiles": 4, "RSI_Outliers": 5, "RSI_AVG": 6}


def get_readable_number(n):
    r"""Escreve o valor de um número em número por extenso.

    :param n: número
    :return: número por extenso.
    :rtype: str
    """
    millnames = ['', ' mil', ' milhões', ' bilhões']
    n = float(n)
    millidx = max(0, min(len(millnames)-1, int(math.floor(0 if n == 0 else math.log10(abs(n))/3))))
    return '{:.1f}{}'.format(n / 10**(3 * millidx), millnames[millidx])


def get_config_path_default():
    r"""Escreve o valor de um número em número por extenso.

        :return: diretório padrão.
        :rtype: str
        """
    user_home = os.getenv("HOME")
    if user_home is None:
        return os.path.abspath("./")
    else:
        return f'{user_home}/.AlgoTradingPy/'


def is_valid_numbers(value):
    if str(value).isdecimal() or str(value).isdigit():
        return True
    else:
        return False


def convert_bool(value):
    try:
        return bool(strtobool(str(value)))
    except:
        return False

