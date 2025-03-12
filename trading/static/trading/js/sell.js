document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.getElementById("searchStock");
    const resultsContainer = document.getElementById("searchResults");
    const sellOverlay = document.getElementById("sellOverlay");
    const overlayStockSymbol = document.getElementById("overlayStockSymbol");
    const overlayStockPrice = document.getElementById("overlayStockPrice");
    const overlayStockOwned = document.getElementById("overlayStockOwned");
    const quantityInput = document.getElementById("quantity");
    const sellButton = document.getElementById("sellButton");
    const closeButton = document.getElementById("closeButton");
    let debounceTimeout;


    // Function to fetch search results
    async function fetchSearchResults(query) {
        if (!query) {
            resultsContainer.innerHTML = "";
            return;
        }

        try {
            const response = await fetch(`/trading/sell_search?q=${query}`, {
                headers: { "X-Requested-With": "XMLHttpRequest" }
            });
            const data = await response.json();
            resultsContainer.innerHTML = "";
            if (data.stocks && data.stocks.length > 0) {
                data.stocks.forEach(stock => {
                    const item = document.createElement("div");
                    item.classList.add("search-result-item");
                    
                    // Style the search result
                    Object.assign(item.style, {
                        padding: '8px',
                        cursor: 'pointer',
                    });
                    item.addEventListener('mouseover', () => item.style.backgroundColor = '#f8f9fa');
                    item.addEventListener('mouseout', () => item.style.backgroundColor = '');
                    
                    item.textContent = stock[0];
                    item.addEventListener("click", () => openSellOverlay(stock[0], stock[1]));
                    resultsContainer.appendChild(item);
                });
            } else {
                resultsContainer.innerHTML = `<div class="no-results">${data.message || "No stocks found"}</div>`;
            }
        } catch (error) {
            console.error("Error fetching search results:", error);
        }
    }

    // Debounced search handler
    searchInput.addEventListener("input", () => {
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(() => {
            fetchSearchResults(searchInput.value.trim());
        }, 300);
    });

    // Open overlay for selling
    async function openSellOverlay(symbol, quantity) {
        sellButton.disabled = true;
        overlayStockPrice.textContent = 'loading...';
        sellOverlay.style.display = "block";
        overlayStockSymbol.textContent = symbol;
        overlayStockOwned.textContent = quantity;
        document.getElementById('quantity').value = '1';
        
        try {
            const response = await fetch(`/trading/get_price?symbol=${encodeURIComponent(symbol)}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (!response.ok) {
                const data = await response.json();
                overlayStockPrice.textContent = 'Unavailable';
                sellOverlay.style.display = 'none';
                const alertDiv = createAlert('warning', data.error);
                document.getElementById('alert').innerHTML = '';
                document.getElementById('alert').appendChild(alertDiv);
            }
            
            const data = await response.json();
            overlayStockPrice.textContent = `$${data.price}`
            if (!data.error) { // If no error, enable the Sell button
                sellButton.disabled = false;
            }
        } catch (error) {
            console.error("Error fetching stock price:", error);
            overlayStockPrice.textContent = "Unavailable";
        }
    }

    // Close overlay
    closeButton.addEventListener("click", () => {
        sellOverlay.style.display = "none";
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            sellOverlay.style.display = "none";
        }
    });

    // Click row to open sell overlay
    document.querySelectorAll(".stock-row").forEach(row => {
        row.addEventListener("click", () => {
            openSellOverlay(row.dataset.symbol, row.dataset.quantity);
        });
    });

    // Handle sell action
    sellButton.addEventListener("click", async () => {
        const symbol = overlayStockSymbol.textContent;
        const quantity = quantityInput.value;
        sellButton.disabled = true; // Disable so user doesn't make multiple requests
        try {
            const response = await fetch("/trading/sell", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    'X-Requested-With': 'XMLHttpRequest',
                    "X-CSRFToken": getCookie('csrftoken'),
                },
                body: JSON.stringify({ symbol, quantity })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                sellOverlay.style.display = "none";
                sessionStorage.setItem("successMessage", data.message);
                location.reload();

                // Show success alert
                const alertDiv = createAlert('success', data.message);
                document.getElementById('alert').innerHTML = '';
                document.getElementById('alert').appendChild(alertDiv);
            }
            else {
                sellOverlay.style.display = "none";
                // Show error alert
                const alertDiv = createAlert('danger', data.error);

                document.getElementById('alert').innerHTML = '';
                document.getElementById('alert').appendChild(alertDiv);
            }
        } catch (error) {
            console.error("Error processing sell request:", error);
            
            // Show error alert
            const alertDiv = createAlert('danger', 'An unknown error occurred. Please try again later.');
            document.getElementById('alert').innerHTML = '';
            document.getElementById('alert').appendChild(alertDiv);
        }
    });


    // Helper function to create an alert
    function createAlert(type, message) {
        const alertDiv = document.createElement('div');
        alertDiv.classList.add('alert', `alert-${type}`, 'alert-dismissible', 'fade', 'show');
        alertDiv.setAttribute('role', 'alert');
        alertDiv.innerHTML = message;
        return alertDiv;
    }

    // Check if session storage stored message before page reload
    const successMessage = sessionStorage.getItem("successMessage");
    if (successMessage) {
        const alertDiv = createAlert('success', successMessage);
        document.getElementById('alert').innerHTML = '';
        document.getElementById('alert').appendChild(alertDiv);

        // Clear the message after displaying it
        sessionStorage.removeItem("successMessage");
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
