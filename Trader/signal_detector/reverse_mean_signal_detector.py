import queue

from signal_detector.abstract_signal_detector import AbstractSignalDetector


class ReverseMeanSignalDetector(AbstractSignalDetector):

    def __init__(self, app_config, symbol):
        super().__init__(app_config=app_config, symbol=symbol)

    def start(self):
        super().start()
