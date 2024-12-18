from manager.abstract_manager import AbstractManager
from manager.price_manager import PriceManager


class SymbolDataManager(AbstractManager):

    def __init__(self, app_config, price_consumers_queues):
        super().__init__(app_config)
        self.price_managers = []
        for symbol, price_consumer_queues in price_consumers_queues.items():
            price_manager = PriceManager(app_config=app_config, symbol=symbol,
                                         price_consumers_queues=price_consumer_queues)
            self.price_managers.append(price_manager)

    def start(self):
        for price_manager in self.price_managers:
            price_manager.start()

    def get_threads(self):
        threads = []
        for price_manager in self.price_managers:
            threads += price_manager.threads
        return threads
