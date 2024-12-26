from abc import ABC


class AbstractSignal(ABC):

    def __init__(self, type, detector, symbol):
        self.type = type
        self.detector = detector
        self.symbol = symbol
