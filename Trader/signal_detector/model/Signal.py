from signal_detector.model.AbstractSignal import AbstractSignal


class Signal(AbstractSignal):

    def __init__(self, detector, symbol, signal_type, price):
        super().__init__(type=signal_type, detector=detector, symbol=symbol)
        self.price = price
