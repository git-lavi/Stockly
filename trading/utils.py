# File to store helper functions for views.py
from django.contrib.auth.models import User



import requests
import os
import csv


def get_stock_price_data(symbol: str):
    """
    Fetches stock price data for the given stock symbols.

    Returns: A dictionary containing stock price data for the symbol
    """
    api_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
    url = 'https://www.alphavantage.co/query'
    params = {
        'function': 'GLOBAL_QUOTE',
        'symbol': symbol,
        'apikey': api_key
    }
    response = requests.get(url, params)
    price_data = response.json()['Global Quote'] # API contains price data inside 'Global Quote'
    return price_data


def format_price(price: str):
    """Return a formatted string for a given str 'price', rounded to exactly two decimal places"""
    return format(round(float(price), 2), '.2f')


def get_valid_symbols():
    """Return active stock symbols from a listings file"""
    with open("/code/trading/data/listing_status.csv", "r") as file:
        reader = csv.DictReader(file)
        stocks = [
            {
            'symbol': row['symbol'],
            'name': row['name'] if len(row['name']) < 50 else row['name'][:50]+'...',
            }
            for row in reader if row['assetType'] == 'Stock'
        ]
    return stocks