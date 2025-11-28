// Utility functions
class Utils {
    static formatCard(cardId) {
        const suits = ['♦', '♥', '♠', '♣'];
        const suitNames = ['Oros', 'Copas', 'Espadas', 'Bastos'];
        const suitIndex = Math.floor((cardId - 1) / 10);
        const value = ((cardId - 1) % 10) + 1;
        
        let displayValue = value;
        if (value === 8) displayValue = 'J';
        if (value === 9) displayValue = 'Q'; 
        if (value === 10) displayValue = 'K';
        
        return {
            value: displayValue,
            suit: suits[suitIndex],
            suitName: suitNames[suitIndex],
            isRed: suitIndex <= 1,
            fullName: `${displayValue} di ${suitNames[suitIndex]}`
        };
    }

    static showNotification(message, type = 'info') {
        // Rimuovi notifiche esistenti
        const existingNotifications = document.querySelectorAll('.notification');
        existingNotifications.forEach(notif => notif.remove());

        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            background: ${type === 'error' ? '#e74c3c' : type === 'success' ? '#2ecc71' : '#3498db'};
            color: white;
            border-radius: 5px;
            z-index: 1001;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 3000);
    }

    static formatScore(scores) {
        return Object.entries(scores).map(([player, score]) => 
            `${player}: ${score}`
        ).join(' | ');
    }

    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}
