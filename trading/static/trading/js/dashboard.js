document.addEventListener('DOMContentLoaded', function () {
    const tableRows = document.querySelectorAll('#stocks-table-body tr');
    const totalStockValueElement = document.getElementById('total-stock-value');
    let totalStockValue = 0;
    let stocksProcessed = 0;
    let totalStocks = tableRows.length;
    let encounteredError = false;

    // Function to format the price value
    function formatPrice(price) {
        return price ? `${parseFloat(price).toFixed(2)}` : 'N/A';
    }

    // Function to update the total stock value
    function finalizeTotalStockValue() {
        totalStockValueElement.querySelector('.spinner-border').classList.add('d-none');
        totalStockValueElement.innerHTML += encounteredError ? 'N/A' : `$${totalStockValue.toFixed(2)}`;
    }

    // Function to create an alert
    function createAlert(type, message) {
        const alertDiv = document.createElement('div');
        alertDiv.classList.add('alert', `alert-${type}`, 'alert-dismissible', 'fade', 'show');
        alertDiv.setAttribute('role', 'alert');
        alertDiv.innerHTML = message;
        return alertDiv;
    }

    if (tableRows.length === 0) {
        totalStockValueElement.textContent = 'N/A';
    }

    // Loop through each row and fetch stock data
    tableRows.forEach(row => {
        const symbol = row.getAttribute('data-symbol');
        const quantity = row.getAttribute('data-quantity');

        fetch(`/trading/get_price?symbol=${symbol}`, {
            method: 'GET',
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(response => response.json())
        .then(data => {
            const fields = {
                'open-price': data.open,
                'previous-close': data.previous_close,
                'price': data.price,
                'total': data.price * quantity
            };

            Object.keys(fields).forEach(className => {
                const cell = row.querySelector(`.${className}`);
                const spinner = cell.querySelector('.spinner-border');
                const priceValue = cell.querySelector('.price-value');

                spinner.classList.add('d-none'); // Hide spinner
                priceValue.classList.remove('d-none'); // Show value

                priceValue.textContent = data.error ? 'N/A' : formatPrice(fields[className]);
            });

            if (!data.error) {
                totalStockValue += fields.total;
            } else {
                encounteredError = true;
            }
        })
        .catch(() => {
            encounteredError = true;
            row.querySelectorAll('.spinner-border').forEach(spinner => spinner.classList.add('d-none'));
            row.querySelectorAll('.price-value').forEach(value => {
                value.classList.remove('d-none');
                value.textContent = 'N/A';
            });
        })
        .finally(() => {
            stocksProcessed++;
            if (stocksProcessed === totalStocks) {
                finalizeTotalStockValue();
            }
            if (encounteredError) {
                const alertDiv = createAlert('warning', 'Error fetching prices for one or more stock. Please try again later.');
                document.getElementById('alert').innerHTML = '';
                document.getElementById('alert').appendChild(alertDiv);
            }
        });
    });
});
