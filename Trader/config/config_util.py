import logging

import yaml

from config.api_config import ApiConfig
from config.api_config_credentials import ApiConfigCredentials
from config.app_config import AppConfig
from config.env_util import get_environment
from config.api_price_config import ApiPriceConfig
from config.klines_config import KlinesConfig
from config.signal_config import SignalConfig
from config.trader_config import TraderConfig


def load_current_config():
    try:
        env = get_environment()
        file_name = f'application-{env}.yml'
        file_config = load_file(f'resources/{file_name}')

        api_config = extract_api_config(file_config)
        signal_configs = extract_signal_config(file_config)
        klines_config = extract_klines_config(file_config)
        traders_config = extract_traders_config(file_config)

        app_config = AppConfig()
        app_config.api_config = api_config
        app_config.signal_configs = signal_configs
        app_config.klines_config = klines_config
        app_config.traders_config = traders_config

        return app_config
    except Exception as e:
        logging.error('An error occurred while loading the config', e)
        raise Exception('An error occurred while loading the config')


def extract_price_config(file_config):
    file_price_config = file_config['price']['symbols']
    return ApiPriceConfig(file_price_config)


def extract_api_config(file_config):
    file_config_api = file_config['api']
    file_credentials = file_config_api['credentials']
    credentials = ApiConfigCredentials(file_credentials['api-key'], file_credentials['secret'])
    websocket_base_url = file_config_api['websocket-base-url']
    base_url = file_config_api['base-url']

    return ApiConfig(credentials=credentials, websocket_base_url=websocket_base_url, base_url=base_url)


def load_file(path):
    with open(path, 'r') as file:
        return yaml.safe_load(file)


def extract_signal_config(file_config):
    file_signal_config = file_config['signals']
    signal_configs = []
    for entry in file_signal_config:
        for key, value in entry.items():
            symbol = value['symbol']
            detector = value['detector']
            need_klines = value.get('need_klines', None)
            signal_config = SignalConfig(symbol=symbol, detector=detector, need_klines=need_klines)
            signal_configs.append(signal_config)
    return signal_configs


def extract_klines_config(file_config):
    file_klines_config = file_config['klines']
    klines_configs = []
    for entry in file_klines_config:
        for key, value in entry.items():
            period = value['period']
            kline_config = KlinesConfig(symbol=key, period=period)
            klines_configs.append(kline_config)
    return klines_configs


def extract_traders_config(file_config):
    file_traders_config = file_config['traders']
    traders_configs = []
    for entry in file_traders_config:
        for key, value in entry.items():
            symbol = value['symbol']
            detector = value['detector']
            capital = value['capital']
            trader_config = TraderConfig(symbol=symbol, detector=detector, capital=capital)
            traders_configs.append(trader_config)
    return traders_configs
