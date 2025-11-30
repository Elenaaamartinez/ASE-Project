const API_BASE = "http://localhost:5000"

class EscobaAPI {
  static async healthCheck() {
    try {
      const response = await fetch(`${API_BASE}/health`)
      return await response.json()
    } catch (error) {
      console.error("Health check failed:", error)
      return null
    }
  }

  // Auth endpoints
  static async register(username, password, email = null) {
    const payload = { username, password }
    if (email) payload.email = email

    const response = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    return await response.json()
  }

  static async login(username, password) {
    const response = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    })
    return await response.json()
  }

  // Game endpoints
  static async createMatch(player1, player2) {
    const response = await fetch(`${API_BASE}/match/match`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ player1, player2 }),
    })
    return await response.json()
  }

  static async getMatchState(matchId, player) {
    const response = await fetch(`${API_BASE}/match/match/${matchId}?player=${player}`)
    return await response.json()
  }

  static async playCard(matchId, player, cardId) {
    const response = await fetch(`${API_BASE}/match/match/${matchId}/play`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ player, card_id: cardId }),
    })
    return await response.json()
  }

  // Player endpoints
  static async getPlayerProfile(username) {
    const response = await fetch(`${API_BASE}/players/${username}`)
    return await response.json()
  }

  // History endpoints
  static async getPlayerHistory(username) {
    const response = await fetch(`${API_BASE}/history/${username}`)
    return await response.json()
  }

  // Cards endpoints
  static async getAllCards() {
    const response = await fetch(`${API_BASE}/cards/cards`)
    return await response.json()
  }
}