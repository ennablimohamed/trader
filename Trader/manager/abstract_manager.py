from abc import ABC, abstractmethod


class AbstractManager(ABC):

    def __init__(self, app_config):
        self.app_config = app_config

    @abstractmethod
    def start(self):
        pass
