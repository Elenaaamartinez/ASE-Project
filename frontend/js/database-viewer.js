// File: frontend/js/database-viewer.js
class DatabaseViewer {
    static show() {
        // Create modal
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.9);
            z-index: 10000;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        `;

        modal.innerHTML = `
            <div style="
                background: white;
                border-radius: 15px;
                width: 90%;
                height: 90%;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            ">
                <div style="
                    background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
                    color: white;
                    padding: 20px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                ">
                    <h2 style="margin: 0;">🔍 Database Viewer</h2>
                    <button onclick="this.closest('.modal').remove()" style="
                        background: none;
                        border: none;
                        color: white;
                        font-size: 24px;
                        cursor: pointer;
                    ">×</button>
                </div>
                <div style="
                    flex: 1;
                    padding: 20px;
                    overflow: auto;
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                ">
                    <div>
                        <h3>👥 Players</h3>
                        <pre id="dbPlayers" style="background: #f8f9fa; padding: 15px; border-radius: 5px; max-height: 300px; overflow: auto;"></pre>
                    </div>
                    <div>
                        <h3>🎮 Matches</h3>
                        <pre id="dbMatches" style="background: #f8f9fa; padding: 15px; border-radius: 5px; max-height: 300px; overflow: auto;"></pre>
                    </div>
                    <div>
                        <h3>🃏 Cards</h3>
                        <pre id="dbCards" style="background: #f8f9fa; padding: 15px; border-radius: 5px; max-height: 300px; overflow: auto;"></pre>
                    </div>
                    <div>
                        <h3>📊 Stats</h3>
                        <pre id="dbStats" style="background: #f8f9fa; padding: 15px; border-radius: 5px; max-height: 300px; overflow: auto;"></pre>
                    </div>
                </div>
                <div style="
                    padding: 15px;
                    background: #ecf0f1;
                    display: flex;
                    gap: 10px;
                    justify-content: center;
                ">
                    <button onclick="DatabaseViewer.loadAll()" style="
                        padding: 10px 20px;
                        background: #27ae60;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                    ">🔄 Aggiorna Tutto</button>
                    <button onclick="this.closest('.modal').remove()" style="
                        padding: 10px 20px;
                        background: #e74c3c;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                    ">Chiudi</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        this.loadAll();
    }

    static async loadAll() {
        await this.loadPlayers();
        await this.loadMatches();
        await this.loadCards();
        await this.loadStats();
    }

    static async loadPlayers() {
        try {
            const response = await fetch('http://localhost:5000/players/mario');
            const data = await response.json();
            document.getElementById('dbPlayers').textContent = JSON.stringify(data, null, 2);
        } catch (error) {
            document.getElementById('dbPlayers').textContent = `Errore: ${error.message}`;
        }
    }

    static async loadMatches() {
        try {
            const response = await fetch('http://localhost:5000/history/mario');
            const data = await response.json();
            document.getElementById('dbMatches').textContent = JSON.stringify(data, null, 2);
        } catch (error) {
            document.getElementById('dbMatches').textContent = `Errore: ${error.message}`;
        }
    }

    static async loadCards() {
        try {
            const response = await fetch('http://localhost:5000/cards/cards');
            const data = await response.json();
            document.getElementById('dbCards').textContent = JSON.stringify(data, null, 2);
        } catch (error) {
            document.getElementById('dbCards').textContent = `Errore: ${error.message}`;
        }
    }

    static async loadStats() {
        try {
            const stats = {
                services: {},
                timestamp: new Date().toISOString()
            };

            // Test services
            const services = [
                { name: 'API Gateway', url: '/health' },
                { name: 'Auth', url: '/auth/health' },
                { name: 'Cards', url: '/cards/health' },
                { name: 'Matches', url: '/matches/health' },
                { name: 'Players', url: '/players/health' },
                { name: 'History', url: '/history/health' }
            ];

            for (const service of services) {
                try {
                    const response = await fetch(`http://localhost:5000${service.url}`);
                    stats.services[service.name] = response.ok ? '✅ Online' : '❌ Offline';
                } catch (e) {
                    stats.services[service.name] = '❌ Offline';
                }
            }

            document.getElementById('dbStats').textContent = JSON.stringify(stats, null, 2);
        } catch (error) {
            document.getElementById('dbStats').textContent = `Errore: ${error.message}`;
        }
    }
}
