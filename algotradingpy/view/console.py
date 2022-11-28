# -*- coding: utf-8 -*-
u"""
Description: Módulo para tratar a saída e imprimir logs
File name: console.py
Author: Daniel Tell <daniel.tell@gmail.com>
Created on 2021-10-02
Updated on 2022-09-18
"""

import algotradingpy.view.logger as _logger

enable_logging = False
log_level = ""


def create_logger(log_dir, file_name):
    global enable_logging
    try:
        _logger.create_logger(log_dir, file_name)
    except Exception as e:
        enable_logging = False
        show_error(f"Não foi possível criar arquivo de log em {log_dir}/{file_name}.", e)
        pass


def show(msg):
    print(msg)
    if enable_logging:
        _logger.info(msg)


def show_warning(msg):
    print(f'\033[7;33m{msg}\033[m')
    if enable_logging:
        _logger.warning(msg)


def show_error(msg, exception):
    print(f'\033[7;31m{msg} ({exception})\033[m')
    if enable_logging:
        _logger.error(msg, exception)


def debug(msg):
    if log_level == "debug":
        print(msg)
        if enable_logging:
            _logger.info(msg)
