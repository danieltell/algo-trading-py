#!/usr/bin/env python
# -*- coding: utf-8 -*-
u"""
Description: Uma biblioteca para backtesting de estratégias de negociação de criptomoedas.
File name: __main__.py
Author: Daniel Tell <daniel.tell@gmail.com>
Date created: 19/09/2022
Date last modified: 19/09/2022
"""

import algotradingpy
import algotradingpy.view.console as console
import algotradingpy.utils.config as config
import algotradingpy.utils.util as util
from algotradingpy.controller.collect import DataCollection
import argparse
import sys

run_mode = "main"


def run_get_data(log_dir):
    global run_mode
    run_mode = "get_data"
    console.create_logger(log_dir, run_mode)
    console.show('Coleta de dados da Bitfinex foi iniciada')

    getData = DataCollection()
    # symbols = config.get_symbols()
    # if ('btcusd' in symbols):
    #     print(symbols['btcusd'])

    #print(symbol in config.get_symbols())


def main():
    try:
        parser = argparse.ArgumentParser(
            description='Uma biblioteca para backtesting de estratégias de negociação de criptomoedas/ações')
        parser.add_argument('--config',
                            metavar='arquivo', default=config.get_conf_file_default(),
                            help='Arquivo de configuração gravável (json).'
                                 ' Usado para armazenar parâmetros do banco de dados símbolos a serem coletados.'
                                 ' Padrão: %(default)s')

        parser.add_argument('--get-data', dest='getdata', action='store_true',
                            help='Coleta e popula continuamente cotações da Bitfinex no banco de dados.'
                                 ' Edite o arquivo de configuração (json) para incluir ou remover os símbolos,')

        parser.add_argument('--enable-logging', dest='logging',
                            help='Habilita geração de registros de atividades em arquivo de log.'
                                 ' Diretório do arquivo de log pode ser alterado através do argumento --log-dir.',
                            action="store_true")

        parser.add_argument('--log-dir',
                            metavar='caminho', dest="logdir", default=util.get_config_path_default(),
                            help='O diretório onde a saída de registro é salva, precisa terminar com uma barra.'
                                 ' Padrão: %(default)s')

        parser.add_argument('--version', action='version',
                            version=f'algotradingpy {algotradingpy.__version__}',
                            help='Imprime p número da versão e sai.')

        if len(sys.argv) == 1:
            parser.print_help(sys.stderr)
            sys.exit(1)

        args = parser.parse_args()
        if args.config:
            config.set_file(args.config)
        if args.logging:
            console.enable_logging = True
        log_dir = util.get_config_path_default()
        if args.logdir:
            log_dir = args.logdir
        console.log_level = config.get_loglevel()
        if args.getdata:
            run_get_data(log_dir)

        #console.log_level = "debug";
        #config.set_file("/home/daniel/.AlgoTradingPy/config.json")
        #run_get_data('/home/daniel/.AlgoTradingPy/')

    except Exception as e:
        console.show_error("Erro ao iniciar método main()", e)
    except (InterruptedError, KeyboardInterrupt):
        console.show("AlgoTradingPy foi finalizado.")


if __name__ == '__main__': main()


