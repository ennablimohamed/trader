from manager.abstract_manager import AbstractManager
from manager.klines_manager import KlinesManager
from manager.price_manager import PriceManager


class SymbolDataManager(AbstractManager):

    def __init__(self, app_config):
        super().__init__(app_config)
        self.price_managers = None
        self.klines_managers = None

    def init_price_managers(self, price_consumers_queues):

        price_managers = []
        for symbol, price_consumer_queues in price_consumers_queues.items():
            price_manager = PriceManager(app_config=self.app_config, symbol=symbol,
                                         consumers_queues=price_consumer_queues)
            price_managers.append(price_manager)
        self.price_managers = price_managers

    def init_klines_managers(self, klines_consumers_queues):

        klines_managers = []
        klines_config = self.app_config.klines_config
        for symbol, klines_consumer_queues in klines_consumers_queues.items():
            period = None
            for entry in klines_config:
                if entry.symbol == symbol:
                    period = entry.period
            klines_manager = KlinesManager(app_config=self.app_config, symbol=symbol, period=period,
                                           consumers_queues=klines_consumer_queues)
            klines_managers.append(klines_manager)
        self.klines_managers = klines_managers

    def start(self):
        for price_manager in self.price_managers:
            price_manager.start()
        for klines_manager in self.klines_managers:
            klines_manager.start()

    def get_threads(self):
        threads = []
        for price_manager in self.price_managers:
            threads += price_manager.threads
        return threads


