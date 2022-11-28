u"""
Classe utilizada para obter os dados das criptomoedas na
exchange Bitfinex inserindo em banco de dados Mysql.
'''
Created on 2021-10-23
Updated on 2021-10-23

@author: Daniel Tell
"""
from datetime import date

import requests
import datetime
import time
import json
import mysql.connector
import mysql.connector as db
from mysql.connector import Error
import algotradingpy.utils.util as util
from algotradingpy.view import console
import algotradingpy.utils.config as config


class DataCollection:

    total_trades = 0
    total_candles = 0
    total_inserts = 0
    exec_hour = datetime.datetime.now()
    start_hour = datetime.datetime.now()
    dict_time_candles = {}
    dict_last_trades = {}
    dict_cid_symbol = {}

    def __init__(self):

        self.db_host = config.get_db_host()
        self.db_user = config.get_db_user()
        self.db_pass = config.get_db_pass()
        self.db_name = config.get_db_name()
        self.db_port = config.get_db_port()
        self.symbols = config.get_symbols()
        self.time_frames = config.get_timeframes()
        for tf in self.time_frames:
            if tf not in util.API_TIME_FRAMES:
                console.show_warning(f"AVISO! O timeframe '{tf}' configurado em config.json é inválido. "
                       f"São aceito apenas estes timeframes: {util.API_TIME_FRAMES}")
        self.start_date = config.get_past()
        self.interval = config.get_interval()
        self.api_limit = config.get_limit()
        self.conn = self.connect()
        self.cursor = self.conn.cursor(buffered=True)
        self.run()

    def connect(self):
        try:
            conn = mysql.connector.connect(host=self.db_host,
                                           database=self.db_name,
                                           user=self.db_user,
                                           password=self.db_pass,
                                           port=self.db_port)
            if conn.is_connected():
                msg = 'Connected to MySQL database at {}'.format(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
                console.show(msg)
            return conn
        except Error as e:
            console.show_error('Não foi possível conectar com o banco de dados, causa:', e)

    def run(self):
        try:
            self.create_tables()
            self.insert_new_coins()
            self.update_coins()
            # obtém o cid e timestamp dos últimos registros de trades de todos os simbolos de config.json
            self.get_all_last_trades()
            # obtém o timestamp últimos registros de candles de todos os simbolos e timeframes vindos de config.json
            self.get_all_last_candles()
            self.print_coins()
            # Execute eternamente o seguinte:
            while True:
                # Percorra cada símbolo do dicionario que está vindo do arquivo de configuração
                try:
                    for symbol, desc in self.symbols.items():
                        symbol = str(symbol).strip()
                        cid = self.dict_cid_symbol[symbol]
                        last_in_trade = self.dict_last_trades[symbol]
                        self.insert_trade(cid, symbol, desc, last_in_trade)
                        # consulta candles para cada timeframe que estiver no arquivo de configuracao
                        for time_frame in self.time_frames:
                            last_in_candle = self.dict_time_candles[str(symbol + time_frame)]
                            self.insert_candle(cid, symbol, desc, time_frame, last_in_candle)
                            time.sleep(self.interval)
                        time.sleep(self.interval)
                except Exception as e:
                    try:
                        if not self.conn.is_connected():
                            console.show_warning('Não conectado com o banco de dados! Tentando reconectar...')
                            self.conn.reconnect()
                    except Exception as e:
                        console.show_error('Falha ao reconectar no banco de dados.', e)

                # Se passou 10 minutos mostre relatório dos inserts até o momento
                if (datetime.datetime.now() - self.exec_hour).seconds > 600:
                    self.print_results()
                    self.exec_hour = datetime.datetime.now()
                time.sleep(1)

        except Error as e:
            console.show_error('Erro no programa principal, causa:', e)

        finally:
            self.conn.close()

    def create_tables(self):
        # Cria as tabelas no MySQL caso elas não existam
        try:
            self.cursor.execute(util.CREATE_TBL_COINS)
            self.cursor.execute(util.CREATE_TBL_TRADES_RAW)
            self.cursor.execute(util.CREATE_TBL_CANDLES_RAW)
        except Error as e:
            console.show_error('Erro ao criar tabela , causa:', e)

    def insert_new_coins(self):
        # Insere as moedas no MySQL e antes de inserir verifique se ela está no dicionario de moedas do arquivo Const.py
        # Consulte todas as moedas na API da Bitfinex
        try:
            r = requests.get(util.API_GET_SYMBOLS)
            response = json.loads(r.text)
        except (json.JSONDecodeError, requests.ConnectionError) as e:
            console.show_error('Erro ao carregar o JSON de Symbols da API, causa:', e)
        # Consulte todas as moedas no BD e verifique se tem a mesma quantidade na exchange
        try:
            self.cursor.execute(util.SELECT_ALL_COINS)
            cursor2 = self.conn.cursor()
            symbols_before = self.cursor.rowcount
            # if cursor.rowcount < len(response):
            # Insere na tabela coins o simbolo da moeda e sua descrição (caso a mesma esteja no dicionario(em Const))
            for symbol in response:
                # Procure o simbolo no dicionario, se encontrar inclui a descrição no argumento da query
                desc = self.symbols[symbol] if symbol in self.symbols else ''
                args = (symbol, desc, 'cryptocurrency')
                cursor2.execute(util.INSERT_TBL_COINS, args)

            self.conn.commit()
            self.cursor.execute(util.SELECT_ALL_COINS)
            if self.cursor.rowcount - symbols_before > 0:
                msg = '{} moedas novas inseridas'.format(self.cursor.rowcount - symbols_before)
                console.show(msg)
        except Error as e:
            console.show_error('Erro ao inserir novas moedas, causa:', e)

    def update_coins(self):
        # Verifica se foram incluidas ou removidas moedas do dicionario
        try:
            row = self.cursor.fetchone()
            cursor2 = self.conn.cursor()
            while row is not None:
                cid = row[0]
                symbol = row[1]
                description = row[2]
                # Se o registro no MySQL estiver com coluna description em branco, mas o simbolo foi incluido no dicionario
                if description == '' and symbol in self.symbols:
                    msg = 'Nova moeda no dicionário detectada: {} : {}, atualizando MySQL...'.format(
                        symbol, self.symbols[symbol])
                    console.show(msg)
                    args = (self.symbols[symbol], cid)
                    # Faça um update da coluna description com o valor correspondente no dicionario
                    cursor2.execute(util.UPDATE_DESCRIPTION_TBL_COINS, args)
                row = self.cursor.fetchone()
        except Error as e:
            console.show_error('Erro ao atualizar moedas do dicionário, causa:', e)

    def insert_trade(self, cid, symbol, description, last_in_trade):
        try:
            # Converta o obj datetime em milisegundos para ser utilizado na API
            start_time = (last_in_trade * 1000) + 1
            end_time = int(time.time() * 1000)
            # Converta o timestamp (last_in_trade) vindo do MySQL para o objeto datetime para mostrar no print
            last_in_trade = datetime.datetime.fromtimestamp(last_in_trade)
            # Busque registros de trades para esse simbolo na API a partir de startTime (coluna lastintrade MySQL)
            #print(str(util.API_GET_TRADES_V2).format(symbol.upper(), self.api_limit, start_time, end_time))
            trades = []
            try:
                r = requests.get(
                    str(util.API_GET_TRADES_V2).format(symbol.upper(), self.api_limit, start_time, end_time))
                if r.status_code != 200:
                    console.debug('{} retornando status {} no request de trade.'.format(description, r.status_code))
                    return False
                trades = json.loads(r.text)
            except (json.JSONDecodeError, requests.ConnectionError) as e:
                console.show_error('Erro ao carregar o JSON de Trades da API, causa:', e)
                return False
            except Exception as e:
                console.show_error('Erro durante execução do request na API.', e)
                return False
            # Verifique se o JSON está vazio ou se atin giu o ratelimit
            if len(trades) == 0:
                console.debug('\033[1;31m{}\033[m sem registros de \033[7;34mtrade\033[m para inserir.'.format(description))
                return False
            elif 'error' in trades:
                msg = 'Atingiu o ratelimit, dormindo por 1 minuto...'
                console.show_warning(msg)
                time.sleep(60)
                return False
            # Com o último registro do JSON converta para obj datetime e armazene na var. endTime para mostrar no print
            end_time_timestamp = trades[len(trades) - 1][1] / 1000
            end_time = datetime.datetime.fromtimestamp(end_time_timestamp)
            console.debug(
                'Inserindo {} registros de \033[7;34mtrades\033[m da moeda \033[7;34m{}\033[m. Período: {} a {}.'.format(
                    len(trades), description, last_in_trade.strftime("%d/%m/%Y %H:%M:%S"),
                    end_time.strftime("%d/%m/%Y %H:%M:%S")))
            # Para cada registro  do JSON insira no MySQL
            cursor2 = self.conn.cursor()
            for trade in trades:
                args = (trade[0], trade[1], trade[3], trade[2],
                        'bitfinex', 'buy' if float(trade[2]) >= 0.0 else 'sell', cid)
                cursor2.execute(util.INSERT_TBL_TRADES, args)
            # Atualize a coluna lastintrade da moeada atual com o timestamp do último registro inserido em trades_raw
            args = (trades[len(trades) - 1][1], cid)
            cursor2.execute(util.UPDATE_LASTINTRADE_TBL_COINS, args)
            self.dict_last_trades[str(symbol)] = end_time_timestamp
            self.total_trades += len(trades)
            self.conn.commit()
        except Error as e:
            console.show_error('Erro ao inserir registros de trades no MySQL, causa:', e)
            raise Exception(e)
        return True

    def insert_candle(self, cid, symbol, description, time_frame, last_in_candle):
        try:
            # Converta o obj datetime em milisegundos para ser utilizado na API
            start_time = (last_in_candle * 1000) + 1
            end_time = int(time.time() * 1000)
            # Converta o timestamp (last_in_candle) vindo do MySQL para o objeto datetime para mostrar no print
            last_in_candle = datetime.datetime.fromtimestamp(last_in_candle)
            #print(str(util.API_GET_CANDLES).format(time_frame, symbol.upper(), self.api_limit, start_time, end_time))
            candles = []
            try:
                r = requests.get(
                    str(util.API_GET_CANDLES).format(time_frame, symbol.upper(), self.api_limit, start_time, end_time))
                if r.status_code != 200:
                    console.debug('{} retornando status {} no request de candle.'.format(description, r.status_code))
                    return False
                candles = json.loads(r.text)
            except (json.JSONDecodeError, requests.ConnectionError) as e:
                console.show_error('Erro ao carregar o JSON de Candles da API, causa:', e)
            except Exception as e:
                console.show_error('Erro durante execução do request na API.', e)
                return False
            # Verifique se o JSON está vazio ou se atingiu o ratelimit
            if len(candles) <= 1:
                console.debug(
                    '\033[1;31m{} - {}\033[m sem registros de \033[7;33mcandles\033[m para inserir.'.format(description, time_frame))
                return False
            elif 'error' in candles:
                msg = 'Atingiu o ratelimit, dormindo por 1 minuto...'
                console.show_warning(msg)
                time.sleep(60)
                return False
            candles = candles[:-1]  # não inserir o último candle, pois não deve estar fechado ainda
            end_time_timestamp = candles[len(candles) - 1][0] / 1000
            end_time = datetime.datetime.fromtimestamp(end_time_timestamp)
            console.debug(
                'Inserindo {} registros de \033[7;33mcandles\033[m da moeda \033[7;33m{}\033[m. Timeframe: {}, '
                'Período: {} a {}.'.format(len(candles), description, time_frame,
                                           last_in_candle.strftime("%d/%m/%Y %H:%M:%S"),
                                           end_time.strftime("%d/%m/%Y %H:%M:%S")))
            cursor2 = self.conn.cursor()
            for candle in candles:
                '''INSERT IGNORE INTO candles_raw (time, open, close, high, low, volume, cid, timeframe) 
                VALUES (SELECT FROM_UNIXTIME(%s * 1000 * 0.001))),%s,%s,%s,%s,%s,%s)'''
                args = (candle[0], candle[1], candle[2], candle[3], candle[4], candle[5], cid, time_frame)
                cursor2.execute(util.INSERT_TBL_CANDLES, args)
            # Atualize a coluna lastincandle da moeada atual com o timestamp do último registro inserido em candles_raw
            args = (candles[len(candles) - 1][0], cid)
            cursor2.execute(util.UPDATE_LASTINCANDLE_TBL_COINS, args)
            self.dict_time_candles[str(symbol + time_frame)] = end_time_timestamp
            self.total_candles += len(candles)
            self.conn.commit()
        except Error as e:
            console.show_error('Erro ao inserir registros de candles no MySQL, causa:', e)
            raise Exception(e)
        return True

    def print_results(self):
        interval = (datetime.datetime.now() - self.exec_hour).seconds // 60
        minutes = (datetime.datetime.now() - self.start_hour).seconds // 3600

        if interval > 0:
            total = self.total_trades + self.total_candles
            console.show('-=' * 40)
            console.show('Resultados em {}:'.format(self.exec_hour.strftime("%d/%m/%Y %H:%M:%S")))
            console.show('{} minutos(s) executando (iniciado em {}).'.format(minutes, self.start_hour.strftime("%d/%m/%Y %H:%M:%S")))
            console.show('{} registros inseridos nos últimos 10 minutos ({}/min).'
                         .format(util.get_readable_number(total - self.total_inserts), util.get_readable_number(
                (total - self.total_inserts) / interval)))
            console.show('Total: {} registros inseridos.'.format(util.get_readable_number(total)))
            self.total_inserts = (self.total_trades + self.total_candles)

    def print_coins(self):
        moedas = ' * '
        col = 0
        for row in self.symbols:
            col += 1
            if col % 4 == 0:
                moedas += row + ' * \n * '
            else:
                moedas += row + ' * '
        console.show('\n' + '-=' * 40)
        console.show('Coletando dados dessa(s) {} moeda(s): \n{}'.format(len(self.symbols), moedas))
        console.show('-=' * 40)

    def get_all_last_trades(self):
        deleted_symbols = []
        try:
            console.show('Consultando últimos registros de trades no MySQL...')
            past = datetime.datetime.strptime(self.start_date, '%Y-%m-%d %H:%M:%S')
            past = int(past.timestamp())
            for symbol in self.symbols:
                symbol = str(symbol).strip()  # remover espaços
                args = (symbol, 'cryptocurrency')
                try:
                    cursor2 = self.conn.cursor(buffered=True)
                    cursor2.execute(util.SELECT_LAST_IN_TRADE, args)
                    row_last_in_trade = cursor2.fetchone()
                    if row_last_in_trade:
                        last_inserted_trade = int(row_last_in_trade[1].timestamp())
                        if last_inserted_trade < past:
                            last_inserted_trade = past

                        #console.debug(f"Obtendo último timestamp trade de {symbol} = {last_inserted_trade}")
                        self.dict_cid_symbol[str(symbol)] = row_last_in_trade[0]
                        self.dict_last_trades[str(symbol)] = last_inserted_trade
                    else:
                        console.show_warning(f"{symbol} não foi encontrado e será removido da lista de símbolos.")
                        deleted_symbols.append(symbol)
                except Exception as e:
                    console.show_error(f"Erro ao consultar data e hora do último trade de símbolo '{symbol}' "
                                 f"no banco de dados.", e)

            for symbol in deleted_symbols:
                del self.symbols[symbol]
            console.show('Últimos registros de trades foram carregados com sucesso')

        except Exception as e:
            console.show_error('Erro ao consultar data e hora do último trade no banco de dados.', e)

    def get_all_last_candles(self):
        try:
            console.show('Consultando últimos registros de candles no MySQL...')
            past = datetime.datetime.strptime(self.start_date, '%Y-%m-%d %H:%M:%S')
            past = int(past.timestamp())
            for symbol in self.symbols:
                symbol = str(symbol).strip()  # remover espaços
                for time_frame in self.time_frames:
                    time_frame = str(time_frame).strip()  # remover espaços
                    args = (past, symbol, time_frame)
                    try:
                        cursor2 = self.conn.cursor(buffered=True)
                        cursor2.execute(util.SELECT_LAST_IN_CANDLE, args)
                        row_last_in_candle = cursor2.fetchone()
                        #console.debug(f"Obtendo último timestamp candle de {symbol} - {time_frame} = {row_last_in_candle[0]}")
                        self.dict_time_candles[str(symbol + time_frame)] = row_last_in_candle[0]
                    except Exception as e:
                        console.show_error(f"Erro ao consultar data e hora do último candle de símbolo '{symbol}' "
                                     f"e timeframe '{time_frame}' no banco de dados.", e)

            console.show('Últimos registros de candles foram carregados com sucesso')

        except Exception as e:
            console.show_error(f"Erro ao consultar data e hora do último candle no banco de dados.", e)

