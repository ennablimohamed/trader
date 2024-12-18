from manager.abstract_manager import AbstractManager
from manager.signal.signal_manager import SignalManager
from manager.symbol_data_manager import SymbolDataManager


class AppManager(AbstractManager):

    def __init__(self, app_config):
        super().__init__(app_config)
        self.signal_manager = SignalManager(self.app_config)
        price_queues = self.signal_manager.get_price_queues()
        self.symbol_data_manager = SymbolDataManager(app_config=self.app_config, price_consumers_queues=price_queues)

    def start(self):
        self.symbol_data_manager.start()
        self.signal_manager.start()
        threads = self.__get_threads()
        for t in threads:
            t.join()

    def __get_threads(self):
        threads = self.signal_manager.get_threads()
        threads += self.symbol_data_manager.get_threads()
        return threads
