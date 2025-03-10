"""
Module responsible for executing limit price orders

Author: Sunil Chauhan

The functions in this module facilitate to accept Orders for limit order processing.

Usage:
    from limit_order_agent import LimitOrderAgent, Order
    from trading_framework.execution_client import ExecutionClient
    
    order = Order('buy', '123', 1000, 100.0)
    limit_order_obj = LimitOrderAgent(ExecutionClient())
    limit_order_obj.add_order(order)
    
Current flaws (limitations) of the trading framework:
1. ExecutionClient Protocol class through 'buy' and 'sell' abstract methods implements interface
   or contract for structural duck typing. But, there is no return type defined for the abstract 
   methods which should be mandatory criteria for consistant interface implementation of Protocol.
2. There is no concrete implementations of ExecutionClient Protocol abstract methods 'buy' and 'sell'.
   Using these methods with the provided ExecutionClient object will throw NotImplementedError
3. 'amount' argument in ExecutionClient Protocol 'buy' and 'sell' methods defined as 'int'. It should be
   'float' for consistancy with PriceListener Protocol abstract method
4. Custom ExecutionException should be one of the return value of abstract methods 'buy' and 'sell'.
   This will indicate to classes implementing abstract methods to raise ExecutionException in case of execution
   error (as described in docstring of 'buy'/'sell' methods).
5. There is no "Is-a" relationship between LimitOrderAgent class and PriceListener Protocol class. In other words,
   there is no need for LimitOrderAgent class to inherit all the properties and methods of PriceListener 
   class. So, rather than inheriting from PriceListener class, PriceListener class object should be used as 
   composition (similar to ExecutionClient object).
6. Using PriceListener class object as composition removes tight coupling between these two classes. This 
   improves re-usability of LimitOrderAgent class to work with different broker PriceListners using on_price_tick()
   method
7. No return type defined for on_price_tick() of PriceListener Protocol
8. No broker APIs provided for on_price_tick() implementation, hence 'random' module is used to simulate
   real-time ticker pricing.
9. Typo in docstring for on_price_tick() method in PriceListener Protocol class for 'price' argument 
   (Should be 'the' in place of 'hte')
"""

import threading
import time
import random

from trading_framework.execution_client import ExecutionClient, ExecutionException
from trading_framework.price_listener import PriceListener

class Order:
    """Responsible for creating Order object
    """
    def __init__(self, flag: str, product_id: str, quantity: int, limit_price: float) -> None:
        """Constructor to initialise Order object

        Args:
            flag (str): flag indicating whether to buy or sell (i.e. Order type)
            product_id (str): product id of the stock
            quantity (int): quantity to buy/sell
            limit_price (float): the limit at which to buy or sell
        """
        self.order_type = flag.lower()
        self.product_id = product_id
        self.quantity = quantity
        self.limit_price = limit_price

class LimitOrderAgent(PriceListener):
    """Responsible for processing orders based on given limit price. Uses multi-threading to add and process new orders.
    """

    def __init__(self, execution_client: ExecutionClient) -> None:
        """ Initialise Limit Order Agent class
        
        Args:
            execution_client: can be used to buy or sell - see ExecutionClient protocol definition
        """
        super().__init__()
        self.execution_client = execution_client
        self.order_queue = []
        self.lock = threading.Lock()
        self._stop_thread_event = threading.Event()
        # Thread responsible for running infinite loop and processing new order once available in queue
        self._thread = threading.Thread(target=self._process_queue, args=(self._stop_thread_event,))
        self._thread.daemon = True
        self._thread.start()
    
    def add_order(self, order: Order) -> None:
        """Append new Order object to order queue
        
        Args:
            order (Order):  New order to add in queue
        """
        with self.lock:
            self.order_queue.append(order)  

    def on_price_tick(self, product_id: str, price: float) -> float:
        """Fetch current price for given product id using broker API

        Args:
            product_id (str): product id of the stock
            price (float): Limit price of the stock

        Returns:
            current_price (float): Current price of the stock
        """
        # See PriceListener protocol and readme file
        # Simulate current price using random.uniform() for price between 1.0 to 200.0 for given product id
        current_price = random.uniform(1.0, 200.0)
        print(f"Current price of {product_id} is {current_price}")
        return current_price

    def execute_orders(self, order: Order, current_price: float) -> None:
        """Execute limit order if limit price matched with current price

        Args:
            order (Order):  New order for processing
            current_price (float): Current price of the stock
        """
        try:
            if (order.order_type == 'buy' and order.limit_price >= current_price):
                print(f"Executing {order.order_type} order for {order.quantity} at {current_price} for limit price {order.limit_price}")
                self.execution_client.buy(order.product_id, order.quantity)
                self.order_queue.pop(0)
            elif (order.order_type == 'sell' and order.limit_price <= current_price):
                print(f"Executing {order.order_type} order for {order.quantity} at {current_price} for limit price {order.limit_price}")
                self.execution_client.sell(order.product_id, order.quantity)
                self.order_queue.pop(0)
            else:
                print(f"Limit price not matched with current price for {order.product_id}.")
        except Exception as e:
            raise ExecutionException(f"Error during executing orders")

    def _process_queue(self, event_object) -> None:
        """Process limit order queue
        
        Args:
            event_object (threading.Event): Event object to stop/start thread responsible for Queue processing
        """
        while not event_object.is_set():
            with self.lock:
                if self.order_queue:
                    print(f"Total held orders waiting for execution: {len(self.order_queue)}")
                    order = self.order_queue[0]
                    print(f"Currently executing order: {order.product_id}")
                    current_price = self.on_price_tick(order.product_id, order.limit_price)
                    self.execute_orders(order, current_price)
                    time.sleep(1)
    
    def stop_processing_queue(self) -> None:
        """Stop thread responsible for queue processing
        """
        self._stop_thread_event.set()
        self._thread.join()
    
