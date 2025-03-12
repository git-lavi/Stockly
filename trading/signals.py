from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Portfolio

@receiver(post_save, sender=User)
def create_user_portfolio(sender, instance, created, **kwargs):
    """Automatically create a portfolio for each new user"""
    if created:
        Portfolio.objects.create(user=instance)