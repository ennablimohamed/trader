import logging

from manager.abstract_manager import AbstractManager
from trader.reverse_mean_trader import ReverserMeanTrader


class TraderManager(AbstractManager):

    def __init__(self, app_config):
        super().__init__(app_config)
        self.traders = self.__extract_traders()

    def start(self):
        for trader in self.traders:
            trader.start()

    def __extract_traders(self):
        logging.debug(f'__extract_traders : Extracting traders')
        traders = []
        traders_configs = self.app_config.traders_config
        for config in traders_configs:
            if config.detector == 'ReverseMeanSignalDetector':
                trader = ReverserMeanTrader(symbol=config.symbol, capital=config.capital, signal_detector=config.detector)
                traders.append(trader)
        return traders

    def get_price_queues(self):
        price_queues = {}
        for trader in self.traders:
            symbol = trader.symbol
            if price_queues.get(symbol):
                price_queues[symbol].append(trader.price_queue)
            else:
                price_queues[symbol] = [trader.price_queue]
        return price_queues

    def get_threads(self):
        threads = []
        for trader in self.traders:
            threads += trader.threads
        return threads
