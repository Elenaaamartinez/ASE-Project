class AuthManager {
    constructor() {
        this.currentUser = null;
        this.setupEventListeners();
    }

    setupEventListeners() {
        document.getElementById('loginBtn').addEventListener('click', () => this.showLogin());
        document.getElementById('registerBtn').addEventListener('click', () => this.showRegister());
        document.getElementById('playBtn').addEventListener('click', () => this.showGame());
        document.getElementById('profileBtn').addEventListener('click', () => this.showProfile());
        document.getElementById('logoutBtn').addEventListener('click', () => this.logout());
    }

    showLogin() {
        this.showModal(`
            <h3>Accedi</h3>
            <form id="loginForm">
                <input type="text" id="loginUsername" placeholder="Username" required>
                <input type="password" id="loginPassword" placeholder="Password" required>
                <button type="submit">Accedi</button>
            </form>
            <p style="text-align: center; margin-top: 15px;">
                Non hai un account? <a href="#" onclick="authManager.showRegister()">Registrati</a>
            </p>
        `);
        
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('loginUsername').value;
            const password = document.getElementById('loginPassword').value;
            
            await this.login(username, password);
        });
    }

    showRegister() {
        this.showModal(`
            <h3>Registrati</h3>
            <form id="registerForm">
                <input type="text" id="regUsername" placeholder="Username" required>
                <input type="password" id="regPassword" placeholder="Password" required>
                <input type="email" id="regEmail" placeholder="Email (opzionale)">
                <button type="submit">Registrati</button>
            </form>
            <p style="text-align: center; margin-top: 15px;">
                Hai già un account? <a href="#" onclick="authManager.showLogin()">Accedi</a>
            </p>
        `);
        
        document.getElementById('registerForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('regUsername').value;
            const password = document.getElementById('regPassword').value;
            const email = document.getElementById('regEmail').value;
            
            await this.register(username, password, email);
        });
    }

    async login(username, password) {
        try {
            const result = await EscobaAPI.login(username, password);
            if (result.message === "Login successful" || result.token) {
                this.currentUser = username;
                this.updateUI();
                this.hideModal();
                Utils.showNotification(`Benvenuto ${username}!`, 'success');
            } else {
                Utils.showNotification('Login fallito: Credenziali errate', 'error');
            }
        } catch (error) {
            Utils.showNotification('Login fallito: ' + (error.message || 'Errore di connessione'), 'error');
        }
    }

    async register(username, password, email) {
        try {
            const result = await EscobaAPI.register(username, password, email);
            if (result.message && result.message.includes('successfully')) {
                Utils.showNotification('Registrazione completata! Ora puoi accedere.', 'success');
                this.showLogin();
            } else {
                Utils.showNotification('Registrazione fallita: ' + (result.error || 'Errore sconosciuto'), 'error');
            }
        } catch (error) {
            Utils.showNotification('Registrazione fallita: ' + (error.message || 'Errore di connessione'), 'error');
        }
    }

    logout() {
        this.currentUser = null;
        this.updateUI();
        Utils.showNotification('Arrivederci!', 'info');
    }

    updateUI() {
        const isLoggedIn = this.currentUser !== null;
        
        // Mostra/nascondi bottoni
        document.getElementById('loginBtn').style.display = isLoggedIn ? 'none' : 'block';
        document.getElementById('registerBtn').style.display = isLoggedIn ? 'none' : 'block';
        document.getElementById('playBtn').style.display = isLoggedIn ? 'block' : 'none';
        document.getElementById('profileBtn').style.display = isLoggedIn ? 'block' : 'none';
        document.getElementById('logoutBtn').style.display = isLoggedIn ? 'block' : 'none';

        // Aggiorna contenuto principale
        const welcomeSection = document.getElementById('welcome');
        const gameSection = document.getElementById('gameSection');
        
        if (isLoggedIn) {
            welcomeSection.innerHTML = `
                <h2>Benvenuto, ${this.currentUser}!</h2>
                <p>Clicca "Gioca" per iniziare una partita o "Profilo" per vedere le tue statistiche.</p>
            `;
            gameSection.style.display = 'none';
            welcomeSection.style.display = 'block';
        } else {
            welcomeSection.innerHTML = `
                <h2>Benvenuto a La Escoba!</h2>
                <p>Il classico gioco di carte spagnolo</p>
                <div class="card-preview">
                    <div class="card">
                        <div class="card-value">7</div>
                        <div class="suit red">♦</div>
                        <div class="card-name">Oros</div>
                    </div>
                    <div class="card">
                        <div class="card-value">10</div>
                        <div class="suit red">♥</div>
                        <div class="card-name">Copas</div>
                    </div>
                    <div class="card">
                        <div class="card-value">4</div>
                        <div class="suit black">♠</div>
                        <div class="card-name">Espadas</div>
                    </div>
                </div>
                <p style="text-align: center; margin-top: 20px;">
                    <strong>Accedi o registrati per iniziare a giocare!</strong>
                </p>
            `;
            gameSection.style.display = 'none';
            welcomeSection.style.display = 'block';
        }
    }

    showGame() {
        document.getElementById('welcome').style.display = 'none';
        document.getElementById('gameSection').style.display = 'block';
        
        // Mostra interfaccia per creare/joinare partita
        document.getElementById('gameSection').innerHTML = `
            <div class="game-header">
                <h3>🎮 Gioca</h3>
                <button onclick="authManager.showMainScreen()">← Torna Indietro</button>
            </div>
            <div class="game-options">
                <button onclick="gameManager.showCreateGame()">Crea Nuova Partita</button>
                <button onclick="gameManager.showJoinGame()">Unisciti a Partita</button>
                <button onclick="gameManager.showRandomMatch()">Partita Casuale</button>
            </div>
            <div id="gameInterface" style="display:none"></div>
        `;
    }

    showProfile() {
        document.getElementById('welcome').style.display = 'none';
        document.getElementById('gameSection').style.display = 'block';
        
        this.loadProfile();
    }

    async loadProfile() {
        if (!this.currentUser) return;
        
        try {
            const profile = await EscobaAPI.getPlayerProfile(this.currentUser);
            const history = await EscobaAPI.getPlayerHistory(this.currentUser);
            
            document.getElementById('gameSection').innerHTML = `
                <div class="game-header">
                    <h3>👤 Profilo di ${this.currentUser}</h3>
                    <button onclick="authManager.showMainScreen()">← Torna Indietro</button>
                </div>
                
                <div class="profile-info">
                    <h4>Statistiche</h4>
                    <p><strong>Punteggio Totale:</strong> ${profile.total_score}</p>
                    <p><strong>Livello:</strong> ${profile.level}</p>
                    <p><strong>Partite Giocate:</strong> ${profile.matches_played}</p>
                    <p><strong>Vittorie:</strong> ${profile.matches_won}</p>
                    <p><strong>Sconfitte:</strong> ${profile.matches_lost}</p>
                    <p><strong>Percentuale Vittorie:</strong> ${(profile.win_rate * 100).toFixed(1)}%</p>
                </div>
                
                <div class="match-history">
                    <h4>Storico Partite (${history.match_count})</h4>
                    ${history.matches.length > 0 ? 
                        history.matches.map(match => `
                            <div class="match-item">
                                <p><strong>VS ${match.player1 === this.currentUser ? match.player2 : match.player1}</strong></p>
                                <p>Risultato: <strong>${match.your_result === 'win' ? '✅ Vittoria' : match.your_result === 'loss' ? '❌ Sconfitta' : '⚪ Pareggio'}</strong></p>
                                <p>Punteggio: ${JSON.stringify(match.scores)}</p>
                                <p><small>${new Date(match.end_time).toLocaleString()}</small></p>
                            </div>
                        `).join('') :
                        '<p>Nessuna partita giocata ancora.</p>'
                    }
                </div>
            `;
        } catch (error) {
            console.error('Error loading profile:', error);
            document.getElementById('gameSection').innerHTML = `
                <div class="game-header">
                    <h3>👤 Profilo</h3>
                    <button onclick="authManager.showMainScreen()">← Torna Indietro</button>
                </div>
                <p>Errore nel caricamento del profilo.</p>
            `;
        }
    }

    showMainScreen() {
        document.getElementById('gameSection').style.display = 'none';
        document.getElementById('welcome').style.display = 'block';
        this.updateUI();
    }

    showModal(content) {
        // Rimuovi modali esistenti
        const existingModal = document.querySelector('.modal');
        if (existingModal) {
            existingModal.remove();
        }

        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <span class="close" onclick="authManager.hideModal()">&times;</span>
                ${content}
            </div>
        `;
        document.body.appendChild(modal);

        // Chiudi modal cliccando fuori
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.hideModal();
            }
        });
    }

    hideModal() {
        const modal = document.querySelector('.modal');
        if (modal) {
            modal.remove();
        }
    }
}

const authManager = new AuthManager();
