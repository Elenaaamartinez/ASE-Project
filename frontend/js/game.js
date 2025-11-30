// Import necessary modules or declare variables before using them
const authManager = require("./auth.js")
const Utils = require("./utils.js")
const EscobaAPI = require("./api.js")

class GameManager {
  constructor() {
    this.currentMatch = null
    this.playerName = null
    this.opponentName = null
    this.gameInterval = null
  }

  showCreateGame() {
    document.querySelector(".game-options").style.display = "none"
    document.getElementById("gameInterface").style.display = "block"

    document.getElementById("gameInterface").innerHTML = `
            <div class="board-section">
                <h4>Create New Match</h4>
                <form id="createGameForm">
                    <input type="text" id="opponentUsername" placeholder="Opponent's username" required style="width: 100%; padding: 0.75rem; margin-bottom: 1rem; border: 2px solid var(--color-border); border-radius: 0.5rem; background: var(--color-surface-light); color: var(--color-text);">
                    <div style="display: flex; gap: 1rem;">
                        <button type="submit" class="btn btn-play">Create Match</button>
                        <button type="button" class="btn" onclick="gameManager.hideGameInterface()">Cancel</button>
                    </div>
                </form>
            </div>
        `

    document.getElementById("createGameForm").addEventListener("submit", async (e) => {
      e.preventDefault()
      const opponent = document.getElementById("opponentUsername").value
      await this.createGame(authManager.currentUser, opponent)
    })
  }

  showJoinGame() {
    document.querySelector(".game-options").style.display = "none"
    document.getElementById("gameInterface").style.display = "block"

    document.getElementById("gameInterface").innerHTML = `
            <div class="board-section">
                <h4>Join Match</h4>
                <form id="joinGameForm">
                    <input type="text" id="matchId" placeholder="Match ID" required style="width: 100%; padding: 0.75rem; margin-bottom: 1rem; border: 2px solid var(--color-border); border-radius: 0.5rem; background: var(--color-surface-light); color: var(--color-text);">
                    <div style="display: flex; gap: 1rem;">
                        <button type="submit" class="btn btn-play">Join</button>
                        <button type="button" class="btn" onclick="gameManager.hideGameInterface()">Cancel</button>
                    </div>
                </form>
            </div>
        `

    document.getElementById("joinGameForm").addEventListener("submit", async (e) => {
      e.preventDefault()
      const matchId = document.getElementById("matchId").value
      await this.joinGame(matchId, authManager.currentUser)
    })
  }

  showRandomMatch() {
    this.createGame(authManager.currentUser, "bot_player")
  }

  hideGameInterface() {
    document.getElementById("gameInterface").style.display = "none"
    document.querySelector(".game-options").style.display = "flex"
  }

  async createGame(player1, player2) {
    try {
      Utils.showNotification("Creating match...", "info")

      const result = await EscobaAPI.createMatch(player1, player2)

      if (result.error) {
        throw new Error(result.error)
      }

      if (!result.match_id) {
        throw new Error("No match ID received from the server")
      }

      this.currentMatch = result.match_id
      this.playerName = player1
      this.opponentName = player2

      Utils.showNotification("Match created successfully!", "success")
      this.showGameInterface()
      return result
    } catch (error) {
      console.error("Error creating game:", error)
      let errorMessage = "Error creating match: "

      if (error.message.includes("Failed to fetch")) {
        errorMessage += "Server connection error"
      } else if (error.message.includes("player2")) {
        errorMessage += "Player 2 not found. Make sure they exist."
      } else {
        errorMessage += error.message
      }

      Utils.showNotification(errorMessage, "error")
      return null
    }
  }

  async joinGame(matchId, player) {
    try {
      Utils.showNotification("Joining match...", "info")
      const state = await EscobaAPI.getMatchState(matchId, player)
      this.currentMatch = matchId
      this.playerName = player
      this.opponentName = state.players.find((p) => p !== player)

      Utils.showNotification("Successfully joined the match!", "success")
      this.showGameInterface()
    } catch (error) {
      console.error("Error joining game:", error)
      Utils.showNotification("Error joining match: " + error.message, "error")
    }
  }

  showGameInterface() {
    document.getElementById("gameSection").innerHTML = `
            <div class="game-header">
                <h3>🎮 Match in Progress</h3>
                <button class="btn btn-danger" onclick="gameManager.leaveGame()">Leave Match</button>
            </div>
            <div id="gameState">
                <p>Loading match...</p>
            </div>
        `

    this.startGameLoop()
  }

  async startGameLoop() {
    if (this.gameInterval) {
      clearInterval(this.gameInterval)
    }

    this.gameInterval = setInterval(() => {
      this.updateGameState()
    }, 3000)

    await this.updateGameState()
  }

  async updateGameState() {
    if (!this.currentMatch || !this.playerName) return

    try {
      const state = await EscobaAPI.getMatchState(this.currentMatch, this.playerName)
      this.renderGameState(state)

      if (state.status === "finished") {
        clearInterval(this.gameInterval)
        this.showGameResult(state)
      }
    } catch (error) {
      console.error("Error updating game state:", error)
    }
  }

  renderGameState(state) {
    const gameState = document.getElementById("gameState")

    if (!state || state.error) {
      gameState.innerHTML = "<p>Error loading match state.</p>"
      return
    }

    const isMyTurn = state.current_player === this.playerName

    gameState.innerHTML = `
            <div class="game-info">
                <p><strong>Match:</strong> ${state.match_id}</p>
                <p><strong>Players:</strong> ${state.players.join(" vs ")}</p>
                <p><strong>Current Turn:</strong> ${state.current_player}</p>
                <p><strong>Score:</strong> ${Utils.formatScore(state.scores)}</p>
                <p><strong>Status:</strong> ${state.status === "active" ? "🟢 In Progress" : "🔴 Finished"}</p>
                <p><strong>Cards left in deck:</strong> ${state.remaining_deck || "N/A"}</p>
            </div>
            
            <div class="board-section">
                <h4>🃏 Cards on Table (${state.table_cards.length})</h4>
                <div class="card-area">
                    ${state.table_cards
                      .map((cardId) => {
                        const card = Utils.formatCard(cardId)
                        return `
                            <div class="card-spanish table-card" data-card-id="${cardId}" title="${card.fullName}">
                                <img src="${card.imagePath}" alt="${card.fullName}" />
                            </div>
                        `
                      })
                      .join("")}
                </div>
            </div>

            <div class="board-section">
                <h4>🎴 Your Hand (${state.your_hand.length} cards)</h4>
                <div class="card-area">
                    ${state.your_hand
                      .map((cardId) => {
                        const card = Utils.formatCard(cardId)
                        return `
                            <div class="card-spanish playable ${isMyTurn ? "your-turn" : "not-your-turn"}" 
                                 data-card-id="${cardId}" 
                                 onclick="${isMyTurn ? `gameManager.playCard(${cardId})` : ""}"
                                 title="${card.fullName}">
                                <img src="${card.imagePath}" alt="${card.fullName}" />
                            </div>
                        `
                      })
                      .join("")}
                </div>
                <div class="turn-info">
                    ${
                      isMyTurn
                        ? "✅ It's your turn! Choose a card"
                        : `⏳ Waiting for ${state.current_player}'s turn`
                    }
                </div>
            </div>

            <div class="board-section">
                <h4>🏆 Captured Cards (${state.captured_cards ? state.captured_cards.length : 0})</h4>
                <div class="card-area">
                    ${
                      state.captured_cards && state.captured_cards.length > 0
                        ? state.captured_cards
                            .map((cardId) => {
                              const card = Utils.formatCard(cardId)
                              return `
                            <div class="card-spanish captured" data-card-id="${cardId}" title="${card.fullName}">
                                <img src="${card.imagePath}" alt="${card.fullName}" />
                            </div>
                        `
                            })
                            .join("")
                        : '<p style="color: var(--color-text-muted);">No captured cards yet</p>'
                    }
                </div>
            </div>
        `
  }

  async playCard(cardId) {
    if (!this.currentMatch || !this.playerName) return

    const currentState = await EscobaAPI.getMatchState(this.currentMatch, this.playerName)
    if (currentState.current_player !== this.playerName) {
      Utils.showNotification("It's not your turn!", "error")
      return
    }

    try {
      Utils.showNotification("Playing card...", "info")
      const result = await EscobaAPI.playCard(this.currentMatch, this.playerName, cardId)

      await this.updateGameState()

      if (result.message) {
        Utils.showNotification(result.message, "success")
      }
    } catch (error) {
      console.error("Error playing card:", error)
      Utils.showNotification("Error playing card: " + (error.message || "Invalid move"), "error")
    }
  }

  leaveGame() {
    if (this.gameInterval) {
      clearInterval(this.gameInterval)
      this.gameInterval = null
    }
    this.currentMatch = null
    this.playerName = null
    this.opponentName = null

    Utils.showNotification("Match left", "info")
    authManager.showGame()
  }

  showGameResult(state) {
    const winner = state.scores[state.players[0]] > state.scores[state.players[1]] ? state.players[0] : state.players[1]

    const isWinner = winner === this.playerName

    document.getElementById("gameState").innerHTML += `
            <div class="game-result ${isWinner ? "victory" : "defeat"}">
                <h3>${isWinner ? "🎉 VICTORY!" : "😔 DEFEAT"}</h3>
                <p>Winner: <strong>${winner}</strong></p>
                <p>Final Score: ${Utils.formatScore(state.scores)}</p>
                <div style="display: flex; gap: 1rem; justify-content: center; margin-top: 1.5rem;">
                    <button class="btn" onclick="gameManager.leaveGame()">Return to Menu</button>
                    ${
                      this.opponentName !== "bot_player"
                        ? `<button class="btn btn-play" onclick="gameManager.createGame('${this.playerName}', '${this.opponentName}')">Rematch</button>`
                        : ""
                    }
                </div>
            </div>
        `

    Utils.showNotification(`Match ended! Winner: ${winner}`, isWinner ? "success" : "info")
  }
}

const gameManager = new GameManager()