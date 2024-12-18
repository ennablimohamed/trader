import logging

from manager.abstract_manager import AbstractManager
from signal_detector.reverse_mean_signal_detector import ReverseMeanSignalDetector


class SignalManager(AbstractManager):

    def __init__(self, app_config):
        super().__init__(app_config)
        self.signal_detectors = self.__extract_signal_detectors()

    def start(self):
        logging.info('start : Starting signal detectors')
        for detector in self.signal_detectors:
            detector.start()

    def __extract_signal_detectors(self):
        logging.debug(f'__extract_signal_detectors : Extracting signal configs')
        signal_detectors = []
        signal_configs = self.app_config.signal_configs
        for config in signal_configs:
            if config.detector == 'ReverseMeanSignalDetector':
                detector = ReverseMeanSignalDetector(symbol=config.symbol, app_config=self.app_config)
                signal_detectors.append(detector)
        return signal_detectors

    def get_price_queues(self):
        price_queues = {}
        for detector in self.signal_detectors:
            symbol = detector.symbol
            if price_queues.get(symbol):
                price_queues[symbol].append(detector.price_queue)
            else:
                price_queues[symbol] = [detector.price_queue]
        return price_queues

    def get_threads(self):
        threads = []
        for signal_detector in self.signal_detectors:
            threads += signal_detector.threads
        return threads

