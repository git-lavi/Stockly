from django.urls import path, reverse_lazy
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Login handled by Django
    path("login", auth_views.LoginView.as_view(redirect_authenticated_user=True), name="login"),

    # Logout
    path("logout", views.logout_view, name="logout"),

    # Register a new user
    path("register", views.register, name="register"),

    path("change_password", auth_views.PasswordChangeView.as_view(
        template_name="registration/password_change.html",
        success_url=reverse_lazy("dashboard"),
    ), name="change_password"),

    # Index view
    path("", views.index, name="index"),

    # API: Fetch user's balance
    path("get_balance", views.get_balance, name="get_balance"),

    # User Dashboard
    path("dashboard", views.dashboard, name="dashboard"),

    # Transaction history page
    path("transactions", views.transactions, name="transactions"),

    # Buy page
    path("buy", views.buy, name="buy"),

    # API: Search for stocks in Buy page
    path("search_stocks", views.search_stocks, name="search_stocks"),

    # Get stock price for a symbol
    path("get_price", views.get_price, name="get_price"),

    # Sell page
    path("sell", views.sell, name="sell"),

    # API: Search for owned stocks in Sell page
    path("sell_search", views.sell_search, name="sell_search"),

]
