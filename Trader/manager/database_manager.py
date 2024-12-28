import psycopg2
from manager.abstract_manager import AbstractManager
from trader.model.trade import Trade
from trader.model.trader import Trader


class DatabaseManager(AbstractManager):

    def __init__(self, app_config):
        super().__init__(app_config)

    def start(self):
        pass

    def connect(self):
        """Établit une connexion à la base de données PostgreSQL."""
        try:
            db_config = self.app_config.database_config
            conn = psycopg2.connect(
                dbname=db_config.db_name,
                user=db_config.user,
                password=db_config.password,
                host=db_config.host,
                port=db_config.port
            )
            return conn
        except Exception as e:
            print(f"connect : An error occurred when connecting to the database")
            return None

    def save_trader(self, trader):
        """Sauvegarde un objet Trader dans la base de données."""
        conn = self.connect()
        if conn is None:
            return
        cursor = conn.cursor()
        try:
            query = """
            INSERT INTO public.traders (capital, remaining_capital, profit, free_slots, signal_detector, symbol, 
                                        progress_percentage, total_reserved_amount, trade_quantity)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
            """
            cursor.execute(query, (
                trader.capital,
                trader.remaining_capital,
                trader.profit,
                trader.free_slots,
                trader.signal_detector,
                trader.symbol,
                trader.progress_percentage,
                trader.total_reserved_amount,
                trader.trade_quantity
            ))
            trader.id = cursor.fetchone()[0]
            conn.commit()
        except Exception as e:
            print(f"Erreur lors de l'insertion du trader : {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    def save_trade(self, trade):
        """Sauvegarde un objet Trade dans la base de données."""
        conn = self.connect()
        if conn is None:
            return
        cursor = conn.cursor()
        try:
            query = """
            INSERT INTO public.trades (
                trader_id, buy_id, open_date, status, detected_price, reserved_amount, quantity, sale_id, cost, 
                buy_commission, buy_price, quantity_filled, close_date, sale_price, duration, sale_timestamp, sale_fees
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
            """
            cursor.execute(query, (
                trade.trader_id,
                trade.buy_id,
                trade.open_date,
                trade.status,
                trade.detected_price,
                trade.reserved_amount,
                trade.quantity,
                trade.sale_id,
                trade.cost,
                trade.buy_commission,
                trade.buy_price,
                trade.quantity_filled,
                trade.close_date,
                trade.sale_price,
                trade.duration,
                trade.sale_timestamp,
                trade.sale_fees
            ))
            trade.id = cursor.fetchone()[0]
            conn.commit()
        except Exception as e:
            print(f"Erreur lors de l'insertion du trade : {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    def load_all_traders(self):
        """Charge tous les traders depuis la base de données."""
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        traders = []
        try:
            query = """
            SELECT id, capital, remaining_capital, profit, free_slots, signal_detector, symbol, 
                   progress_percentage, total_reserved_amount, trade_quantity 
            FROM public.traders
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            for row in rows:
                trader = Trader()
                trader.id = row[0]
                trader.capital = row[1]
                trader.remaining_capital = row[2]
                trader.profit = row[3]
                trader.free_slots = row[4]
                trader.signal_detector = row[5]
                trader.symbol = row[6]
                trader.progress_percentage = row[7]
                trader.total_reserved_amount = row[8]
                trader.trade_quantity = row[9]
                traders.append(trader)
        except Exception as e:
            print(f"Erreur lors du chargement des traders : {e}")
        finally:
            cursor.close()
            conn.close()
        return traders

    def load_trades_by_trader(self, trader_id, status_not='closed'):
        """Charge les trades d'un trader spécifique avec un statut différent de 'closed'."""
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        trades = []
        try:
            query = """
            SELECT id, trader_id, buy_id, open_date, status, detected_price, reserved_amount, quantity, sale_id, cost, 
                   buy_commission, buy_price, quantity_filled, close_date, sale_price, duration, sale_timestamp, sale_fees
            FROM public.trades
            WHERE trader_id = %s AND status != %s
            """
            cursor.execute(query, (trader_id, status_not))
            rows = cursor.fetchall()
            for row in rows:
                trade = Trade()
                trade.id = row[0]
                trade.trader_id = row[1]
                trade.buy_id = row[2]
                trade.open_date = row[3]
                trade.status = row[4]
                trade.detected_price = row[5]
                trade.reserved_amount = row[6]
                trade.quantity = row[7]
                trade.sale_id = row[8]
                trade.cost = row[9]
                trade.buy_commission = row[10]
                trade.buy_price = row[11]
                trade.quantity_filled = row[12]
                trade.close_date = row[13]
                trade.sale_price = row[14]
                trade.duration = row[15]
                trade.sale_timestamp = row[16]
                trade.sale_fees = row[17]
                trades.append(trade)
        except Exception as e:
            print(f"Erreur lors du chargement des trades : {e}")
        finally:
            cursor.close()
            conn.close()
        return trades

    def update_trader(self, trader):
        """Met à jour un trader dans la base de données en fonction de son ID."""
        conn = self.connect()
        if conn is None:
            return
        cursor = conn.cursor()
        try:
            query = """
            UPDATE public.traders
            SET capital = %s, remaining_capital = %s, profit = %s, free_slots = %s, signal_detector = %s, 
                symbol = %s, progress_percentage = %s, total_reserved_amount = %s, trade_quantity = %s
            WHERE id = %s;
            """
            cursor.execute(query, (
                trader.capital,
                trader.remaining_capital,
                trader.profit,
                trader.free_slots,
                trader.signal_detector,
                trader.symbol,
                trader.progress_percentage,
                trader.total_reserved_amount,
                trader.trade_quantity,
                trader.id
            ))
            conn.commit()
        except Exception as e:
            print(f"Erreur lors de la mise à jour du trader : {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    def update_trade(self, trade):
        """Met à jour un trade dans la base de données en fonction de son ID."""
        conn = self.connect()
        if conn is None:
            return
        cursor = conn.cursor()
        try:
            query = """
            UPDATE public.trades
            SET trader_id = %s, buy_id = %s, open_date = %s, status = %s, detected_price = %s, reserved_amount = %s,
                quantity = %s, sale_id = %s, cost = %s, buy_commission = %s, buy_price = %s, quantity_filled = %s,
                close_date = %s, sale_price = %s, duration = %s, sale_timestamp = %s, sale_fees = %s
            WHERE id = %s;
            """
            cursor.execute(query, (
                trade.trader_id,
                trade.buy_id,
                trade.open_date,
                trade.status,
                trade.detected_price,
                trade.reserved_amount,
                trade.quantity,
                trade.sale_id,
                trade.cost,
                trade.buy_commission,
                trade.buy_price,
                trade.quantity_filled,
                trade.close_date,
                trade.sale_price,
                trade.duration,
                trade.sale_timestamp,
                trade.sale_fees,
                trade.id
            ))
            conn.commit()
        except Exception as e:
            print(f"Erreur lors de la mise à jour du trade : {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

