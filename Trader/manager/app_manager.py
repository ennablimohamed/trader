import logging

from manager.abstract_manager import AbstractManager
from manager.order_manager import OrderManager
from manager.signal_manager import SignalManager
from manager.symbol_data_manager import SymbolDataManager
from manager.trader_manager import TraderManager
from utils.dico_util import merge_dicts


class AppManager(AbstractManager):

    def __init__(self, app_config):
        super().__init__(app_config)
        self.trader_manager = TraderManager(self.app_config)
        self.signal_manager = SignalManager(self.app_config)
        self.fill_signal_consumers_queues()
        price_queues = self.__extract_price_queues()
        klines_queues = self.signal_manager.get_klines_queues()
        self.symbol_data_manager = SymbolDataManager(
            app_config=self.app_config,
            price_consumers_queues=price_queues,
            klines_consumers_queues=klines_queues
        )
        order_queues = self.trader_manager.get_order_queues()
        self.order_manager = OrderManager(app_config=app_config, order_queues=order_queues)

    def start(self):
        logging.info("start : Starting symbol_data_manager")
        self.symbol_data_manager.start()
        logging.info("start : Starting signal manager")
        self.signal_manager.start()
        logging.info("start : Starting trader manager")
        self.trader_manager.start()
        logging.info("start : Starting order manager")
        self.order_manager.start()
        threads = self.__get_threads()
        for t in threads:
            t.join()

    def __get_threads(self):
        threads = self.signal_manager.get_threads()
        threads += self.symbol_data_manager.get_threads()
        threads += self.trader_manager.get_threads()
        threads += self.order_manager.get_threads()
        return threads

    def __extract_price_queues(self):
        signal_price_queues = self.signal_manager.get_price_queues()
        trader_price_queues = self.trader_manager.get_price_queues()
        price_queues = merge_dicts(signal_price_queues, trader_price_queues)
        return price_queues

    def fill_signal_consumers_queues(self):
        for trader in self.trader_manager.traders:
            trader_config = trader.trader_config
            self.signal_manager.add_signal_consumer(trader.signal_queue, trader_config.detector, trader_config.symbol)


