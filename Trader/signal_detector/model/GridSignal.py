from signal_detector.model.AbstractSignal import AbstractSignal


class GridSignal(AbstractSignal):

    def __init__(self, signal_type, detector, symbol, min_price, max_price):
        super().__init__(signal_type, detector, symbol)
        self.min_price = min_price
        self.max_price = max_price
