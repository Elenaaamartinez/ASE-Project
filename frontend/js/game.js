class GameManager {
    constructor() {
        this.currentMatch = null;
        this.playerName = null;
        this.opponentName = null;
        this.gameInterval = null;
    }

    showCreateGame() {
        document.querySelector('.game-options').style.display = 'none';
        document.getElementById('gameInterface').style.display = 'block';
        
        document.getElementById('gameInterface').innerHTML = `
            <h4>Crea Nuova Partita</h4>
            <form id="createGameForm">
                <input type="text" id="opponentUsername" placeholder="Username avversario" required>
                <button type="submit">Crea Partita</button>
                <button type="button" onclick="gameManager.hideGameInterface()">Annulla</button>
            </form>
        `;
        
        document.getElementById('createGameForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const opponent = document.getElementById('opponentUsername').value;
            await this.createGame(authManager.currentUser, opponent);
        });
    }

    showJoinGame() {
        document.querySelector('.game-options').style.display = 'none';
        document.getElementById('gameInterface').style.display = 'block';
        
        document.getElementById('gameInterface').innerHTML = `
            <h4>Unisciti a Partita</h4>
            <form id="joinGameForm">
                <input type="text" id="matchId" placeholder="ID Partita" required>
                <button type="submit">Unisciti</button>
                <button type="button" onclick="gameManager.hideGameInterface()">Annulla</button>
            </form>
        `;
        
        document.getElementById('joinGameForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const matchId = document.getElementById('matchId').value;
            await this.joinGame(matchId, authManager.currentUser);
        });
    }

    showRandomMatch() {
        // Per semplicità, crea una partita con un bot
        this.createGame(authManager.currentUser, 'bot_player');
    }

    hideGameInterface() {
        document.getElementById('gameInterface').style.display = 'none';
        document.querySelector('.game-options').style.display = 'flex';
    }

    async createGame(player1, player2) {
    try {
        Utils.showNotification('Creazione partita in corso...', 'info');
        console.log(`Creating game: ${player1} vs ${player2}`);
        
        const result = await EscobaAPI.createMatch(player1, player2);
        console.log('Create game response:', result);
        
        if (result.error) {
            throw new Error(result.error);
        }
        
        if (!result.match_id) {
            throw new Error('Nessun ID partita ricevuto dal server');
        }
        
        this.currentMatch = result.match_id;
        this.playerName = player1;
        this.opponentName = player2;
        
        Utils.showNotification('Partita creata con successo!', 'success');
        this.showGameInterface();
        return result;
        
    } catch (error) {
        console.error('Error creating game:', error);
        let errorMessage = 'Errore nella creazione della partita: ';
        
        if (error.message.includes('Failed to fetch')) {
            errorMessage += 'Errore di connessione al server';
        } else if (error.message.includes('player2')) {
            errorMessage += 'Giocatore 2 non trovato. Assicurati che esista.';
        } else {
            errorMessage += error.message;
        }
        
        Utils.showNotification(errorMessage, 'error');
        return null;
    }
}

    async joinGame(matchId, player) {
        try {
            Utils.showNotification('Unione alla partita in corso...', 'info');
            const state = await EscobaAPI.getMatchState(matchId, player);
            this.currentMatch = matchId;
            this.playerName = player;
            this.opponentName = state.players.find(p => p !== player);
            
            Utils.showNotification('Unito alla partita con successo!', 'success');
            this.showGameInterface();
        } catch (error) {
            console.error('Error joining game:', error);
            Utils.showNotification('Errore nell\'unione alla partita: ' + error.message, 'error');
        }
    }

    showGameInterface() {
        document.getElementById('gameSection').innerHTML = `
            <div class="game-header">
                <h3>🎮 Partita in Corso</h3>
                <button onclick="gameManager.leaveGame()">Abbandona Partita</button>
            </div>
            <div id="gameState">
                <p>Caricamento partita...</p>
            </div>
        `;
        
        this.startGameLoop();
    }

    async startGameLoop() {
        // Ferma eventuali intervalli precedenti
        if (this.gameInterval) {
            clearInterval(this.gameInterval);
        }

        // Aggiorna lo stato della partita ogni 3 secondi
        this.gameInterval = setInterval(() => {
            this.updateGameState();
        }, 3000);
        
        await this.updateGameState();
    }

    async updateGameState() {
        if (!this.currentMatch || !this.playerName) return;

        try {
            const state = await EscobaAPI.getMatchState(this.currentMatch, this.playerName);
            this.renderGameState(state);
            
            // Se la partita è finita, ferma il loop
            if (state.status === 'finished') {
                clearInterval(this.gameInterval);
                this.showGameResult(state);
            }
        } catch (error) {
            console.error('Error updating game state:', error);
        }
    }

    renderGameState(state) {
        const gameState = document.getElementById('gameState');
        
        if (!state || state.error) {
            gameState.innerHTML = '<p>Errore nel caricamento dello stato della partita.</p>';
            return;
        }

        const cardInfo = state.your_hand.map(cardId => Utils.formatCard(cardId));
        const isMyTurn = state.current_player === this.playerName;

        gameState.innerHTML = `
            <div class="game-info">
                <p><strong>Partita:</strong> ${state.match_id}</p>
                <p><strong>Giocatori:</strong> ${state.players.join(' vs ')}</p>
                <p><strong>Turno di:</strong> ${state.current_player}</p>
                <p><strong>Punteggio:</strong> ${Utils.formatScore(state.scores)}</p>
                <p><strong>Stato:</strong> ${state.status === 'active' ? '🟢 In Corso' : '🔴 Terminata'}</p>
                <p><strong>Carte rimanenti nel mazzo:</strong> ${state.remaining_deck || 'N/A'}</p>
            </div>
            
            <div class="table-cards">
                <h4>🃏 Carte sul Tavolo (${state.table_cards.length})</h4>
                <div class="card-area">
                    ${state.table_cards.map(cardId => {
                        const card = Utils.formatCard(cardId);
                        return `
                            <div class="card table-card" data-card-id="${cardId}">
                                <div class="card-value">${card.value}</div>
                                <div class="suit ${card.isRed ? 'red' : 'black'}">${card.suit}</div>
                                <div class="card-name">${card.suitName}</div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>

            <div class="player-hand">
                <h4>🎴 La Tua Mano (${state.your_hand.length} carte)</h4>
                <div class="card-area">
                    ${state.your_hand.map(cardId => {
                        const card = Utils.formatCard(cardId);
                        return `
                            <div class="card playable ${isMyTurn ? 'your-turn' : 'not-your-turn'}" 
                                 data-card-id="${cardId}" 
                                 onclick="gameManager.playCard(${cardId})"
                                 title="${card.fullName}">
                                <div class="card-value">${card.value}</div>
                                <div class="suit ${card.isRed ? 'red' : 'black'}">${card.suit}</div>
                                <div class="card-name">${card.suitName}</div>
                            </div>
                        `;
                    }).join('')}
                </div>
                <div class="turn-info">
                    ${isMyTurn ? 
                      '✅ È il tuo turno! Scegli una carta dalla tua mano' : 
                      `⏳ Aspettando il turno di ${state.current_player}`
                    }
                </div>
            </div>

            <div class="captured-cards">
                <h4>🏆 Carte Catturate (${state.captured_cards ? state.captured_cards.length : 0})</h4>
                <div class="card-area">
                    ${state.captured_cards ? state.captured_cards.map(cardId => {
                        const card = Utils.formatCard(cardId);
                        return `
                            <div class="card captured" data-card-id="${cardId}">
                                <div class="card-value">${card.value}</div>
                                <div class="suit ${card.isRed ? 'red' : 'black'}">${card.suit}</div>
                                <div class="card-name">${card.suitName}</div>
                            </div>
                        `;
                    }).join('') : '<p>Nessuna carta catturata ancora</p>'}
                </div>
            </div>
        `;
    }

    async playCard(cardId) {
        if (!this.currentMatch || !this.playerName) return;

        const currentState = await EscobaAPI.getMatchState(this.currentMatch, this.playerName);
        if (currentState.current_player !== this.playerName) {
            Utils.showNotification('Non è il tuo turno!', 'error');
            return;
        }

        try {
            Utils.showNotification('Giocando carta...', 'info');
            const result = await EscobaAPI.playCard(this.currentMatch, this.playerName, cardId);
            
            // Aggiorna immediatamente lo stato
            await this.updateGameState();
            
            if (result.message) {
                Utils.showNotification(result.message, 'success');
            }
            
        } catch (error) {
            console.error('Error playing card:', error);
            Utils.showNotification('Errore durante la mossa: ' + (error.message || 'Mossa non valida'), 'error');
        }
    }

    leaveGame() {
        if (this.gameInterval) {
            clearInterval(this.gameInterval);
            this.gameInterval = null;
        }
        this.currentMatch = null;
        this.playerName = null;
        this.opponentName = null;
        
        Utils.showNotification('Partita abbandonata', 'info');
        authManager.showGame(); // Torna al menu principale
    }

    showGameResult(state) {
        const winner = state.scores[state.players[0]] > state.scores[state.players[1]] ? 
                      state.players[0] : state.players[1];
        
        const isWinner = winner === this.playerName;
        
        document.getElementById('gameState').innerHTML += `
            <div class="game-result ${isWinner ? 'victory' : 'defeat'}">
                <h3>${isWinner ? '🎉 VITTORIA!' : '😔 SCONFITTA'}</h3>
                <p>Vincitore: <strong>${winner}</strong></p>
                <p>Punteggio Finale: ${Utils.formatScore(state.scores)}</p>
                <button onclick="gameManager.leaveGame()">Torna al Menu</button>
                ${this.opponentName !== 'bot_player' ? 
                  `<button onclick="gameManager.createGame('${this.playerName}', '${this.opponentName}')">Rivincita</button>` : 
                  ''
                }
            </div>
        `;

        Utils.showNotification(`Partita terminata! Vincitore: ${winner}`, isWinner ? 'success' : 'info');
    }
}

const gameManager = new GameManager();
