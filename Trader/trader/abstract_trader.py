import logging
import queue
import threading
import time
from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal

from binance.spot import Spot
from date.date_util import get_current_date, compute_duration_until_now
from signal_detector.model.signal_type import SIGNAL_TYPE_BUY, SIGNAL_TYPE_SELL
from trader.model.trade import Trade

STATUS_BUY_OPEN = 'buy-open'
STATUS_FILLED = 'filled'
STATUS_CLOSED = 'closed'
STATUS_SALE_OPEN = 'sale-open'


class AbstractTrader(ABC):

    def __init__(self, api_config, trader_config):
        self.last_price = None
        self.price_queue = queue.Queue(maxsize=1000)
        self.stop_event = threading.Event()
        self.threads = []
        self.signal_queue = queue.Queue(maxsize=1000)
        self.api_config = api_config
        self.trader_config = trader_config
        self.capital = trader_config.capital
        self.free_slots = 0
        self.total_reserved_amount = Decimal('0')
        self.current_trades = []
        self.trade_history = []
        self.fees_to_cover = Decimal('0')
        self.order_queue = queue.Queue(maxsize=1000)
        self.trading_fee_percentage = Decimal('0.001')

    def start(self):
        self.__init_client()
        self.init_price_handling()
        self.init_signal_handling()
        self.init_order_update_handling()

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
            quantity = Decimal(str(self.trader_config.trade_quantity))
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

            trade = Trade()
            trade.buy_id = order_id
            trade.open_date = get_current_date()
            trade.quantity = quantity
            trade.detected_price = self.last_price
            trade.status = STATUS_BUY_OPEN
            trade.reserved_amount = order_reserved_amount

            self.free_slots -= 1
            self.total_reserved_amount += order_reserved_amount
            self.current_trades.append(trade)
            logging.info(f"open_position : A new order opened with id {order_id}")

        except Exception as e:
            logging.error(f"An Error occurred when opening buy position : {e}")

    def close_position(self):

        for trade in self.current_trades:
            if trade.status == STATUS_FILLED:
                try:
                    remote_order = self.client.new_order(symbol=self.trader_config.symbol,
                                                         side='buy',
                                                         type='LIMIT',
                                                         quantity=str(trade.quantity),
                                                         timeInForce='GTC',
                                                         price=str(self.last_price))
                    order_id = remote_order['orderId']
                    trade.sale_id = order_id
                    trade.status = STATUS_SALE_OPEN
                    logging.info(
                        f"close_position : Sale order opened with buy-id {trade.buy_id} and sale_id {trade.sale_id}")
                except Exception as e:
                    logging.error(f"Erreur lors de la vente : {e}")
                break

    def init_order_update_handling(self):
        t = threading.Thread(
            target=self.process_order_update_message,
            args=(),
            daemon=True
        )
        t.start()
        self.threads.append(t)

    def process_order_update_message(self):

        while not self.stop_event.is_set():
            try:
                message = self.order_queue.get(timeout=1)
                if message is None:
                    break
                if message['e'] == 'executionReport':
                    for order in self.current_trades:
                        if order.buy_id == message['i'] or order.sale_id == message['i']:
                            status = message['X']
                            if status == 'FILLED':
                                if message['S'] == 'BUY':
                                    self.update_buy_position(message, order)
                                elif message['S'] == 'SELL':
                                    self.update_sell_position(message, order)
                self.order_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"Error processing message for : {e}", exc_info=True)
                self.order_queue.task_done()

    def update_buy_position(self, message, trade):

        try:
            trade.cost = Decimal(message['Z'])
            trade.buy_commission = Decimal(message['n'])
            quantity_filled = Decimal(message['z'])
            trade.quantity_filled = quantity_filled
            trade.buy_price = trade.cost / quantity_filled
            trade.status = STATUS_FILLED
            self.total_reserved_amount -= trade.reserved_amount
            self.__update_capital('buy', trade.cost)
            logging.info("update_buy_order : Trade updated. Buy order executed successfully")
        except Exception as e:
            logging.error("update_buy_order")

    def update_sell_position(self, message, trade):

        try:
            logging.info(f"update_sale_order : Updating sale order with message {message}")
            trade.sailed_quantity = Decimal(message['z'])
            trade.close_date = get_current_date()
            trade.sale_price = Decimal(message['L'])
            start_datetime = datetime.strptime(trade.open_date, "%d/%m/%YT%H:%M")
            trade.duration = compute_duration_until_now(start_datetime)
            trade.sale_timestamp = time.time()
            total_sale_amount = Decimal(message['Z'])
            trade.sale_fees = total_sale_amount * self.trading_fee_percentage
            trade.profit = total_sale_amount - trade.cost - trade.sale_fees - self.fees_to_cover
            trade.status = STATUS_CLOSED

            self.__update_capital(action='sell', total=total_sale_amount - trade.sale_fees)
            self.trade_history.append(trade)
            self.current_trades.remove(trade)
            if trade.profit > 0:
                logging.info(f"update_sale_order : trade closed with profit {trade.profit}")
            if trade.profit < 0:
                logging.info(f"update_sale_order : trade closed with loss {trade.profit}")

        except Exception as e:
            logging.error(f'update_sale_order : An error occurred while updating order {trade.sale_id} with message {message}')

    def __update_capital(self, action, total):

        if action == 'buy':
            self.capital -= total
        elif action == 'sell':
            self.capital += total

    def init_signal_handling(self):
        t = threading.Thread(
            target=self.process_signal_message,
            args=(),
            daemon=True
        )
        t.start()
        self.threads.append(t)

    def process_signal_message(self):

        while not self.stop_event.is_set():
            try:
                signal = self.signal_queue.get(timeout=1)
                if signal is None:
                    break
                if signal.type == SIGNAL_TYPE_BUY:
                    self.handle_buy_signal_logic(signal)
                elif signal.type == SIGNAL_TYPE_SELL:
                    self.handle_sell_signal_logic(signal)
                self.signal_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"process_signal_message : Error processing signal message for symbol {self.trader_config.symbol}: {e}", exc_info=True)
                self.signal_queue.task_done()

    @abstractmethod
    def handle_buy_signal_logic(self, signal):
        pass

    @abstractmethod
    def handle_sell_signal_logic(self, signal):
        pass
