import logging
import queue
import threading
from abc import ABC
from decimal import Decimal

from binance.spot import Spot
from date.date_util import get_current_date
from trader.model.order import Order

STATUS_BUY_OPEN = 'buy-open'
STATUS_FILLED = 'filled'
STATUS_CLOSED = 'closed'
STATUS = 'sell-open'


class AbstractTrader(ABC):

    def __init__(self, api_config, trader_config):
        self.last_price = None
        self.price_queue = queue.Queue(maxsize=1000)
        self.stop_event = threading.Event()
        self.threads = []
        self.signal_queue = queue.Queue(maxsize=1000)
        self.api_config = api_config
        self.__init_client()
        self.trader_config = trader_config
        self.capital = trader_config.capital
        self.free_slots = 0
        self.total_reserved_amount = Decimal('0')
        self.current_orders = []
        self.fees_to_cover = Decimal('0')

    def start(self):
        self.init_price_handling()

    def process_price_update_message(self):

        while not self.stop_event.is_set():
            try:
                message = self.price_queue.get(timeout=1)
                if message is None:
                    break
                self.last_price = message['last_price']
                self.price_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(
                    f"process_price_update_message : Error processing price message for symbol {self.trader_config.symbol}: {e}",
                    exc_info=True)
                self.price_queue.task_done()

    def init_price_handling(self):
        t = threading.Thread(
            target=self.process_price_update_message,
            args=(),
            daemon=True
        )
        t.start()
        self.threads.append(t)

    def buy_fees(self):
        try:
            quantity = Decimal('0.0000001') * Decimal('1000')
            order = self.client.new_order(
                symbol=self.trader_config.symbol,
                side='BUY',
                type='MARKET',
                quantity=str(quantity)
            )

            fills = order.get('fills', [])
            total_cost = Decimal('0')
            for fill in fills:
                price = Decimal(fill['price'])
                qty = Decimal(fill['qty'])
                total_cost += price * qty
            self.free_slots = 999
            self.fees_to_cover = total_cost / self.free_slots
            logging.info(f'fees to cover {self.fees_to_cover}')
            self.trader_config.capital -= total_cost
            logging.info('Fees bought')
        except Exception as e:
            logging.error(f"Error placing buy order: {e}")

    def __init_client(self):
        credentials = self.api_config.credentials
        trades_base_url = self.api_config.trades_config.base_url
        self.client = Spot(
            api_key=credentials.api_key,
            api_secret=credentials.secret,
            base_url=trades_base_url)

    def open_position(self):
        try:
            quantity = self.trader_config.trade_quantity
            # Place a market buy order using Binance API
            remote_order = self.client.new_order(symbol=self.trader_config.symbol,
                                                 side='buy',
                                                 type='LIMIT',
                                                 quantity=str(quantity),
                                                 timeInForce='GTC',
                                                 price=str(self.last_price))

            # Extract order details
            order_id = remote_order['orderId']
            order_reserved_amount = self.last_price * quantity

            order = Order()
            order.id = order_id
            order.open_date = get_current_date()
            order.detected_price = self.last_price
            order.status = STATUS_BUY_OPEN
            order.reserved_amount = order_reserved_amount

            self.free_slots -= 1
            self.total_reserved_amount += order_reserved_amount
            self.current_orders.append(order)

        except Exception as e:
            logging.error(f"Error opening buy position : {e}")
