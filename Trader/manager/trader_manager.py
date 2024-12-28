import logging

from manager.abstract_manager import AbstractManager
from trader.grid_trader import GridTrader
from trader.reverse_mean_trader import ReverserMeanTrader

REVERSE_MEAN_SIGNAL_DETECTOR = 'ReverseMeanSignalDetector'
GRID_SIGNAL_DETECTOR = 'GridSignalDetector'


class TraderManager(AbstractManager):

    def __init__(self, app_config, database_manager):
        super().__init__(app_config)
        self.traders = []
        self.database_manager = database_manager

    def start(self):
        logging.info("start : Loading traders...")
        traders = self.database_manager.load_all_traders()
        self.__extract_traders(traders)
        for trader in self.traders:
            trader.start()

    def __extract_traders(self, traders):
        logging.debug(f'__extract_traders : Extracting traders')
        for trader in traders:
            if trader.signal_detector == REVERSE_MEAN_SIGNAL_DETECTOR:
                trader = ReverserMeanTrader(
                    api_config=self.app_config.api_config,
                    trader=trader,
                    database_manager=self.database_manager)
                self.traders.append(trader)
            elif trader.detector == GRID_SIGNAL_DETECTOR:
                trader = GridTrader(
                    api_config=self.app_config.api_config,
                    trader=trader,
                    database_manager=self.database_manager)
                self.traders.append(trader)

    def get_price_queues(self):
        price_queues = {}
        for trader in self.traders:
            if price_queues.get(trader.trader.symbol):
                price_queues[trader.trader.symbol].append(trader.price_queue)
            else:
                price_queues[trader.trader.symbol] = [trader.price_queue]
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
