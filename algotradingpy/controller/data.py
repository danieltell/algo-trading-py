# -*- coding: utf-8 -*-
u"""
Description: Módulo com classes que vão controlar o carregamento dos dados do banco de dados.
File name: data.py
Author: Daniel Tell <daniel.tell@gmail.com>
Date created: 19/09/2022
Date last modified: 30/09/2022
"""
import mysql.connector as db
from mysql.connector import pooling
import algotradingpy.view.console as console
import pandas as pd
from algotradingpy.model.asset import Asset
from algotradingpy.model.setup import Setup
from datetime import datetime, timedelta
import algotradingpy.utils.util as util


class Mysql:
    connection_pool: db.pooling.MySQLConnectionPool = None

    def __init__(self, db_host, db_user, db_pass, db_name, db_port=3306):
        r"""Classe para gerenciar dados de um banco Mysql.

        :param str db_host: endereço do banco de dados
        :param str db_user: usuário do banco
        :param str db_pass: senha do usuário
        :param str db_name: nome da base de dados
        :param int db_port: porta do banco de dados
        """
        self.db_host = db_host
        self.db_user = db_user
        self.db_pass = db_pass
        self.db_name = db_name
        self.db_port = db_port
        self.create_mysql_pool()
        # self.conn = self.connect_mysql()

    def create_mysql_pool(self, pool_size=32):
        r"""Cria uma pool de conexões com o banco de dados a armazena no atributo connection_pool.

         :param int pool_size: tamanho de pool é um número de objetos de conexão que o pool pode suportar
         :return: True se consegui criar ou False se não
         :rtype: bool
         """
        try:
            self.connection_pool = db.pooling.MySQLConnectionPool(pool_name="mysql_pool",
                                                                            pool_size=pool_size,
                                                                            pool_reset_session=True,
                                                                            host=self.db_host,
                                                                            port=self.db_port,
                                                                            database=self.db_name,
                                                                            user=self.db_user,
                                                                            password=self.db_pass)
            return True
        except db.Error as e:
            console.show_error("Não foi possível criar pool de conexoes com o banco de dados.", e)
            # raise e
            return False

    def get_mysql_conn(self):
        r"""Obtém uma conexão MySQL da pool de conexões com o banco de dados,"""
        if self.connection_pool is not None:
            try:
                conn = self.connection_pool.get_connection()

                if conn.is_connected():
                    db_Info = conn.get_server_info()
                    date_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    console.debug(
                        f"Conectou com o banco de dados MySQL usando pool em {date_time}. Versão MySQL: {db_Info}")
                return conn
            except db.Error as e:
                console.show_error("Erro ao conectar ao banco de dados MySQL usando pool de conexão.", e)
                # raise e

    def _select(self, query, args=None):
        r"""Faz uma consulta (select) no banco de dados MySQL e retorna
            uma tupla com nomes das colunas e rows.

            :param str query: uma consulta ao banco na sintaxe MySQL
            :return: (column_names, rows)
            :rtype: tuple
            """
        try:
            conn = self.get_mysql_conn()
            if not conn.is_connected():
                conn.reconnect()
            cursor = conn.cursor(buffered=True)
            cursor.execute(query, args)
            return cursor.column_names, cursor.fetchall()
        except db.Error as e:
            raise db.Error(e.msg)
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def _execute(self, stmt, args):
        r"""Faz uma operação de insert/update/delete no banco de dados MySQL.

            :param str stmt: um statement SQL para ser exccutado
            :param tuple args: argumentos para ser passadoo ao statement
            :return: número de registros afetados pela operação
            :rtype: int
            """
        try:
            conn = self.get_mysql_conn()
            if not conn.is_connected():
                conn.reconnect()
            cursor = conn.cursor()
            cursor.execute(stmt, args)
            conn.commit()
            return cursor.rowcount
        except db.Error as e:
            raise db.Error(e.msg)
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def get_symbols(self, with_data_only=True):
        r"""Obtém um DataFrame com todos os simbolos que estão na tabela 'coins' se with_data_only=False,
            ou somente símbolos que tem dados cadastrados na tabela de candles.

           :param bool with_data_only: filtra apenas símbolos cujo dados estão no banco
           :return: um DataFrame contendo relação de símbolos, descrição, data_ultimo_candle, timeframes
           :rtype: pd.DataFrame
           """
        try:
            console.debug("Consultando dados de todos símbolos disponíveis...")
            query = "SELECT symbol, description, type FROM coins ORDER BY cid"
            if with_data_only:
                query = '''SELECT c.symbol, c.description, c.lastincandle, cr.timeframes FROM coins c INNER JOIN
                        (SELECT cr.cid, group_concat(DISTINCT cr.timeframe) as timeframes FROM candles_raw cr GROUP BY cr.cid
                        ORDER BY cr.timeframe ASC) cr ON c.cid = cr.cid'''

            column_names, rows = self._select(query)
            df_symbols = pd.DataFrame(rows)
            if df_symbols.empty:
                console.debug("Sem registros de símbolos no banco de dados!")
            else:
                console.debug(f"{len(df_symbols)} registros retornados")
            df_symbols.columns = column_names
            return df_symbols
        except Exception as e:
            console.show_error("Erro ao consultar os símbolos no banco de dados", e)

    def get_candles(self, symbol, time_frame, start_date, end_date) -> Asset:
        r"""Obtém um Asset com dados de candlestick com períodos de 'time_frame' e entre 'start_date' e 'end_date',

           :param str symbol: símbolo do ativo que possui dados de candlestick
           :param str time_frame: período de tempo de cada candlestick (1m, 5m, 15m, etc)
           :param start_date: data inicial dos registros de candles_raw
           :param end_date: data final dos registros de candles_raw
           :return: um objeto Asset de type='candlestick' ou None se não encontrar registros
           :rtype: Asset
           """
        try:
            console.debug(f"Consultando dados de candlestick (intervalos de {time_frame}) para {symbol} "
                          f"no período de {start_date} até {end_date}...")
            query = """SELECT c.description, cr.time, cr.open, cr.close, cr.low, cr.high, cr.volume
                      FROM candles_raw cr, coins c WHERE c.cid = cr.cid AND c.symbol = %(symbol)s 
                      AND cr.time BETWEEN %(start_date)s AND %(end_date)s AND cr.timeframe = %(time_frame)s 
                      ORDER BY cr.time ASC """
            args = {'symbol': symbol, 'time_frame': time_frame, 'start_date': start_date, 'end_date': end_date}
            column_names, rows = self._select(query, args)
            df_candlestick = pd.DataFrame(rows)
            if df_candlestick.empty:
                console.debug("Sem registros no período!")
                return None
            else:
                console.debug(f"{len(df_candlestick)} registros retornados")
            df_candlestick.columns = column_names
            description = df_candlestick['description'].head(1)
            description = description[0]
            del df_candlestick['description']
            df_candlestick.set_index("time", inplace=True)
            asset = Asset(ptype="candlestick", symbol=symbol, time_frame=time_frame, description=description,
                          data=df_candlestick)
            return asset

        except Exception as e:
            console.show_error("Erro ao consultar dados de candlestick no banco de dados", e)

    def get_trades(self, symbol, start_date, end_date):
        r"""Obtém um Asset com dados de trades entre 'start_date' e 'end_date',

          :param str symbol: símbolo do ativo que possui dados de trade
          :param start_date: data inicial dos registros de trades_raw
          :param end_date: data final dos registros de trades_raw
          :return: um objeto Asset de dtype='trade' ou None se não encontrar registros
          :rtype: Asset
          """
        try:
            console.debug(f"Consultando dados de trade para {symbol} no período de {start_date} até {end_date}...")
            query = f"""SELECT c.description, tr.time, amount, price, type 
                   FROM trades_raw tr, coins c WHERE c.cid = tr. cid AND c.symbol = %(symbol)s 
                   AND tr.time BETWEEN %(start_date)s AND %(end_date)s  
                   ORDER BY tr.time ASC """
            args = {'symbol': symbol, 'start_date': start_date, 'end_date': end_date}
            column_names, rows = self._select(query, args)
            df_trade = pd.DataFrame(rows)
            if df_trade.empty:
                console.debug("Sem registros no período!")
                return None
            else:
                console.debug(f"{len(df_trade)} registros retornados")
            df_trade.columns = column_names
            description = df_trade['description'].head(1)
            description = description[0]
            del df_trade['description']
            df_trade.set_index("time", inplace=True)
            asset = Asset(ptype="trade", symbol=symbol, time_frame=None, description=description,
                          data=df_trade)
            return asset

        except Exception as e:
            console.show_error("Erro ao consultar dados de trade no banco de dados", e)

    def update(self, asset, days_to_keep=15):
        r"""Obtém um Assset com dados atualizados de candles/trades (dependendo de 'dtype' de 'asset'), Remove os 
        registros que forem anterioes a (end_date - days_to_keep)

         :param Asset asset: objeto Asset que será atualizado
         :param int days_to_keep: quantidade de dias que devem ser mantidos os registros
         :return: um objeto Assset com dados atualizados de candles/trades
         :rtype: Asset
         """
        if asset.get_type() == "candlestick":
            console.debug(f"Atualizando dados de candlestick de {asset.symbol} com intervalos de {asset.time_frame}...")
            index = asset.candles.tail(1).index.strftime('%Y-%m-%d %H:%M:%S')[0]  # último indice do DataFrame candles
            last_date = datetime.strptime(index, '%Y-%m-%d %H:%M:%S')
            start = last_date + timedelta(seconds=30)  # e adicona + 30 segundos
            end = datetime.now()
            updated_asset = self.get_candles(start_date=start, end_date=end, symbol=asset.symbol,
                                             time_frame=asset.time_frame)
            size_before = len(asset.candles)
            if updated_asset is not None:
                asset.candles = asset.candles.append(updated_asset.candles)
                asset.last_update = end
                asset.updated = True
                index = asset.candles.tail(1).index.strftime('%Y-%m-%d %H:%M:%S')[0]  # último indice do DataFrame candles
                last_date = datetime.strptime(index, '%Y-%m-%d %H:%M:%S')
                size_after = len(asset.candles)
                start = last_date - timedelta(days=days_to_keep)  # subtrair "days_to_keep" dias
                asset.candles = asset.candles.loc[start: last_date, :]

                console.debug(f"{size_after - len(asset.candles)} registros antigos foram removidos "
                              f"e {size_after - size_before} novos foram inseridos.")
            else:
                console.debug("Não existem novos dados de candlestick para atualizar.")
        return asset

    def get_setup(self,  symbol, time_frame):
        r"""Obtém um Asset com dados de candlestick com períodos de 'time_frame' e entre 'start_date' e 'end_date',

          :param str symbol: símbolo do ativo que possui dados de candlestick
          :param str time_frame: período de tempo de cada candlestick (1m, 5m, 15m, etc)
          :return: um objeto Setup ou None se não encontrar o registro no banco
          :rtype: Setup
          """
        setup = None
        try:
            console.debug(f"Consultando setup de {symbol} no timeframe de {time_frame} no banco de dados ...")
            query = f"""SELECT jsonsetup, created_at
                      FROM setups s, coins c WHERE c.cid = s.cid AND c.symbol = %(symbol)s 
                      AND s.timeframe = %(time_frame)s AND s.deleted_at IS NULL;"""
            args = {'symbol': symbol, 'time_frame': time_frame}
            column_names, rows = self._select(query, args)
            for row in rows:
                jsonsetup = row[0]
                created_at = row[1]
                setup = Setup(strategy="MAxMA", start_money=1, short=0, long=0, stop_loss=0, stop_gain=0,
                              trailing_stop=False)
                try:
                    setup.set_json(jsonsetup, last_update=created_at)
                except Exception as e:
                    console.show_error(f"Impossível carregar JSON de Setup de {symbol}, {time_frame}", e)
                    return None
        except Exception as e:
            console.show_error("Erro ao consultar setup no banco de dados", e)
        return setup

    def insert_setup(self, symbol, time_frame, setup):
        r"""Insere um novo setup no banco de dados, desativando se houver outro setup de mesmo símbolo e time_frame.

          :param str symbol: símbolo do ativo que possui dados de candlestick
          :param str time_frame: período de tempo de cada candlestick (1m, 5m, 15m, etc)
          :param Setup setup: período de tempo de cada candlestick (1m, 5m, 15m, etc)
          :return int: True se inseriu ou False se não
          :rtype: bool
          """
        try:
            console.debug(f"Inativando, se existir, setup de {symbol} no timeframe de {time_frame}.")
            update = "UPDATE setups set deleted_at=now() WHERE cid=(SELECT cid FROM coins WHERE symbol=%s) AND " \
                     "timeframe=%s AND deleted_at IS NULL;"
            args = (symbol, time_frame)
            rows = self._execute(update, args)
            console.debug(f"Inserindo novo setup de {symbol} no timeframe de {time_frame} ...")
            insert = f"INSERT INTO setups (cid, timeframe, startdate, enddate, returns, jsonsetup) " \
                f"VALUES ((SELECT cid FROM coins WHERE symbol=%s), %s ,%s, %s, %s, %s);"
            args = (symbol, time_frame, setup.start_date, setup.end_date, setup.returns, setup.get_json())
            rows = self._execute(insert, args)
            if rows >= 0:
                console.debug(f"Setup de '{symbol}-{time_frame}-{setup.get_strategy()}' foi inserido com sucesso!")
            return rows > 0

        except Exception as e:
            console.show_error(f"Falha ao inserir novo setup de '{symbol}-{time_frame}-{setup.get_strategy()}'"
                               f" no banco de dados", e)
        return setup

    def create_tables(self):
        r"""Cria as tabelas que ainda não existirem no banco de dados."""
        try:
            console.debug(f"Tentando criar tabelas se não existirem  no banco de dados.")
            conn = self.get_mysql_conn()
            cursor = conn.cursor()
            for table, stmt in util.CREATE_TABLES.items():
                cursor.execute(stmt)
            conn.commit()
        except db.Error as e:
            console.show_error(f"Falha ao tentar criar tabela {table} no banco de dados", e)
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def get_candles_days(self, symbol, time_frame, days) -> Asset:
        r"""Obtém um Asset com dados de candlestick dentro do intervalo dos últimos dias (days).

           :param str symbol: símbolo do ativo que possui dados de candlestick
           :param str time_frame: período de tempo de cada candlestick (1m, 5m, 15m, etc)
           :param days: número de dias anteriores a última data no banco de dados.
           :return: um objeto Asset de type='candlestick' ou None se não encontrar registros
           :rtype: Asset
           """
        try:
            query = """SELECT DATE_ADD(MAX(cr.time), INTERVAL 1 MINUTE) as lastdate 
                      FROM candles_raw cr, coins c WHERE c.cid = cr.cid AND c.symbol = %(symbol)s 
                      AND cr.timeframe = %(time_frame)s"""
            args = {'symbol': symbol, 'time_frame': time_frame}
            column_names, rows = self._select(query, args)
            end = None
            if len(rows) > 0:
                end = rows[0][0]
            if end is None:
                console.debug("Sem registros no período!")
                return None
            args = {'symbol': symbol, 'time_frame': time_frame, "end": end, "days": days}
            query = """SELECT MIN(t.day) as day FROM (
                            SELECT DATE_FORMAT(cr.time,'%Y-%m-%d') as day 
                            FROM candles_raw cr, coins c WHERE c.cid = cr.cid AND c.symbol = %(symbol)s 
                            AND cr.timeframe = %(time_frame)s 
                            AND DATE_FORMAT(cr.time,'%Y-%m-%d') < DATE_FORMAT(%(end)s,'%Y-%m-%d')  
                            GROUP BY DATE_FORMAT(cr.time,'%y-%m-%d') ORDER BY cr.time DESC LIMIT %(days)s ) as t;"""
            column_names, rows = self._select(query, args)
            if len(rows) > 0:
                end_hour = datetime.strftime(end, '%H:%M:%S')
                start = f"{rows[0][0]} {end_hour}"
            else:
                end_day = datetime.strftime(end, '%Y-%m-%d')
                start = f"{end_day} 00:00:00"
            return self.get_candles(symbol=symbol, time_frame=time_frame, start_date=start, end_date=end)

        except Exception as e:
            console.show_error("Erro ao consultar dados de candlestick no banco de dados [data.get_candles_days]", e)
            print(symbol, time_frame, days, end)
            raise (e)


