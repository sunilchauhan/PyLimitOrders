"""This module contains unittest for limit.limit_order_agent.py

Test classes:
- OrderTest: Test case for Order class
- LimitOrderAgentTest: Test case for LimitOrderAgent class
"""
import unittest
from unittest.mock import MagicMock, patch

from trading_framework.execution_client import ExecutionClient
from limit_order_agent import LimitOrderAgent, Order, random
from limit.limit_order_agent import Order

class OrderTest(unittest.TestCase):
    """Test Order class
    """
    def test_init(self):
        """Test Order class __init__ method
        """
        order = Order('buy', '123', 500, 100.0)
        self.assertEqual(order.product_id, '123')
        self.assertEqual(order.order_type, 'buy')
        self.assertEqual(order.limit_price, 100.0)
        self.assertEqual(order.quantity, 500)

class LimitOrderAgentTest(unittest.TestCase):
    """Test to unittest functionality of limit_order_agent class
    """
    def setUp(self):
        self.mock_execution_client = MagicMock(spec=ExecutionClient)
        self.limit_order_agent = LimitOrderAgent(self.mock_execution_client)
        self.mock_random = patch.object(random, 'uniform', return_value=100).start()
    
    def tearDown(self):
        self.mock_random.stop()
        self.limit_order_agent.stop_processing_queue()
        self.limit_order_agent._stop_thread_event.set()
        self.limit_order_agent._thread.join()
    
    def test_add_order(self):
        """Test to check add_order functionality
        """
        order = Order('buy', '123', 500, 100.0)
        self.limit_order_agent.add_order(order)
        self.assertTrue(order in self.limit_order_agent.order_queue)
    
    def test_on_price_tick(self):
        """Test to check simulation of on_price_tick method
        """
        self.mock_random.return_value = 100
        actual_result = self.limit_order_agent.on_price_tick('test_product_id', 1000.0)
        expected_result = 100
        self.assertEqual(actual_result, expected_result)
    
    def test_execute_buy_orders(self):
        """Test to check execution of buy order
        """
        order = Order('buy', '123', 1000, 100.0)
        self.limit_order_agent.order_queue.append(order)
        self.limit_order_agent.execute_orders(order, 100.0)
        self.mock_execution_client.buy.assert_called_with('123', 1000)
        # Check if 'sell' function not getting called for 'buy' orders
        self.mock_execution_client.sell.assert_not_called()
    
    def test_execute_sell_orders(self):
        """Test to check execution of sell order
        """
        order = Order('sell', '123', 1000, 100.0)
        self.limit_order_agent.order_queue.append(order)
        self.limit_order_agent.execute_orders(order, 100.0)
        self.mock_execution_client.sell.assert_called_with('123', 1000)
        # Check if 'buy' function not getting called for 'sell' orders
        self.mock_execution_client.buy.assert_not_called()
    
    def test_execute_orders_exception(self):
        """Test exception handling for execute orders
        """
        self.mock_execution_client.sell.side_effect = lambda: Exception()
        with self.assertRaises(Exception) as context:
            order = Order('sell', '123', 1000, 100.0)
            self.limit_order_agent.execute_orders(order, 100.0)
        self.assertTrue('Error during executing orders' in str(context.exception))

if __name__ == '__main__':
    unittest.main()


