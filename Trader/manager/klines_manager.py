import logging
import queue
import threading
import time
import requests

from manager.abstract_manager import AbstractManager


class KlinesManager(AbstractManager):

    def __init__(self, app_config, symbol, period, consumers_queues):
        super().__init__(app_config)
        self.symbol = symbol
        self.period = period
        self.threads = []
        self.consumers_queues = consumers_queues

    def start(self):
        self.init_handler()

    def init_handler(self):
        t = threading.Thread(
            target=self.process_klines_update,
            args=(),
            daemon=True
        )
        t.start()
        self.threads.append(t)

    def process_klines_update(self):
        base_url = self.app_config.api_config.base_url
        url = base_url + '/api/v3/klines'
        params = {
            'symbol': self.symbol,
            'interval': self.period,
            'limit': 1000
        }
        while True:
            try:
                logging.debug('process_klines_update : Retrieving klines...')
                response = requests.get(url, params=params)
                self.__notify_consumers(response.json())
            except Exception as e:
                logging.error('An error occureed while updqting klines')
            finally:
                time.sleep(60)

    def __notify_consumers(self, payload):

        logging.debug(f"__notify_consumers : Start notifying consumers about klines update for symbol {self.symbol}")
        for q in self.consumers_queues:
            try:
                q.put_nowait(payload)
            except queue.Full:
                logging.warning(f"Klines queue is full for symbol {self.symbol}. Dropping message.")
            except Exception as e:
                logging.error(f"An error occurred while notifying consumers for klines update for symbol {self.symbol}")