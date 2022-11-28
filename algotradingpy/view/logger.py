#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
u"""
Description: Módulo para tratar as configurações
File name: logging.py
Author: Daniel Tell <daniel.tell@gmail.com>
Created on 2022-09-18
Updated on 2022-09-18
"""

import os
import logging
import algotradingpy.utils.util as util

logger = None


def create_logger(log_dir, file_name):
    global logger
    if log_dir is None:
        log_dir = util.get_config_path_default()
    if file_name is not None:
        try:
            if not os.path.exists(log_dir):
                os.mkdir(log_dir)
            logging.basicConfig(filename=log_dir + file_name + '.log', filemode='a',
                                format='%(asctime)-15s - %(name)s - %(levelname)s - %(message)s')
            logging.raiseExceptions = False
            logger = logging.getLogger(f'AlgoTradingPy')
            logger.setLevel(level=logging.INFO)
        except Exception as e:
            raise e


def info(msg):
    if logger is not None:
        logger.info(msg)


def error(msg, exception):
    if logger is not None:
        #logger.error(msg + ' (%s)', str(exception), exc_info=1)
        logger.error(msg + ' (%s)', str(exception))


def warning(msg):
    if logger is not None:
        logger.warning(msg)