// MATCHMAKING ENGINE v2.1.0 - TERMINAL INTERFACE
// Dynamic Backend-Driven Dashboard Controller

class TerminalMatchmakingEngine {
    constructor() {
        this.players = [];
        this.events = [];
        this.gameModes = {};
        this.currentMode = null;
        this.matchCount = 0;
        this.isRunning = false;
        this.apiBase = 'http://localhost:8000/api/v2';
        this.wsBase = 'ws://localhost:8000';
        this.socket = null;
        this.matchEvents = [];
        this.processedMatches = new Set();
        
        // Player data templates
        this.playerNames = [
            'ALPHA_01', 'BETA_02', 'GAMMA_03', 'DELTA_04', 'EPSILON_05', 'ZETA_06',
            'THETA_07', 'IOTA_08', 'KAPPA_09', 'LAMBDA_10', 'MU_11', 'NU_12',
            'XI_13', 'OMICRON_14', 'PI_15', 'RHO_16', 'SIGMA_17', 'TAU_18'
        ];
        
        this.regions = ['in-central', 'us-east', 'eu-west', 'asia-se'];
        this.skillRange = { min: 45, max: 130 };
        
        this.init();
    }

    async init() {
        this.setupEventListeners();
        this.setupWebSocket();
        await this.loadBackendData();
        this.startSystemLogging();
        this.simulateInitialLoad();
    }

    async loadBackendData() {
        try {
            this.logEvent('> LOADING BACKEND DATA...');
            
            // Create a timeout promise
            const timeoutPromise = new Promise((_, reject) => 
                setTimeout(() => reject(new Error('Backend request timeout')), 5000)
            );
            
            // Load game modes from backend with timeout
            const gameModesResponse = await Promise.race([
                fetch(`${this.apiBase}/game_modes`),
                timeoutPromise
            ]);
            
            if (!gameModesResponse.ok) {
                throw new Error(`HTTP ${gameModesResponse.status}: ${gameModesResponse.statusText}`);
            }
            
            const gameModesData = await gameModesResponse.json();
            this.gameModes = gameModesData.game_modes;
            
            console.log('Loaded game modes:', this.gameModes);
            
            // Set first game mode as default
            this.currentMode = Object.keys(this.gameModes)[0];
            
            // Update UI with backend data
            this.updateGameModeButtons();
            this.updateSystemStatus();
            
            this.logEvent(`> LOADED ${Object.keys(this.gameModes).length} GAME MODES FROM BACKEND`);
            
        } catch (error) {
            this.logEvent(`[X] ERROR: Failed to load backend data - ${error.message}`);
            console.error('Backend data loading failed:', error);
            
            // Fallback to hardcoded modes if backend fails
            this.gameModes = {
                '1v1_duel': { description: 'A classic 1v1 fight to the finish.' },
                '2v2_clash': { description: 'A team-based 2v2 Clash.' },
                '3v3_arena': { description: 'A team-based 3v3 battle.' }
            };
            this.currentMode = Object.keys(this.gameModes)[0];
            this.updateGameModeButtons();
            this.logEvent('> USING FALLBACK GAME MODES');
        }
    }

    setupWebSocket() {
        try {
            // Connect to backend WebSocket for real-time match events
            this.socket = io(this.wsBase, {
                auth: {
                    playerId: 'dashboard' // Dashboard client identifier
                }
            });

            this.socket.on('connect', () => {
                this.logEvent('> WEBSOCKET: Connected to backend');
            });

            this.socket.on('disconnect', () => {
                this.logEvent('[X] WEBSOCKET: Disconnected from backend');
            });

            this.socket.on('match_found', (data) => {
                // this.logEvent(`[*] REAL MATCH FOUND: ${data.matchId}`);
                this.handleMatchFound(data);
            });

            this.socket.on('dashboard_log', (data) => {
                this.logEvent(`BACKEND: ${data.message}`);
            });

            this.socket.on('pool_updated', (data) => {
                this.logEvent(`POOL UPDATE: ${data.gameMode} | ${data.action}`);
            });

        } catch (error) {
            this.logEvent(`[X] WEBSOCKET ERROR: ${error.message}`);
        }
    }

    setupEventListeners() {
        // Player simulation buttons
        document.querySelectorAll('[data-player]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.simulatePlayer(parseInt(e.target.dataset.player));
            });
        });

        // Control buttons
        document.getElementById('runMatch').addEventListener('click', () => {
            this.runMatch();
        });

        document.getElementById('clearPool').addEventListener('click', () => {
            this.clearPool();
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            this.handleKeyboard(e);
        });
    }

    updateGameModeButtons() {
        const modeSelector = document.querySelector('.mode-selector');
        if (!modeSelector) {
            console.error('Mode selector element not found');
            return;
        }
        
        console.log('Updating game mode buttons with modes:', Object.keys(this.gameModes));
        
        modeSelector.innerHTML = '';
        
        if (Object.keys(this.gameModes).length === 0) {
            console.warn('No game modes available');
            return;
        }
        
        Object.keys(this.gameModes).forEach(mode => {
            const button = document.createElement('button');
            button.className = 'control-button';
            button.setAttribute('data-mode', mode);
            button.textContent = mode.toUpperCase().replace('_', ' ');
            
            if (mode === this.currentMode) {
                button.classList.add('active');
            }
            
            button.addEventListener('click', (e) => {
                console.log('Game mode button clicked:', mode);
                this.selectMode(mode);
            });
            
            modeSelector.appendChild(button);
            console.log('Added button for mode:', mode);
        });
        
        console.log(`Created ${Object.keys(this.gameModes).length} game mode buttons`);
    }

    selectMode(mode) {
        // Remove active class from all mode buttons
        document.querySelectorAll('[data-mode]').forEach(btn => {
            btn.classList.remove('active');
        });
        
        // Add active class to selected mode
        document.querySelector(`[data-mode="${mode}"]`).classList.add('active');
        
        this.currentMode = mode;
        this.logEvent(`MODE CHANGED: ${mode.toUpperCase()}`);
    }

    async simulatePlayer(playerNum) {
        if (!this.currentMode) {
            this.logEvent('[X] ERROR: No game mode selected');
            return;
        }

        const playerId = this.playerNames[Math.floor(Math.random() * this.playerNames.length)];
        const skill = Math.floor(Math.random() * (this.skillRange.max - this.skillRange.min + 1)) + this.skillRange.min;
        const region = this.regions[Math.floor(Math.random() * this.regions.length)];
        
        const playerData = {
            playerName: playerId,
            skill: skill,
            regionPreference: [{ [region]: 1 }]
        };

        try {
            this.logEvent(`> QUEUEING PLAYER_${playerNum} FOR ${this.currentMode.toUpperCase()}...`);
            
            const response = await fetch(`${this.apiBase}/join_queue?gameMode=${this.currentMode}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(playerData)
            });

            if (response.ok) {
                const result = await response.json();
                const player = {
                    id: playerId,
                    skill: skill,
                    region: region,
                    joinTime: new Date(),
                    playerNum: playerNum,
                    ticketId: result.ticket.ticket
                };

                this.players.push(player);
                this.updatePlayerPool();
                this.logEvent(`✓ PLAYER_${playerNum} QUEUED [SKILL: ${skill} | REGION: ${region}]`);
                
                // Update button state
                const button = document.querySelector(`[data-player="${playerNum}"]`);
                button.classList.add('active');
                button.textContent = `P${playerNum} ✓`;
            } else {
                const error = await response.json();
                this.logEvent(`[X] ERROR: Failed to queue player - ${error.detail}`);
            }
        } catch (error) {
            this.logEvent(`[X] ERROR: Failed to queue player - ${error.message}`);
        }
    }

    runMatch() {
        this.logEvent('[ℹ] BACKEND MATCHING: Matches are handled by the backend worker');
        this.logEvent('> Backend worker automatically processes matches every 2 seconds');
        this.logEvent('> Players will be matched when conditions are met');
        this.logEvent('> Real-time match events are received via WebSocket');
    }

    // Removed old createMatch method - now using simulateMatchFound for better match event handling

    getMostCommonRegion() {
        if (this.players.length === 0) return 'NONE';
        const regionCounts = {};
        this.players.forEach(player => {
            regionCounts[player.region] = (regionCounts[player.region] || 0) + 1;
        });
        return Object.keys(regionCounts).reduce((a, b) => 
            regionCounts[a] > regionCounts[b] ? a : b
        );
    }

    clearPool() {
        this.players = [];
        this.updatePlayerPool();
        this.logEvent('> PLAYER POOL CLEARED');
        
        // Reset all player buttons
        document.querySelectorAll('[data-player]').forEach(btn => {
            btn.classList.remove('active');
            btn.textContent = btn.textContent.replace(' ✓', '');
        });
    }

    // Removed resetSystem method to match backend

    updatePlayerPool() {
        const playerList = document.getElementById('playerList');
        playerList.innerHTML = '';
        
        if (this.players.length === 0) {
            playerList.innerHTML = '<div class="log-entry">NO ACTIVE PLAYERS</div>';
        } else {
            this.players.forEach(player => {
                const playerEntry = document.createElement('div');
                playerEntry.className = 'player-entry';
                playerEntry.innerHTML = `
                    <div>
                        <span class="player-id">${player.id}</span>
                        <span class="player-stats">[SKILL: ${player.skill} | REGION: ${player.region}]</span>
                    </div>
                    <div class="timestamp">${this.formatTime(player.joinTime)}</div>
                `;
                playerList.appendChild(playerEntry);
            });
        }
        
        this.updateStatistics();
    }

    updateStatistics() {
        document.getElementById('totalPlayers').textContent = this.players.length;
        
        if (this.players.length > 0) {
            const avgSkill = Math.round(this.players.reduce((sum, p) => sum + p.skill, 0) / this.players.length);
            document.getElementById('avgSkill').textContent = avgSkill;
            
            const uniqueRegions = [...new Set(this.players.map(p => p.region))];
            document.getElementById('regions').textContent = uniqueRegions.join(', ');
        } else {
            document.getElementById('avgSkill').textContent = '0';
            document.getElementById('regions').textContent = 'NONE';
        }
    }

    updateSystemStatus() {
        document.getElementById('queueStatus').textContent = this.players.length > 0 ? 'ACTIVE' : 'EMPTY';
        document.getElementById('matchCount').textContent = this.matchCount;
    }

    logEvent(message) {
        const timestamp = new Date();
        const event = {
            message: message,
            timestamp: timestamp
        };
        
        this.events.push(event);
        this.addEventToLog(event);
    }

    addEventToLog(event) {
        const eventLog = document.getElementById('eventLog');
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry new';
        logEntry.innerHTML = `
            <span class="timestamp">[${this.formatTime(event.timestamp)}]</span> ${event.message}
        `;
        
        eventLog.appendChild(logEntry);
        
        // Auto-scroll to bottom
        eventLog.scrollTop = eventLog.scrollHeight;
        
        // Remove glow effect after animation
        setTimeout(() => {
            logEntry.classList.remove('new');
        }, 500);
    }

    clearEventLog() {
        document.getElementById('eventLog').innerHTML = '';
    }

    formatTime(date) {
        return date.toLocaleTimeString('en-US', { 
            hour12: false, 
            hour: '2-digit', 
            minute: '2-digit', 
            second: '2-digit' 
        });
    }

    startSystemLogging() {
        // Real-time system status updates
        setInterval(async () => {
            await this.updateSystemStatus();
        }, 2000);
        
        // Pool status updates
        setInterval(async () => {
            await this.updatePoolStatus();
        }, 3000);
        
        // Match events now handled via WebSocket
        // Removed polling-based match checking
    }

    async updateSystemStatus() {
        try {
            const response = await fetch(`${this.apiBase}/system_status`);
            const data = await response.json();
            
            // Update system status display
            const statusElement = document.querySelector('.system-status');
            if (statusElement) {
                statusElement.textContent = `SYSTEM: ${data.system.status.toUpperCase()} | ACTIVE QUEUES: ${data.system.active_queues} | UPTIME: ${data.system.uptime}`;
            }
        } catch (error) {
            console.error('Failed to update system status:', error);
        }
    }

    async updatePoolStatus() {
        try {
            const response = await fetch(`${this.apiBase}/pool_status`);
            const data = await response.json();
            
            // Update pool statistics
            const totalPlayers = Object.values(data.pool_status).reduce((sum, pool) => sum + pool.queue_size, 0);
            document.getElementById('totalPlayers').textContent = totalPlayers;
            
            // Update queue status
            const activeQueues = Object.values(data.pool_status).filter(pool => pool.queue_size > 0).length;
            document.getElementById('queueStatus').textContent = activeQueues > 0 ? 'ACTIVE' : 'EMPTY';
            
        } catch (error) {
            console.error('Failed to update pool status:', error);
        }
    }



    createTeams(players) {
        const teams = {
            team_1: [],
            team_2: []
        };
        
        players.forEach((player, index) => {
            const teamKey = index % 2 === 0 ? 'team_1' : 'team_2';
            teams[teamKey].push({
                playerName: player.id,
                skill: player.skill,
                region: player.region
            });
        });
        
        return teams;
    }

    handleMatchFound(matchEvent) {
        this.matchEvents.push(matchEvent);
        this.matchCount++;
        
        // Log the match found event
        this.logEvent(`[*] MATCH FOUND: ${matchEvent.matchId}`);
        this.logEvent(`    Mode: ${matchEvent.gameMode.toUpperCase()}`);
        this.logEvent(`    Region: ${matchEvent.region}`);
        this.logEvent(`    Players: ${matchEvent.ticketIds.length}`);
        
        // Display match details in the match events panel
        this.displayMatchEvent(matchEvent);
        
        // Remove matched players from local pool
        this.players = this.players.filter(player => 
            !matchEvent.ticketIds.includes(player.ticketId || player.id)
        );
        
        // Update UI
        this.updatePlayerPool();
        this.updateSystemStatus();
        
        // Reset player buttons
        document.querySelectorAll('[data-player]').forEach(btn => {
            btn.classList.remove('active');
            btn.textContent = btn.textContent.replace(' ✓', '');
        });
        
        // Update match count display
        document.getElementById('matchCount').textContent = this.matchCount;
    }

    displayMatchEvent(matchEvent) {
        const eventLog = document.getElementById('eventLog');
        if (!eventLog) return;
        
        // Create match event display
        const matchEntry = document.createElement('div');
        matchEntry.className = 'match-log new';
        matchEntry.innerHTML = `
            <div class="log-entry" style="color: #00FF00; font-weight: bold;">
                [*] MATCH CREATED: ${matchEvent.matchId}
            </div>
            <div class="log-entry" style="margin-left: 20px;">
                Mode: ${matchEvent.gameMode.toUpperCase()} | Region: ${matchEvent.region}
            </div>
            <div class="log-entry" style="margin-left: 20px;">
                Teams: ${Object.keys(matchEvent.teams).length} | Players: ${matchEvent.ticketIds.length}
            </div>
            <div class="log-entry" style="margin-left: 20px; font-size: 10px; color: #FFB000; opacity: 0.7;">
                ${new Date(matchEvent.timestamp).toLocaleTimeString()}
            </div>
        `;
        
        eventLog.appendChild(matchEntry);
        
        // Auto-scroll to bottom
        eventLog.scrollTop = eventLog.scrollHeight;
        
        // Remove glow effect after animation
        setTimeout(() => {
            matchEntry.classList.remove('new');
        }, 2000);
    }

    updateSystemUptime() {
        const systemStatus = document.querySelector('.system-status');
        const now = new Date();
        const uptime = Math.floor((now - this.startTime) / 1000);
        const days = Math.floor(uptime / 86400);
        const hours = Math.floor((uptime % 86400) / 3600);
        const minutes = Math.floor((uptime % 3600) / 60);
        
        systemStatus.textContent = `SYSTEM: ONLINE | CPU: ${Math.floor(Math.random() * 30 + 20)}% | MEM: ${(Math.random() * 2 + 1).toFixed(1)}GB | UPTIME: ${days}d ${hours}h ${minutes}m`;
    }

    simulateInitialLoad() {
        this.startTime = new Date();
        
        setTimeout(() => {
            this.logEvent('> SYSTEM INITIALIZATION COMPLETE');
            this.logEvent('> READY FOR PLAYER CONNECTIONS');
        }, 2000);
    }

    handleKeyboard(e) {
        // Ctrl/Cmd + number keys for player simulation (1-4 only)
        if ((e.ctrlKey || e.metaKey) && e.key >= '1' && e.key <= '4') {
            e.preventDefault();
            this.simulatePlayer(parseInt(e.key));
        }
        
        // Ctrl/Cmd + R for run match
        if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
            e.preventDefault();
            this.runMatch();
        }
        
        // Ctrl/Cmd + C for clear pool
        if ((e.ctrlKey || e.metaKey) && e.key === 'c') {
            e.preventDefault();
            this.clearPool();
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Initialize the engine
    const engine = new TerminalMatchmakingEngine();
    console.log('TerminalMatchmakingEngine initialized:', engine);
});