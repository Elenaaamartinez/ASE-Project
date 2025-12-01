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
            <h3>Login</h3>
            <form id="loginForm">
                <input type="text" id="loginUsername" placeholder="Username" required>
                <input type="password" id="loginPassword" placeholder="Password" required>
                <button type="submit">Login</button>
            </form>
            <p style="text-align: center; margin-top: 15px;">
                Don't have an account? <a href="#" onclick="authManager.showRegister()">Register</a>
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
            <h3>Register</h3>
            <form id="registerForm">
                <input type="text" id="regUsername" placeholder="Username" required>
                <input type="password" id="regPassword" placeholder="Password" required>
                <input type="email" id="regEmail" placeholder="Email (optional)">
                <button type="submit">Register</button>
            </form>
            <p style="text-align: center; margin-top: 15px;">
                Already have an account? <a href="#" onclick="authManager.showLogin()">Login</a>
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
                Utils.showNotification(`Welcome ${username}!`, 'success');
            } else {
                Utils.showNotification('Login failed: Incorrect credentials', 'error');
            }
        } catch (error) {
            Utils.showNotification('Login failed: ' + (error.message || 'Connection error'), 'error');
        }
    }

    async register(username, password, email) {
        try {
            const result = await EscobaAPI.register(username, password, email);
            if (result.message && result.message.includes('successfully')) {
                Utils.showNotification('Registration successful! Please login.', 'success');
                this.showLogin();
            } else {
                Utils.showNotification('Registration failed: ' + (result.error || 'Unknown error'), 'error');
            }
        } catch (error) {
            Utils.showNotification('Registration failed: ' + (error.message || 'Connection error'), 'error');
        }
    }

    logout() {
        this.currentUser = null;
        this.updateUI();
        Utils.showNotification('Goodbye!', 'info');
    }

    updateUI() {
        const isLoggedIn = this.currentUser !== null;
        
        // Show/hide buttons
        document.getElementById('loginBtn').style.display = isLoggedIn ? 'none' : 'block';
        document.getElementById('registerBtn').style.display = isLoggedIn ? 'none' : 'block';
        document.getElementById('playBtn').style.display = isLoggedIn ? 'block' : 'none';
        document.getElementById('profileBtn').style.display = isLoggedIn ? 'block' : 'none';
        document.getElementById('logoutBtn').style.display = isLoggedIn ? 'block' : 'none';

        // Update main content
        const welcomeSection = document.getElementById('welcome');
        const gameSection = document.getElementById('gameSection');
        
        if (isLoggedIn) {
            welcomeSection.innerHTML = `
                <h2>Welcome, ${this.currentUser}!</h2>
                <p>Click "Play" to start a match or "Profile" to view your stats.</p>
            `;
            gameSection.style.display = 'none';
            welcomeSection.style.display = 'block';
        } else {
            welcomeSection.innerHTML = `
                <h2>Welcome to La Escoba!</h2>
                <p>The classic Spanish card game</p>
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
                    <strong>Login or register to start playing!</strong>
                </p>
            `;
            gameSection.style.display = 'none';
            welcomeSection.style.display = 'block';
        }
    }

    showGame() {
        document.getElementById('welcome').style.display = 'none';
        document.getElementById('gameSection').style.display = 'block';
        
        // Show interface to create/join a match
        document.getElementById('gameSection').innerHTML = `
            <div class="game-header">
                <h3>🎮 Play</h3>
                <button onclick="authManager.showMainScreen()">← Go Back</button>
            </div>
            <div class="game-options">
                <button onclick="gameManager.showCreateGame()">Create New Match</button>
                <button onclick="gameManager.showJoinGame()">Join Match</button>
                <button onclick="gameManager.showRandomMatch()">Random Match</button>
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
                    <h3>👤 Profile of ${this.currentUser}</h3>
                    <button onclick="authManager.showMainScreen()">← Go Back</button>
                </div>
                
                <div class="profile-info">
                    <h4>Statistics</h4>
                    <p><strong>Total Score:</strong> ${profile.total_score}</p>
                    <p><strong>Level:</strong> ${profile.level}</p>
                    <p><strong>Matches Played:</strong> ${profile.matches_played}</p>
                    <p><strong>Wins:</strong> ${profile.matches_won}</p>
                    <p><strong>Losses:</strong> ${profile.matches_lost}</p>
                    <p><strong>Win Rate:</strong> ${(profile.win_rate * 100).toFixed(1)}%</p>
                </div>
                
                <div class="match-history">
                    <h4>Match History (${history.match_count})</h4>
                    ${history.matches.length > 0 ? 
                        history.matches.map(match => `
                            <div class="match-item">
                                <p><strong>VS ${match.player1 === this.currentUser ? match.player2 : match.player1}</strong></p>
                                <p>Result: <strong>${match.your_result === 'win' ? '✅ Win' : match.your_result === 'loss' ? '❌ Loss' : '⚪ Draw'}</strong></p>
                                <p>Score: ${JSON.stringify(match.scores)}</p>
                                <p><small>${new Date(match.end_time).toLocaleString()}</small></p>
                            </div>
                        `).join('') :
                        '<p>No matches played yet.</p>'
                    }
                </div>
            `;
        } catch (error) {
            console.error('Error loading profile:', error);
            document.getElementById('gameSection').innerHTML = `
                <div class="game-header">
                    <h3>👤 Profile</h3>
                    <button onclick="authManager.showMainScreen()">← Go Back</button>
                </div>
                <p>Error loading profile.</p>
            `;
        }
    }

    showMainScreen() {
        document.getElementById('gameSection').style.display = 'none';
        document.getElementById('welcome').style.display = 'block';
        this.updateUI();
    }

    showModal(content) {
        // Remove existing modals
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

        // Close modal by clicking outside
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