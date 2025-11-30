from flask import Flask, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Spanish deck data (40 cards) with complete information
SPANISH_DECK = [
    # Oros (Coins) - IDs 1-10
    {"id": 1, "name": "1 de Oros", "suit": "Oros", "value": 1, "points": 1, "image": "1_oros.png", "suit_order": 4},
    {"id": 2, "name": "2 de Oros", "suit": "Oros", "value": 2, "points": 2, "image": "2_oros.png", "suit_order": 4},
    {"id": 3, "name": "3 de Oros", "suit": "Oros", "value": 3, "points": 3, "image": "3_oros.png", "suit_order": 4},
    {"id": 4, "name": "4 de Oros", "suit": "Oros", "value": 4, "points": 4, "image": "4_oros.png", "suit_order": 4},
    {"id": 5, "name": "5 de Oros", "suit": "Oros", "value": 5, "points": 5, "image": "5_oros.png", "suit_order": 4},
    {"id": 6, "name": "6 de Oros", "suit": "Oros", "value": 6, "points": 6, "image": "6_oros.png", "suit_order": 4},
    {"id": 7, "name": "7 de Oros", "suit": "Oros", "value": 7, "points": 7, "image": "7_oros.png", "suit_order": 4},
    {"id": 8, "name": "Sota de Oros", "suit": "Oros", "value": 10, "points": 8, "image": "sota_oros.png", "suit_order": 4},
    {"id": 9, "name": "Caballo de Oros", "suit": "Oros", "value": 11, "points": 9, "image": "caballo_oros.png", "suit_order": 4},
    {"id": 10, "name": "Rey de Oros", "suit": "Oros", "value": 12, "points": 10, "image": "rey_oros.png", "suit_order": 4},
    
    # Copas (Cups) - IDs 11-20
    {"id": 11, "name": "1 de Copas", "suit": "Copas", "value": 1, "points": 1, "image": "1_copas.png", "suit_order": 3},
    {"id": 12, "name": "2 de Copas", "suit": "Copas", "value": 2, "points": 2, "image": "2_copas.png", "suit_order": 3},
    {"id": 13, "name": "3 de Copas", "suit": "Copas", "value": 3, "points": 3, "image": "3_copas.png", "suit_order": 3},
    {"id": 14, "name": "4 de Copas", "suit": "Copas", "value": 4, "points": 4, "image": "4_copas.png", "suit_order": 3},
    {"id": 15, "name": "5 de Copas", "suit": "Copas", "value": 5, "points": 5, "image": "5_copas.png", "suit_order": 3},
    {"id": 16, "name": "6 de Copas", "suit": "Copas", "value": 6, "points": 6, "image": "6_copas.png", "suit_order": 3},
    {"id": 17, "name": "7 de Copas", "suit": "Copas", "value": 7, "points": 7, "image": "7_copas.png", "suit_order": 3},
    {"id": 18, "name": "Sota de Copas", "suit": "Copas", "value": 10, "points": 8, "image": "sota_copas.png", "suit_order": 3},
    {"id": 19, "name": "Caballo de Copas", "suit": "Copas", "value": 11, "points": 9, "image": "caballo_copas.png", "suit_order": 3},
    {"id": 20, "name": "Rey de Copas", "suit": "Copas", "value": 12, "points": 10, "image": "rey_copas.png", "suit_order": 3},
    
    # Espadas (Swords) - IDs 21-30
    {"id": 21, "name": "1 de Espadas", "suit": "Espadas", "value": 1, "points": 1, "image": "1_espadas.png", "suit_order": 2},
    {"id": 22, "name": "2 de Espadas", "suit": "Espadas", "value": 2, "points": 2, "image": "2_espadas.png", "suit_order": 2},
    {"id": 23, "name": "3 de Espadas", "suit": "Espadas", "value": 3, "points": 3, "image": "3_espadas.png", "suit_order": 2},
    {"id": 24, "name": "4 de Espadas", "suit": "Espadas", "value": 4, "points": 4, "image": "4_espadas.png", "suit_order": 2},
    {"id": 25, "name": "5 de Espadas", "suit": "Espadas", "value": 5, "points": 5, "image": "5_espadas.png", "suit_order": 2},
    {"id": 26, "name": "6 de Espadas", "suit": "Espadas", "value": 6, "points": 6, "image": "6_espadas.png", "suit_order": 2},
    {"id": 27, "name": "7 de Espadas", "suit": "Espadas", "value": 7, "points": 7, "image": "7_espadas.png", "suit_order": 2},
    {"id": 28, "name": "Sota de Espadas", "suit": "Espadas", "value": 10, "points": 8, "image": "sota_espadas.png", "suit_order": 2},
    {"id": 29, "name": "Caballo de Espadas", "suit": "Espadas", "value": 11, "points": 9, "image": "caballo_espadas.png", "suit_order": 2},
    {"id": 30, "name": "Rey de Espadas", "suit": "Espadas", "value": 12, "points": 10, "image": "rey_espadas.png", "suit_order": 2},
    
    # Bastos (Clubs) - IDs 31-40
    {"id": 31, "name": "1 de Bastos", "suit": "Bastos", "value": 1, "points": 1, "image": "1_bastos.png", "suit_order": 1},
    {"id": 32, "name": "2 de Bastos", "suit": "Bastos", "value": 2, "points": 2, "image": "2_bastos.png", "suit_order": 1},
    {"id": 33, "name": "3 de Bastos", "suit": "Bastos", "value": 3, "points": 3, "image": "3_bastos.png", "suit_order": 1},
    {"id": 34, "name": "4 de Bastos", "suit": "Bastos", "value": 4, "points": 4, "image": "4_bastos.png", "suit_order": 1},
    {"id": 35, "name": "5 de Bastos", "suit": "Bastos", "value": 5, "points": 5, "image": "5_bastos.png", "suit_order": 1},
    {"id": 36, "name": "6 de Bastos", "suit": "Bastos", "value": 6, "points": 6, "image": "6_bastos.png", "suit_order": 1},
    {"id": 37, "name": "7 de Bastos", "suit": "Bastos", "value": 7, "points": 7, "image": "7_bastos.png", "suit_order": 1},
    {"id": 38, "name": "Sota de Bastos", "suit": "Bastos", "value": 10, "points": 8, "image": "sota_bastos.png", "suit_order": 1},
    {"id": 39, "name": "Caballo de Bastos", "suit": "Bastos", "value": 11, "points": 9, "image": "caballo_bastos.png", "suit_order": 1},
    {"id": 40, "name": "Rey de Bastos", "suit": "Bastos", "value": 12, "points": 10, "image": "rey_bastos.png", "suit_order": 1}
]

def get_card_by_id(card_id):
    """Get card by ID with validation"""
    try:
        card_id = int(card_id)
        if 1 <= card_id <= 40:
            return next((card for card in SPANISH_DECK if card['id'] == card_id), None)
        return None
    except (ValueError, TypeError):
        return None

@app.route('/cards', methods=['GET'])
def get_all_cards():
    """Get all Spanish deck cards with filtering options"""
    try:
        # Get query parameters for filtering
        suit = request.args.get('suit')
        min_value = request.args.get('min_value')
        max_value = request.args.get('max_value')
        
        filtered_cards = SPANISH_DECK.copy()
        
        # Filter by suit if provided
        if suit and suit in ['Oros', 'Copas', 'Espadas', 'Bastos']:
            filtered_cards = [card for card in filtered_cards if card['suit'] == suit]
        
        # Filter by value range if provided
        if min_value:
            try:
                min_val = int(min_value)
                filtered_cards = [card for card in filtered_cards if card['value'] >= min_val]
            except ValueError:
                pass
        
        if max_value:
            try:
                max_val = int(max_value)
                filtered_cards = [card for card in filtered_cards if card['value'] <= max_val]
            except ValueError:
                pass
        
        # Sort by suit order and value
        filtered_cards.sort(key=lambda x: (x['suit_order'], x['value']))
        
        # Calculate statistics
        suits_count = {}
        for card in filtered_cards:
            suit_name = card['suit']
            suits_count[suit_name] = suits_count.get(suit_name, 0) + 1
        
        return jsonify({
            "count": len(filtered_cards),
            "total_cards": 40,
            "suits_distribution": suits_count,
            "cards": filtered_cards
        })
    except Exception as e:
        return jsonify({"error": f"Failed to get cards: {str(e)}"}), 500

@app.route('/cards/<card_id>', methods=['GET'])
def get_card(card_id):
    """Get specific card by ID"""
    card = get_card_by_id(card_id)

    if card:
        return jsonify(card)
    else:
        return jsonify({"error": "Card not found"}), 404

@app.route('/cards/suits', methods=['GET'])
def get_suits():
    """Get information about all suits"""
    suits_info = {
        "Oros": {
            "name": "Oros",
            "translation": "Coins",
            "suit_order": 4,
            "card_count": 10,
            "description": "Gold coins, highest ranking suit"
        },
        "Copas": {
            "name": "Copas", 
            "translation": "Cups",
            "suit_order": 3,
            "card_count": 10,
            "description": "Chalices or cups"
        },
        "Espadas": {
            "name": "Espadas",
            "translation": "Swords", 
            "suit_order": 2,
            "card_count": 10,
            "description": "Swords"
        },
        "Bastos": {
            "name": "Bastos",
            "translation": "Clubs",
            "suit_order": 1, 
            "card_count": 10,
            "description": "Clubs or cudgels, lowest ranking suit"
        }
    }
    
    return jsonify({
        "suits": suits_info,
        "total_suits": 4
    })

@app.route('/cards/suits/<suit_name>', methods=['GET'])
def get_suit_cards(suit_name):
    """Get all cards of a specific suit"""
    valid_suits = ['Oros', 'Copas', 'Espadas', 'Bastos']
    
    if suit_name not in valid_suits:
        return jsonify({"error": "Invalid suit name"}), 400
    
    suit_cards = [card for card in SPANISH_DECK if card['suit'] == suit_name]
    suit_cards.sort(key=lambda x: x['value'])
    
    return jsonify({
        "suit": suit_name,
        "card_count": len(suit_cards),
        "cards": suit_cards
    })

@app.route('/cards/special', methods=['GET'])
def get_special_cards():
    """Get special cards that give extra points in La Escoba"""
    special_cards = {
        "seven_of_oros": next(card for card in SPANISH_DECK if card['id'] == 7),
        "seven_of_copas": next(card for card in SPANISH_DECK if card['id'] == 17)
    }
    
    # Get all cards worth 10 points (Reyes)
    reyes_cards = [card for card in SPANISH_DECK if card['points'] == 10]
    
    return jsonify({
        "special_cards": {
            "seven_of_oros": {
                "card": special_cards["seven_of_oros"],
                "bonus": "1 extra point in scoring",
                "description": "The most valuable card in the game"
            },
            "seven_of_copas": {
                "card": special_cards["seven_of_copas"], 
                "bonus": "1 extra point in scoring",
                "description": "Second most valuable card"
            }
        },
        "reyes_cards": {
            "count": len(reyes_cards),
            "cards": reyes_cards,
            "description": "Kings (Reyes) worth 10 points each"
        }
    })

@app.route('/cards/deck', methods=['POST'])
def create_shuffled_deck():
    """Create a new shuffled deck (for game initialization)"""
    try:
        deck = list(range(1, 41))  # Card IDs from 1 to 40
        
        # Optional: specify seed for reproducible shuffling
        seed = request.json.get('seed') if request.json else None
        if seed:
            import random
            random.seed(seed)
        
        import random
        random.shuffle(deck)
        
        return jsonify({
            "deck": deck,
            "count": len(deck),
            "seed_used": seed
        })
    except Exception as e:
        return jsonify({"error": f"Failed to create deck: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "Cards service is running",
        "total_cards": len(SPANISH_DECK),
        "suits_available": 4,
        "timestamp": __import__('datetime').datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🃏 Cards Service starting on port 5002...")
    print("📊 40 Spanish cards loaded")
    print("🎴 Suits: Oros, Copas, Espadas, Bastos")
    app.run(host='0.0.0.0', port=5002, debug=False)
