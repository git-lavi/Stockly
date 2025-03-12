# Stockly

## Overview

Stockly is a project housing a web application called Trading, that simulates stock trading, allowing users to buy and sell stocks using virtual money. It provides real-time stock price updates, portfolio management, and transaction history tracking. Built with Django for the backend and JavaScript for frontend interactions, it offers an engaging experience for users interested in stock trading without financial risk.

## Video Demo

[Watch on YouTube](https://youtu.be/YH6Af_83hgM)

## Installation and Usage

### Prerequisites

- [Git](https://git-scm.com/downloads)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Alpha Vantage API key](https://www.alphavantage.co/support/#api-key)

Ensure that you install the appropriate versions of Git and Docker Desktop for your system and obtain an Alpha Vantage API key before proceeding.

### Installation

1. Clone the repository:

    ```bash
    git clone <repository_url>
    ```
    Navigate into the project directory:
    
    ```bash    
    cd stockly
    ```

2. Open the `.env` file and replace `your_api_key` with your actual Alpha Vantage API key:
    
    ```bash
    ALPHA_VANTAGE_API_KEY="your_api_key"
    ```

3. Build and start the containers in the background:

    ```bash
    docker-compose up -d --build
    ```
    **Note:** Ensure that Docker Desktop is running before executing this command.

4. Apply database migrations:

    ```bash
    docker-compose exec web python manage.py makemigrations
    ```
    
    Then, apply the migrations:
    
    ```bash
    docker-compose exec web python manage.py migrate
    ```

5. Access the application at [http://localhost:8000/trading](http://localhost:8000/trading).

### Stopping the Application

When you are done using the application, stop all containers with:

```bash
docker-compose stop
```

### Usage

Refer to the [Video Demo](#video-demo) section for a walkthrough of the application.

### Important Note

The free Alpha Vantage API key allows only a limited number of requests per day. If you exceed the limit, stock prices cannot be fetched, which will affect the Dashboard, Buy, and Sell pages. When this happens, you will receive an alert indicating that prices could not be retrieved and suggesting that you try again later.

## Distinctiveness and Complexity

Stockly stands out from other CS50W projects due to its real-time stock price integration, interactive UI, complex transaction handling, and Docker containerization. Key features include:

- **Portfolio Management:** Tracks each user's balance and stock holdings.
- **Stock Transactions:** Enables users to buy and sell stocks with real-time price retrieval.
- **Database Setup:** Uses PostgreSQL instead of Django's default SQLite database.
- **Data Integrity:** Employs atomic transactions to prevent data corruption.
- **Frontend Interactivity:** JavaScript updates stock prices dynamically.
- **Automated Testing:** Includes unit tests for models and views.
- **Real-time API:** Uses Alpha Vantage to fetch live stock prices.
- **Containerization:** Docker ensures consistent deployment across platforms.

## Project Structure

The project directory includes the following key components:

- **stockly/**: Django project directory containing configuration files.
- **trading/**: Django app handling stock trading logic.
- **.env**: Stores environment variables for the `web` container.
- **docker-compose.yml**: Defines the Docker containers and services.
- **Dockerfile**: Instructions for building the `web` container.
- **manage.py**: Django's command-line utility for administrative tasks.
- **requirements.txt**: Lists required Python packages.

Inside the **trading** app:

- **data/**: Contains supporting data files.
- **migrations/**: Tracks database migrations.
- **static/**: Holds static files (CSS and JavaScript).
- **templates/**: Stores HTML templates.
- **models.py**: Defines database models.
- **signals.py**: Ensures automatic portfolio creation for new users.
- **tests.py**: Contains unit tests.
- **urls.py**: Defines application routes.
- **views.py**: Implements view functions.

## Design Decisions

### Backend (Django)

- Uses Django's ORM to manage users, portfolios, transactions, and stock holdings.
- Employs PostgreSQL for structured data storage.
- Retrieves real-time stock prices via an external API.

### Frontend (HTML, CSS, JavaScript)

- JavaScript dynamically fetches stock prices and validates transactions.
- Bootstrap provides a responsive and clean UI.
- Custom CSS is used for additional styling enhancements.

### Database Structure

- **Portfolio:** Each user has a personal portfolio tracking their cash balance.
- **Stock Transactions:** Logs every buy/sell transaction with timestamps.
- **Holdings:** Maintains stock ownership records, updating after each transaction.

## Mobile Responsiveness

Stockly uses Bootstrap to ensure a fully responsive experience across different devices.

## Acknowledgments

- Developed as the final project for **CS50’s Web Programming with Python and JavaScript** (CS50W) offered by Harvard University on edX.
- Uses the Alpha Vantage API for real-time stock data.
- UI styling with Bootstrap.
- Search icon sourced from Google’s Material Icons pack.
