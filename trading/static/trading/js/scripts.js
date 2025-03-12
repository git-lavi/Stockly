document.addEventListener('DOMContentLoaded', () => {

    // Get the user's balance
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

    // Function to dismiss alerts after 2.5 seconds
    function dismissAlert(alert) {
        setTimeout(() => {
            alert.classList.remove('show');
            alert.classList.add('hide');
        }, 2500); // 2.5 seconds
    }

    // Select existing dismissible alerts
    const alerts = document.querySelectorAll('.alert-dismissible.fade.show');
    alerts.forEach(alert => dismissAlert(alert));

    // Set up MutationObserver to detect new alerts
    const observer = new MutationObserver(mutations => {
        mutations.forEach(mutation => {
            mutation.addedNodes.forEach(node => {
                // Check if the added node is an alert
                if (node.matches && node.matches('.alert-dismissible.fade.show')) {
                    dismissAlert(node);
                }
            });
        });
    });

    // Observe changes in the body (or a parent container of the alerts)
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
});
