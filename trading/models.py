from django.db import models
from django.contrib.auth.models import User
from django.db import transaction
from django.core.exceptions import ValidationError
from decimal import Decimal

# Create your models here.

class Transaction(models.Model):
    BUY = 'BUY'
    SELL = 'SELL'
    TRANSACTION_TYPES = [
        (BUY, 'Buy'),
        (SELL, 'Sell'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    stock_symbol = models.CharField(max_length=10)
    transaction_type = models.CharField(max_length=4, choices=TRANSACTION_TYPES)
    quantity = models.PositiveSmallIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Use atomic transactions for consistency
        with transaction.atomic():
            self.total = Decimal(self.quantity) * Decimal(self.price)
            self.stock_symbol = self.stock_symbol.upper()
            super().save(*args, **kwargs) # Save the Transaction object

            # Get the user's portfolio
            portfolio = Portfolio.objects.get(user=self.user)

            # Get or create the stock holding
            holding, created = StockHolding.objects.get_or_create(portfolio=portfolio, stock_symbol=self.stock_symbol)

            # Handle transaction types
            if self.transaction_type == 'BUY':
                # Ensure user has enough balance for the purchase
                if portfolio.balance < self.total:
                    raise ValidationError("Insufficient balance to complete the purchase.")

                # Deduct balance for the purchase
                portfolio.balance -= self.total
                portfolio.save()
                
                # Increase the stock holding quantity
                holding.quantity += self.quantity
                holding.save()
            
            else:
                # Ensure user has enough stock to sell
                if holding.quantity < self.quantity:
                    raise ValidationError(f"Insufficient quantity of {self.stock_symbol} to sell.")

                # Add balance for the sale
                portfolio.balance += self.total
                portfolio.save()
                
                # Decrease the stock holding quantity
                holding.quantity -= self.quantity
                if holding.quantity == 0:
                    holding.delete()
                else:
                    holding.save()

    def __str__(self):
        return f"{self.user.username} {self.transaction_type} {self.quantity} of {self.stock_symbol} at {self.price}"
    

class Portfolio(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='portfolio')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=10000.00)

    def __str__(self):
        return f"{self.user.username}'s Portfolio"


class StockHolding(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='holdings')
    stock_symbol = models.CharField(max_length=10)
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['portfolio', 'stock_symbol'], name='unique_stock_holding')
        ]

    def __str__(self):
        return f"{self.portfolio.user.username}'s {self.stock_symbol}: {self.quantity} shares"
    
    