from manager.abstract_manager import AbstractManager
from signal_detector.abstract_signal_detector import AbstractSignalDetector


class DeepSignalDetector(AbstractSignalDetector):

    def __init__(self, app_config):
        super().__init__(app_config)


    def start(self):
        pass