class Utils {
  static formatCard(cardId) {
    // Spanish deck: 4 suits x 10 cards = 40 cards
    // cardId: 1-40
    // Suits: oro, copa, espada, basto (in order)
    // Values per suit: 1, 2, 3, 4, 5, 6, 7, sota, caballo, rey

    const suits = ["oro", "copas", "espadas", "bastos"]
    const suitNames = ["Golds", "Cups", "Swords", "Clubs"]
    const suitSymbols = ["./images/oros.png","./images/copas.png","./images/espadas.png","./images/bastos.png"]

    // Calculate suit and value
    const suitIndex = Math.floor((cardId - 1) / 10)
    const valueInSuit = ((cardId - 1) % 10) + 1 // 1-10

    const suit = suits[suitIndex]
    const suitName = suitNames[suitIndex]
    const suitSymbol = suitSymbols[suitIndex]

    let displayValue = valueInSuit
    let cardFileName = ""
    let fullName = ""

    // Map values to filenames
    if (valueInSuit >= 1 && valueInSuit <= 7) {
      // Numeric cards: 1-7
      cardFileName = `${valueInSuit}_${suit}.png`
      fullName = `${valueInSuit} of ${suitName}`
      displayValue = valueInSuit
    } else if (valueInSuit === 8) {
      // Sota (Jack)
      cardFileName = `sota_${suit}.png`
      fullName = `Jack of ${suitName}`
      displayValue = "J"
    } else if (valueInSuit === 9) {
      // Caballo (Knight)
      cardFileName = `caballo_${suit}.png`
      fullName = `Knight of ${suitName}`
      displayValue = "K"
    } else if (valueInSuit === 10) {
      // Rey (King)
      cardFileName = `rey_${suit}.png`
      fullName = `King of ${suitName}`
      displayValue = "R"
    }

    const imagePath = `/carts/${cardFileName}`

    return {
      value: displayValue,
      suit: suitSymbol,
      suitName: suitName,
      isRed: suitIndex === 0 || suitIndex === 1, // oro & copas are red
      fullName: fullName,
      imagePath: imagePath,
      cardId: cardId,
    }
  }

  static showNotification(message, type = "info") {
    const existingNotifications = document.querySelectorAll(".notification")
    existingNotifications.forEach((notif) => notif.remove())

    const notification = document.createElement("div")
    notification.className = `notification ${type}`
    notification.textContent = message

    const colors = {
      error: "#ef4444",
      success: "#22c55e",
      info: "#3b82f6",
      warning: "#f59e0b",
    }

    notification.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            padding: 1rem 1.5rem;
            background: ${colors[type] || colors.info};
            color: white;
            border-radius: 0.5rem;
            z-index: 1001;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            font-weight: 600;
            animation: slideIn 0.3s ease;
        `

    document.body.appendChild(notification)

    setTimeout(() => {
      if (notification.parentNode) {
        notification.style.animation = "slideOut 0.3s ease"
        setTimeout(() => notification.remove(), 300)
      }
    }, 3000)
  }

  static formatScore(scores) {
    return Object.entries(scores)
      .map(([player, score]) => `${player}: ${score}`)
      .join(" | ")
  }

  static debounce(func, wait) {
    let timeout
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout)
        func(...args)
      }
      clearTimeout(timeout)
      timeout = setTimeout(later, wait)
    }
  }
}

const style = document.createElement("style")
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`
document.head.appendChild(style)