from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
import json
import time
from trading.models import User, Transaction, Portfolio, StockHolding
from trading.utils import get_valid_symbols


class TradingModelTestCase(TestCase):

    def setUp(self):
        """Set up test user, initiate a test client and login"""
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.client = Client()
        self.client.login(username="testuser", password="testpassword")
    

    def test_portfolio_automatically_created(self):
        """Test that a user portfolio is automatically created with a balance of $10000"""
        portfolio = Portfolio.objects.first()
        self.assertEqual(portfolio.user, self.user)
        self.assertEqual(portfolio.balance, 10000)

    
    def test_transaction_buy(self):
        """Test that a user can buy a stock under normal circumstances"""
        transaction = Transaction.objects.create(
            user=self.user,
            stock_symbol='EXAMPLE',
            transaction_type='BUY',
            quantity=10,
            price=200.00,
        )
        self.assertEqual(Transaction.objects.first(), transaction)
        self.assertEqual(Transaction.objects.first().total, 2000)

    
    def test_transaction_buy_insufficient_balance(self):
        """Test that a user cannot buy a stock if their balance is insufficient"""
        with self.assertRaises(ValidationError):
            transaction = Transaction.objects.create(
                user=self.user,
                stock_symbol='EXAMPLE',
                transaction_type='BUY',
                quantity=10,
                price=2000.00,
            )
    

    def test_transaction_buy_updates_holding(self):
        """Test that a buy transaction creates/updates a holding"""
        # For a stock not already owned, a new StockHolding object should be created
        Transaction.objects.create(
            user=self.user,
            stock_symbol='EXAMPLE',
            transaction_type='BUY',
            quantity=10,
            price=200.00,
        )
        holding = StockHolding.objects.first()
        self.assertEqual(holding.stock_symbol, 'EXAMPLE')
        self.assertEqual(holding.quantity, 10)

        # For an existing stock holding, quantity should be increased
        Transaction.objects.create(
            user=self.user,
            stock_symbol='EXAMPLE',
            transaction_type='BUY',
            quantity=10,
            price=200.00,
        )
        holding.refresh_from_db()
        self.assertEqual(holding.quantity, 20)


    def test_transaction_sell(self):
        """Test that a user can sell stock they own"""
        # Initialize a holding
        holding = StockHolding.objects.create(
            portfolio=self.user.portfolio,
            stock_symbol='EXAMPLE',
            quantity=10
        )
        # Make a SELL transaction
        transaction = Transaction.objects.create(
            user=self.user,
            stock_symbol='EXAMPLE',
            transaction_type='SELL',
            quantity=10,
            price=200.00
        )

        self.assertEqual(Transaction.objects.first(), transaction)
        self.assertEqual(transaction.total, 2000.00)


    def test_transaction_sell_excessive_quantity(self):
        """Test that a user cannot more stock than they own"""
        # Initialize a holding
        holding = StockHolding.objects.create(
            portfolio=self.user.portfolio,
            stock_symbol='EXAMPLE',
            quantity=10
        )

        # Sell more than owned amount
        with self.assertRaises(ValidationError):
            transaction = Transaction.objects.create(
                user=self.user,
                stock_symbol='EXAMPLE',
                transaction_type='SELL',
                quantity=20,
                price=200.00
            )


    def test_transaction_sell_updates_holding(self):
        """Test that a SELL transaction updates/deletes a holding"""
        # Initialize a holding
        holding = StockHolding.objects.create(
            portfolio=self.user.portfolio,
            stock_symbol='EXAMPLE',
            quantity=10
        )

        # Sell half of owned stock
        Transaction.objects.create(
                user=self.user,
                stock_symbol='EXAMPLE',
                transaction_type='SELL',
                quantity=5,
                price=200.00
            )
        holding.refresh_from_db()
        self.assertEqual(holding.quantity, 5)

        # Sell the remaining half
        Transaction.objects.create(
                user=self.user,
                stock_symbol='EXAMPLE',
                transaction_type='SELL',
                quantity=5,
                price=200.00
            )
        with self.assertRaises(StockHolding.DoesNotExist):
            holding.refresh_from_db()
    
        
    def test_transaction_updates_balance(self):
        Transaction.objects.create(
            user=self.user,
            stock_symbol='EXAMPLE',
            transaction_type='BUY',
            quantity=10,
            price=200.00,
        )
        portfolio = Portfolio.objects.get(user=self.user)
        balance = portfolio.balance
        self.assertEqual(balance, 8000.00)

        Transaction.objects.create(
            user=self.user,
            stock_symbol='EXAMPLE',
            transaction_type='SELL',
            quantity=10,
            price=200.00,
        )
        portfolio = Portfolio.objects.get(user=self.user)
        balance = portfolio.balance
        self.assertEqual(balance, 10000.00)        



class TradingViewTestCase(TestCase):

    def setUp(self):
        """Set up test user, create 15 transactions, login with a test client"""
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.portfolio = self.user.portfolio
        self.client = Client()
        self.client.login(username="testuser", password="testpassword")


    def _create_transactions(self, count: int):
        """Helper method to create Transaction objects"""
        symbols = [stock['symbol'] for stock in get_valid_symbols()[:count]] # Prepare a list of symbols
        return [
            Transaction.objects.create(user=self.user, stock_symbol=symbol,transaction_type='BUY', quantity=3, price=200.00,)
            for symbol in symbols
            ]
    

    def _create_holding(self, stock_symbol: str, quantity: int):
        """Helper method to create a StockHolding object"""
        return StockHolding.objects.create(portfolio=self.portfolio, stock_symbol=stock_symbol, quantity=quantity)

    
    def test_dashboard_view(self):
        """Test the dashboard page prior to loading stock prices"""
        # Create some transactions
        self._create_transactions(15)

        # GET the dashboard page (Page 1)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['stocks_data'])
        self.assertEqual(len(response.context['stocks_data']), 10)
        self.assertEqual(response.context['current_page'], 1)
        self.assertIsNone(response.context['previous_page_number'])
        self.assertEqual(response.context['next_page_number'], 2)

        # Check that the symbol 'AACT-U' was passed with the correct quantity
        self.assertContains(response, '<tr data-symbol="AACT-U" data-quantity="3">')
        self.assertNotContains(response, '<tr data-symbol="AAM-U" data-quantity="3">') # Should not be on Page 1

        # Test the second page
        response = self.client.get(reverse('dashboard'), {'page': 2})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['stocks_data'])
        self.assertEqual(len(response.context['stocks_data']), 5)        
        self.assertEqual(response.context['current_page'], 2)
        self.assertEqual(response.context['previous_page_number'], 1)
        self.assertIsNone(response.context['next_page_number'])

        # Check that the symbol 'AAM-U' was passed with the correct quantity
        self.assertContains(response, '<tr data-symbol="AAM-U" data-quantity="3">')
        self.assertNotContains(response, '<tr data-symbol="AACT-U" data-quantity="3">') # Should not be on Page 2


    def test_transactions_view(self):
        """Test the transactions view"""
        # Create some transactions
        self._create_transactions(15)

        # Create a new transaction
        time.sleep(0.01) # Delay to ensure timestamp is later
        transaction = Transaction.objects.create(user=self.user, stock_symbol='EXAMPLE', transaction_type='BUY', quantity=3, price=200.00)
        
        # Get the first page
        response = self.client.get(reverse('transactions'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['transactions_data']), 10)
        self.assertEqual(response.context['current_page'], 1)
        self.assertIsNone(response.context['previous_page_number'])
        self.assertEqual(response.context['next_page_number'], 2)
        # Check that the recent transaction is in the first page
        self.assertContains(response, f'<td class="stock-symbol" id="stock-symbol-{transaction.id}"')

        # Get the second page
        response = self.client.get(reverse('transactions'), {'page': 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['transactions_data']), 6)
        self.assertEqual(response.context['current_page'], 2)
        self.assertEqual(response.context['previous_page_number'], 1)
        self.assertIsNone(response.context['next_page_number'])
        # Check that the recent transaction is NOT in this page
        self.assertNotContains(response, f'<td class="stock-symbol" id="stock-symbol-{transaction.id}"')

    
    def test_buy_view_get(self):
        """Test that the buy page is rendered correctly for GET requests"""
        all_stocks = get_valid_symbols()
        # Get the first page
        response = self.client.get(reverse('buy'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['stocks']), 20) # 20 symbols per page
        self.assertEqual(response.context['current_page'], 1)
        self.assertIsNone(response.context['previous_page_number'])
        self.assertEqual(response.context['next_page_number'], 2)
        # Verify the symbols in the first page
        self.assertContains(response, f'data-symbol="{all_stocks[1]['symbol']}"')
        self.assertNotContains(response, f'data-symbol="{all_stocks[20]['symbol']}"')

        # Get the second page
        response = self.client.get(reverse('buy'), {'page': 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_page'], 2)
        self.assertEqual(response.context['previous_page_number'], 1)
        self.assertEqual(response.context['next_page_number'], 3)
        # Verify the symbols in the first page
        self.assertContains(response, f'data-symbol="{all_stocks[20]['symbol']}"')
        self.assertNotContains(response, f'data-symbol="{all_stocks[40]['symbol']}"')


    def test_buy_stock_success(self):
        """Test successful stock purchase"""
        response = self.client.post(
            reverse('buy'),
            json.dumps({'symbol': 'GOOGL', 'quantity': 10}),
            "application/json",
            HTTP_X_REQUESTED_WITH='XMLHttpRequest' # Simulate AJAX request
        )
        
        # Verify the response code and JSON
        self.assertEqual(response.status_code, 201)
        self.assertJSONEqual(response.content, {'message': 'Stock purchased successfully'})

        # Verify the transaction was created
        self.assertEqual(Transaction.objects.count(), 1)
        
        # Verify transaction details
        transaction = Transaction.objects.first()
        self.assertEqual(transaction.user, self.user)
        self.assertEqual(transaction.stock_symbol, 'GOOGL')
        self.assertEqual(transaction.quantity, 10)


    def test_buy_stock_insufficient_balance(self):
        """Test purchase failure due to insufficient balance"""
        response = self.client.post(
            reverse('buy'),
            json.dumps({'symbol': 'GOOGL', 'quantity': 500}), # Total likely to exceed default balance $10,000
            "application/json",
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'error': 'Insufficient balance'})
    

    def test_buy_stock_invalid_quantity(self):
        """Test purchase failure due to invalid quantity"""
        response = self.client.post(
            reverse('buy'),
            json.dumps({'symbol': 'GOOGL', 'quantity': 0}),
            "application/json",
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'error': 'Invalid quantity provided'})

    
    def test_buy_stock_invalid_json(self):
        """Test purchase failure due to invalid JSON"""
        response = self.client.post(
            reverse('buy'),
            'Invalid JSON Data',
            "application/json",
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'error': 'Invalid JSON'})
        self.assertEqual(Transaction.objects.count(), 0)


    def test_buy_stock_non_ajax_request(self):
        """Test purchase failure due to missing AJAX header"""
        response = self.client.post(
            reverse('buy'),
            json.dumps({'symbol': 'GOOGL', 'quantity': 10}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Transaction.objects.count(), 0)


    def test_sell_view_get(self):
        """Test that the Sell page renders correctly for GET requests"""
        # Create some holdings
        symbols = [stock['symbol'] for stock in get_valid_symbols()[:30]] # List of 20 symbols using helper function
        holdings = [self._create_holding(symbol, 10) for symbol in symbols]

        # Get the first page
        response = self.client.get(reverse('sell'))
        self.assertEqual(response.status_code, 200)
        # Check context data
        self.assertTrue(response.context['stocks_data'])
        self.assertEqual(response.context['current_page'], 1)
        self.assertEqual(response.context['next_page_number'], 2)
        self.assertIsNone(response.context['previous_page_number'])
        # Verify that expected symbols and quantities are shown
        self.assertContains(response, f'data-symbol="{symbols[0]}" data-quantity="10"')
        self.assertContains(response, f'data-symbol="{symbols[10]}" data-quantity="10"')
        self.assertNotContains(response, f'data-symbol="{symbols[20]}" data-quantity="10"')
        
        # Get the second page
        response = self.client.get(reverse('sell'), {'page': 2})
        self.assertEqual(response.status_code, 200)
        # Check context data
        self.assertTrue(response.context['stocks_data'])
        self.assertEqual(response.context['current_page'], 2)
        self.assertIsNone(response.context['next_page_number'])
        self.assertEqual(response.context['previous_page_number'], 1)
        # Verify that expected symbols and quantities are shown
        self.assertContains(response, f'data-symbol="{symbols[20]}" data-quantity="10"')
        self.assertContains(response, f'data-symbol="{symbols[29]}" data-quantity="10"')
        self.assertNotContains(response, f'data-symbol="{symbols[10]}" data-quantity="10"')


    def test_sell_stock_succcess(self):
        """Test successful stock sale"""
        holding = self._create_holding('GOOGL', 10)
        response = self.client.post(
            reverse('sell'),
            json.dumps({'symbol': 'GOOGL', 'quantity': 10}),
            "application/json",
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 201)
        self.assertJSONEqual(response.content, {'message': 'Stock(s) sold successfully!'})

        # Verify that a transaction was created
        self.assertEqual(Transaction.objects.count(), 1)
        
        # Verify transaction details
        transaction = Transaction.objects.first()
        self.assertEqual(transaction.user, self.user),
        self.assertEqual(transaction.stock_symbol, 'GOOGL'),
        self.assertEqual(transaction.quantity, 10)


    def test_sell_stock_excessive_quantity(self):
        """Test sale failure due to insufficient quantity owned"""
        holding = self._create_holding('GOOGL', 10)
        response = self.client.post(
            reverse('sell'),
            json.dumps({'symbol': 'GOOGL', 'quantity': 20}),
            "application/json",
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'error': 'You do not own 20 shares of GOOGL'})


    def test_sell_stock_invalid_quantity(self):
        """Test sale failure due to non-positive quantity"""
        holding = self._create_holding('GOOGL', 10)
        response = self.client.post(
            reverse('sell'),
            json.dumps({'symbol': 'GOOGL', 'quantity': -1}),
            "application/json",
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'error': 'Invalid quantity provided'})


    def test_sell_stock_foreign_holding(self):
        """Test sale failure when attempting to sell symbol not owned"""
        response = self.client.post(
            reverse('sell'),
            json.dumps({'symbol': 'GOOGL', 'quantity': 10}),
            "application/json",
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'error': 'You do not own any stock of GOOGL'})

    
    def test_sell_stock_invalid_json(self):
        """Test sale failure due to invalid JSON"""
        response = self.client.post(
            reverse('sell'),
            "Invalid JSON",
            "application/json",
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'error': 'Invalid JSON'})

    
    def test_sell_stock_non_ajax_request(self):
        """Test sale failure due to missing AJAX header"""
        holding = self._create_holding('GOOGL', 10)
        response = self.client.post(
            reverse('sell'),
            json.dumps({'symbol': 'GOOGL', 'quantity': 10}),
            "application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Transaction.objects.count(), 0)


    def test_sell_search_endpoint(self):
        """Test that search returns only stocks the user owns"""
        holding = self._create_holding('GOOGL', 10)
        # Search for a stock owned by the user
        response = self.client.get(
            reverse('sell_search'),
            {'q': 'GOOG'},
            "application/json",
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'stocks': [['GOOGL', 10]]})

        # Search for a stock the user doesn't own
        response = self.client.get(
            reverse('sell_search'),
            {'q': 'AAPL'},
            "application/json",
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'stocks': []})

        # No query given
        response = self.client.get(
            reverse('sell_search'),
            {},
            "application/json",
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'message': "Missing search query parameter 'q'"})