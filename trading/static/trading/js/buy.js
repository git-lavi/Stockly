document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.querySelector('#search-input');
    const searchButton = document.querySelector('#search-button');
    const stockRows = document.querySelectorAll('.stock-row');
    const buyButton = document.getElementById('buyButton');

    // Add event listeners to each stock row in the table
    stockRows.forEach(row => {
        const symbol = row.dataset.symbol;
        row.addEventListener('click', () => {
            openOverlay(symbol); 
        });
    });

    // SEARCH
    // Ensure the parent container is relative for correct positioning of search results
    const parentContainer = searchInput.parentNode;
    parentContainer.style.position = 'relative';

    const searchResults = document.createElement('div');
    Object.assign(searchResults.style, {
        position: 'absolute',
        top: '100%',
        left: '0',
        width: '100%',
        backgroundColor: '#fff',
        border: '1px solid #ced4da',
        zIndex: '10',
        maxHeight: '200px',
        overflowY: 'auto',
        borderTop: 'none',
    });

    parentContainer.appendChild(searchResults);

    // Live search on input
    searchInput.addEventListener('input', () => {
        const query = searchInput.value.trim();
        query ? searchStocks(query) : searchResults.innerHTML = '';
    });

    // Search on button click
    searchButton.addEventListener('click', () => {
        const query = searchInput.value.trim();
        if (query) searchStocks(query);
    });


    async function searchStocks(query) {
        searchResults.innerHTML = '';

        try {
            const response = await fetch(`/trading/search_stocks?q=${encodeURIComponent(query)}`);
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);

            const data = await response.json();

            if (data.stocks?.length) {
                const resultsList = document.createElement('ul');
                resultsList.style.listStyle = 'none';
                resultsList.style.padding = '0';
                resultsList.style.margin = '0';

                data.stocks.forEach(stock => {
                    const listItem = document.createElement('li');
                    listItem.textContent = `${stock.symbol} - ${stock.name}`;
                    Object.assign(listItem.style, {
                        padding: '8px',
                        cursor: 'pointer',
                    });

                    // Hover effect
                    listItem.addEventListener('mouseover', () => listItem.style.backgroundColor = '#f8f9fa');
                    listItem.addEventListener('mouseout', () => listItem.style.backgroundColor = '');

                    // Open buy menu on click
                    listItem.addEventListener('click', () => {
                        openOverlay(stock.symbol);
                    })

                    resultsList.appendChild(listItem);
                });

                searchResults.appendChild(resultsList);
            } else {
                searchResults.innerHTML = '<p style="padding: 8px; margin: 0;">No results found.</p>';
            }

        } catch (error) {
            console.error('Error fetching search results:', error);
            searchResults.innerHTML = '<p style="padding: 8px; margin: 0;">Error fetching results.</p>';
        }
    }

    // Function to close the overlay
    function closeOverlay() {
        document.getElementById('stockOverlay').style.display = 'none';
    }

    // Event listener for close button click
    document.getElementById('closeButton').addEventListener('click', closeOverlay);

    // Event listener for Esc key press
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            closeOverlay();
        }
    });

    function openOverlay(symbol) {
        document.getElementById('stockOverlay').style.display = 'block';
        buyButton.disabled = true;        
        getStockPrice(symbol);
    }

    async function getStockPrice(symbol) {
        document.getElementById('overlayStockSymbol').textContent = symbol;
        document.getElementById('overlayStockPrice').textContent = 'loading...';
        document.getElementById('quantity').value = '1';
        try {
            const response = await fetch(`/trading/get_price?symbol=${encodeURIComponent(symbol)}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (!response.ok) {
                console.error('Error fetching stock price:', error);
                closeOverlay();
                // Error alert
                const alertDiv = createAlert('warning', 'Error loading stock price. Please try again later.');
                document.getElementById('stockPriceAlert').innerHTML = '';
                document.getElementById('stockPriceAlert').appendChild(alertDiv);
            }

            const data = await response.json();

            // Update with stock data
            document.getElementById('overlayStockSymbol').textContent = data.symbol;
            document.getElementById('overlayStockPrice').textContent = `$${data.price}`;
            buyButton.disabled = false;

        } catch (error) {
            console.error('Error fetching stock price:', error);
            closeOverlay();
            // Error alert
            const alertDiv = createAlert('warning', 'Error loading stock price. Please try again later.');
            document.getElementById('stockPriceAlert').innerHTML = '';
            document.getElementById('stockPriceAlert').appendChild(alertDiv);

        }

    }


    // Event listener for Buy button click
    buyButton.addEventListener('click', () => {
        const symbol = document.getElementById('overlayStockSymbol').textContent;
        const quantity = document.getElementById('quantity').value;
        buyButton.disabled = true;
        sendBuyRequest(symbol, quantity);
    });

    // Function to send POST request to buy view
    async function sendBuyRequest(symbol, quantity) {
        try {
            const response = await fetch('/trading/buy', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken') // Include CSRF token
                },
                body: JSON.stringify({ symbol: symbol, quantity: quantity })
            });

            if (!response.ok) {
                closeOverlay();
                const data = await response.json();
                const alertDiv = createAlert('danger', data.error);
                document.getElementById('stockPriceAlert').innerHTML = '';
                document.getElementById('stockPriceAlert').appendChild(alertDiv);
            
            } else {
                // Handle successful purchase (e.g., update UI, display confirmation)
                console.log('Purchase successful!');
                closeOverlay();
                searchInput.textContent = '';
                // Update the user's balance
                userBalance = document.getElementById('user-balance');
                if (userBalance) {
                    fetchUserBalance();
                }
                async function fetchUserBalance() {
                    try {
                        const response = await fetch(`/trading/get_balance`, {
                            method: 'GET',
                            headers: {
                                'X-Requested-With': 'XMLHttpRequest'
                            }
                        });
                        if (!response.ok) {
                            throw new Error(`HTTP error! Status: ${response.status}`);
                        }
                        const data = await response.json();
                        // Update user balance
                        userBalance.textContent = `My Balance: $${data.balance}`;
                    } catch (error) {
                        console.error('Error fetching balance:', error);
                        alert('An error occurred while fetching your balance. Please try again.');
                    }
                }
         
                // Success alert
                const alertDiv = createAlert('success', 'Stock(s) purchased successfully!');
                document.getElementById('stockPriceAlert').innerHTML = '';
                document.getElementById('stockPriceAlert').appendChild(alertDiv);
                }
            } catch (error) {
                console.error('Error buying stock:', error);
                const alertDiv = createAlert('danger', 'An unknown error occurred. Please try again later')
                document.getElementById('stockPriceAlert').innerHTML = '';
                document.getElementById('stockPriceAlert').appendChild(alertDiv);
            }
        }

    // Helper function to create an alert
    function createAlert(type, message) {
        const alertDiv = document.createElement('div');
        alertDiv.classList.add('alert', `alert-${type}`, 'alert-dismissible', 'fade', 'show');
        alertDiv.setAttribute('role', 'alert');
        alertDiv.innerHTML = message;
        return alertDiv;
    }

    // Helper function to get CSRF token (from Django documentation)
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

});