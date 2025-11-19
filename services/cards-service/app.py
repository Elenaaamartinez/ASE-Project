from flask import Flask, jsonify

app = Flask(__name__)

# Spanish deck data (40 cards)
SPANISH_DECK = [
    # Oros (Coins)
    {"id": 1, "name": "1 de Oros", "suit": "Oros", "value": 1, "points": 1, "image": "1_oros.png"},
    {"id": 2, "name": "2 de Oros", "suit": "Oros", "value": 2, "points": 2, "image": "2_oros.png"},
    {"id": 3, "name": "3 de Oros", "suit": "Oros", "value": 3, "points": 3, "image": "3_oros.png"},
    {"id": 4, "name": "4 de Oros", "suit": "Oros", "value": 4, "points": 4, "image": "4_oros.png"},
    {"id": 5, "name": "5 de Oros", "suit": "Oros", "value": 5, "points": 5, "image": "5_oros.png"},
    {"id": 6, "name": "6 de Oros", "suit": "Oros", "value": 6, "points": 6, "image": "6_oros.png"},
    {"id": 7, "name": "7 de Oros", "suit": "Oros", "value": 7, "points": 7, "image": "7_oros.png"},
    {"id": 8, "name": "Sota de Oros", "suit": "Oros", "value": 10, "points": 8, "image": "sota_oros.png"},
    {"id": 9, "name": "Caballo de Oros", "suit": "Oros", "value": 11, "points": 9, "image": "caballo_oros.png"},
    {"id": 10, "name": "Rey de Oros", "suit": "Oros", "value": 12, "points": 10, "image": "rey_oros.png"},
    # Copas (Cups) - IDs 11-20
    {"id": 11, "name": "1 de Copas", "suit": "Copas", "value": 1, "points": 1, "image": "1_copas.png"},
    {"id": 12, "name": "2 de Copas", "suit": "Copas", "value": 2, "points": 2, "image": "2_copas.png"},
    {"id": 13, "name": "3 de Copas", "suit": "Copas", "value": 3, "points": 3, "image": "3_copas.png"},
    {"id": 14, "name": "4 de Copas", "suit": "Copas", "value": 4, "points": 4, "image": "4_copas.png"},
    {"id": 15, "name": "5 de Copas", "suit": "Copas", "value": 5, "points": 5, "image": "5_copas.png"},
    {"id": 16, "name": "6 de Copas", "suit": "Copas", "value": 6, "points": 6, "image": "6_copas.png"},
    {"id": 17, "name": "7 de Copas", "suit": "Copas", "value": 7, "points": 7, "image": "7_copas.png"},
    {"id": 18, "name": "Sota de Copas", "suit": "Copas", "value": 10, "points": 8, "image": "sota_copas.png"},
    {"id": 19, "name": "Caballo de Copas", "suit": "Copas", "value": 11, "points": 9, "image": "caballo_copas.png"},
    {"id": 20, "name": "Rey de Copas", "suit": "Copas", "value": 12, "points": 10, "image": "rey_copas.png"},
    # Espadas (Swords) - IDs 21-30
    {"id": 21, "name": "1 de Espadas", "suit": "Espadas", "value": 1, "points": 1, "image": "1_espadas.png"},
    {"id": 22, "name": "2 de Espadas", "suit": "Espadas", "value": 2, "points": 2, "image": "2_espadas.png"},
    {"id": 23, "name": "3 de Espadas", "suit": "Espadas", "value": 3, "points": 3, "image": "3_espadas.png"},
    {"id": 24, "name": "4 de Espadas", "suit": "Espadas", "value": 4, "points": 4, "image": "4_espadas.png"},
    {"id": 25, "name": "5 de Espadas", "suit": "Espadas", "value": 5, "points": 5, "image": "5_espadas.png"},
    {"id": 26, "name": "6 de Espadas", "suit": "Espadas", "value": 6, "points": 6, "image": "6_espadas.png"},
    {"id": 27, "name": "7 de Espadas", "suit": "Espadas", "value": 7, "points": 7, "image": "7_espadas.png"},
    {"id": 28, "name": "Sota de Espadas", "suit": "Espadas", "value": 10, "points": 8, "image": "sota_espadas.png"},
    {"id": 29, "name": "Caballo de Espadas", "suit": "Espadas", "value": 11, "points": 9, "image": "caballo_espadas.png"},
    {"id": 30, "name": "Rey de Espadas", "suit": "Espadas", "value": 12, "points": 10, "image": "rey_espadas.png"},
    # Bastos (Clubs) - IDs 31-40
    {"id": 31, "name": "1 de Bastos", "suit": "Bastos", "value": 1, "points": 1, "image": "1_bastos.png"},
    {"id": 32, "name": "2 de Bastos", "suit": "Bastos", "value": 2, "points": 2, "image": "2_bastos.png"},
    {"id": 33, "name": "3 de Bastos", "suit": "Bastos", "value": 3, "points": 3, "image": "3_bastos.png"},
    {"id": 34, "name": "4 de Bastos", "suit": "Bastos", "value": 4, "points": 4, "image": "4_bastos.png"},
    {"id": 35, "name": "5 de Bastos", "suit": "Bastos", "value": 5, "points": 5, "image": "5_bastos.png"},
    {"id": 36, "name": "6 de Bastos", "suit": "Bastos", "value": 6, "points": 6, "image": "6_bastos.png"},
    {"id": 37, "name": "7 de Bastos", "suit": "Bastos", "value": 7, "points": 7, "image": "7_bastos.png"},
    {"id": 38, "name": "Sota de Bastos", "suit": "Bastos", "value": 10, "points": 8, "image": "sota_bastos.png"},
    {"id": 39, "name": "Caballo de Bastos", "suit": "Bastos", "value": 11, "points": 9, "image": "caballo_bastos.png"},
    {"id": 40, "name": "Rey de Bastos", "suit": "Bastos", "value": 12, "points": 10, "image": "rey_bastos.png"}
]

@app.route('/cards', methods=['GET'])
def get_all_cards():
    """Get all Spanish deck cards"""
    return jsonify({
        "count": len(SPANISH_DECK),
        "cards": SPANISH_DECK
    })

@app.route('/cards/<int:card_id>', methods=['GET'])
def get_card(card_id):
    """Get specific card by ID"""
    card = next((c for c in SPANISH_DECK if c['id'] == card_id), None)

    if card:
        return jsonify(card)
    else:
        return jsonify({"error": "Card not found"}), 404

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "Cards service is running"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
