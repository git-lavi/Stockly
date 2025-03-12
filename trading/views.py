from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.contrib.auth import login, logout, authenticate, decorators
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.core.paginator import Paginator
from .models import User, Transaction, Portfolio, StockHolding
from .utils import get_stock_price_data, format_price, get_valid_symbols

import json
import requests
import os


# Login view handled by Django

def register(request: HttpRequest):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        if request.user.is_authenticated:
            return redirect('dashboard')
        form = UserCreationForm()
    return render(request, 'trading/register.html', {'form': form})


def logout_view(request: HttpRequest):
    logout(request)
    return redirect('login')


def index(request: HttpRequest):
    if request.user.is_authenticated:
        return redirect('dashboard')
    else:
        return redirect('login')
    

@login_required
@require_GET
def get_balance(request: HttpRequest):
    """Gets the user's cash balance. For AJAX"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return HttpResponseBadRequest()
    # Get the user's balance object
    balance = Portfolio.objects.get(user=request.user).balance
    formatted_balance = f"{balance:.2f}" # Convert to str with 2 decimal places
    return JsonResponse({'balance': formatted_balance}, status=200)


@login_required
@require_GET
def dashboard(request: HttpRequest):
    # Retrieve the stock symbols owned by the user
    portfolio = Portfolio.objects.get(user=request.user)
    holdings = StockHolding.objects.filter(portfolio=portfolio).values('stock_symbol', 'quantity').order_by("stock_symbol")

    stocks_data = []
    for holding in holdings:
        stock_data = {
            'symbol': holding['stock_symbol'],
            'quantity': holding['quantity'],
        }
        stocks_data.append(stock_data)

    # Paginate
    paginator = Paginator(stocks_data, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    stocks_data = [stock_data for stock_data in page_obj]
    
    return render(request, 'trading/dashboard.html', {
        'stocks_data': stocks_data,
        'current_page': page_obj.number,
        'previous_page_exists': page_obj.has_previous(),
        'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
        'next_page_exists': page_obj.has_next(),
        'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
    })
    

@login_required
@require_GET
def transactions(request: HttpRequest):
    """Loads a page containing the user's transaction history"""
    transactions = Transaction.objects.filter(user=request.user).order_by("-timestamp").all()
    paginator = Paginator(transactions, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    transactions_data = [transaction for transaction in page_obj]
    return render(request, "trading/transactions.html", {
        'transactions_data': transactions_data,
        'current_page': page_obj.number,
        'previous_page_exists': page_obj.has_previous(),
        'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
        'next_page_exists': page_obj.has_next(),
        'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
    })


@login_required
@require_GET
def get_price(request: HttpRequest):
    """Return the stock price of a symbol"""
    # AJAX requests only
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        symbol = request.GET.get('symbol')
        try:
            # Retrieve current, open, and previous close prices from API
            price_data = get_stock_price_data(symbol)
            price = price_data['05. price']
            open_price = price_data['02. open']
            close_price = price_data['08. previous close']
            return JsonResponse({
                'symbol': symbol,
                'price': price,
                'open': open_price,
                'previous_close': close_price,
            }, status=200)
        except Exception:
            return JsonResponse({'error': 'Error fetching price'}, status=500)
    else:
        return HttpResponseBadRequest()
    


@require_GET
def search_stocks(request: HttpRequest):
    """Returns a list of valid stock symbols matching the search query in JSON format"""
    q = request.GET.get('q')
    if q:
        all_stocks = get_valid_symbols()
        # Loop through all stocks to check if the query is found in stock symbol or name
        stocks = [s for s in all_stocks if q.lower() in s['symbol'].lower() or q.lower() in s['name'].lower()][:10] # Return first five results
        
        if stocks:
            return JsonResponse({'stocks': stocks}, status=200)
        else:
            return JsonResponse({'message': f"No stocks found for '{q}'", 'stocks':[]}, status=200)
    else:
        return JsonResponse({'message': "Missing search query parameter 'q'"}, status=400)


@login_required
@require_http_methods(['GET', 'POST'])
def buy(request: HttpRequest):
    """
    GET: Load the Buy page,
    POST: Purchase new stock
    """
    if request.method == 'POST':
        # Only accept AJAX requests
        if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
            return HttpResponseBadRequest()
        try:
            data = json.loads(request.body)
            symbol = data['symbol']
            quantity = int(data['quantity'])
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except (KeyError, ValueError):
            return JsonResponse({'error': 'Invalid or missing data'}, status=400)
        
        # Verify that quantiity is valid
        if quantity <= 0:
            return JsonResponse({'error': 'Invalid quantity provided'}, status=400)

        # Get the actual stock price
        try:
            price = float(get_stock_price_data(symbol)['05. price'])
        except Exception:
            return JsonResponse({'error': 'Failed to fetch stock price. Please try again later'}, status=500)
        
        # Get user's portfolio
        portfolio = get_object_or_404(Portfolio, user=request.user)
        balance = portfolio.balance

        if balance < quantity * price:
            return JsonResponse({'error': 'Insufficient balance'}, status=400)
        
        # Perform the transaction
        try:
            Transaction.objects.create(
            user=request.user,
            stock_symbol=symbol,
            transaction_type='BUY',
            quantity=quantity,
            price=price
            )
        except Exception:
            return JsonResponse({'error': 'An error occurred while buying stock. Please try again later'}, status=500)
        
        return JsonResponse({'message': 'Stock purchased successfully'}, status=201)

    else:
        # Render page for GET requests
        stocks = get_valid_symbols()
        paginator = Paginator(stocks, 20)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        stocks_data = [{'symbol': item['symbol'], 'name': item['name']} for item in page_obj]
        
        return render(request, "trading/buy.html", {
            'stocks': stocks_data,
            'current_page': page_obj.number,
            'previous_page_exists': page_obj.has_previous(),
            'previous_page_number': page_obj.number - 1 if page_obj.has_previous() else None,
            'next_page_exists': page_obj.has_next(),
            'next_page_number': page_obj.number + 1 if page_obj.has_next() else None,
        })


@login_required
@require_http_methods(['GET', 'POST'])
def sell(request: HttpRequest):
    """
    GET: Load the Sell page
    POST: Sell stock
    """
    if request.method == 'POST':
        # Only accept AJAX requests
        if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
            return HttpResponseBadRequest()
        
        # Extract the stock symbol and quantity
        try:
            data = json.loads(request.body)
            symbol = data['symbol']
            quantity = int(data['quantity'])
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except (KeyError, ValueError):
            return JsonResponse({'error': 'Invalid or missing data'}, status=400)
                
        # Get the user's holdings
        portfolio = Portfolio.objects.get(user=request.user)
        holdings = StockHolding.objects.filter(portfolio=portfolio, stock_symbol=symbol).first()
        if not holdings:
            return JsonResponse({'error': f'You do not own any stock of {symbol}'}, status=400)

        # Ensure quantity provided is valid
        quantity_owned = holdings.quantity
        if quantity > quantity_owned:
            return JsonResponse({'error': f'You do not own {quantity} shares of {symbol}'}, status=400)
        elif quantity <= 0:
            return JsonResponse({'error': 'Invalid quantity provided'}, status=400)
        
        # Get stock price
        try:
            price = float(get_stock_price_data(symbol)['05. price'])
        except Exception:
            return JsonResponse({'error': 'Failed to fetch stock price. Please try again later'}, status=500)
        
        # Perform the transaction
        try:
            Transaction.objects.create(
            user=request.user,
            stock_symbol=symbol,
            transaction_type='SELL',
            quantity=quantity,
            price=price
            )
        except Exception:
            return JsonResponse({'error': 'An error occurred when selling stock. Please try again later'}, status=500)
        
        return JsonResponse({'message': 'Stock(s) sold successfully!'}, status=201)

    else:
        # Get user portfolio and holdings
        portfolio = Portfolio.objects.get(user=request.user)
        holdings = StockHolding.objects.filter(portfolio=portfolio).values('stock_symbol', 'quantity').order_by('stock_symbol')
        
        # Paginate the holdings
        paginator = Paginator(holdings, 20)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        stocks_data = [
            {
                'symbol': holding['stock_symbol'],
                'quantity': holding['quantity'],
            }
            for holding in page_obj
        ]

        return render(request, 'trading/sell.html', {
            'stocks_data': stocks_data,
            'current_page': page_obj.number,
            'previous_page_exists': page_obj.has_previous(),
            'previous_page_number': page_obj.number - 1 if page_obj.has_previous() else None,
            'next_page_exists': page_obj.has_next(),
            'next_page_number': page_obj.number + 1 if page_obj.has_next() else None,
        })


@login_required
@require_GET
def sell_search(request: HttpRequest):
    """Search for stocks owned by a user"""
    # Only accept AJAX requests
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return HttpResponseBadRequest()
    
    q = request.GET.get('q', '').strip()
    if q:
        portfolio = Portfolio.objects.get(user=request.user)
        stocks = StockHolding.objects.filter(portfolio=portfolio, stock_symbol__icontains=q).values_list('stock_symbol', 'quantity')
        return JsonResponse({'stocks': list(stocks)}, status=200)
    else:
        return JsonResponse({'message': "Missing search query parameter 'q'"}, status=400)