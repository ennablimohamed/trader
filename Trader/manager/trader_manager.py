import logging

from manager.abstract_manager import AbstractManager
from trader.reverse_mean_trader import ReverserMeanTrader

REVERSE_MEAN_SIGNAL_DETECTOR = 'ReverseMeanSignalDetector'


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
            if config.detector == REVERSE_MEAN_SIGNAL_DETECTOR:
                trader = ReverserMeanTrader(api_config=self.app_config.api_config,trader_config=config)
                traders.append(trader)
        return traders

    def get_price_queues(self):
        price_queues = {}
        for trader in self.traders:
            trader_config = trader.trader_config
            if price_queues.get(trader_config.symbol):
                price_queues[trader_config.symbol].append(trader.price_queue)
            else:
                price_queues[trader_config.symbol] = [trader.price_queue]
        return price_queues

    def get_order_queues(self):
        order_queues = []
        for trader in self.traders:
            order_queues.append(trader.order_queue)
        return order_queues

    def get_threads(self):
        threads = []
        for trader in self.traders:
            threads += trader.threads
        return threads
