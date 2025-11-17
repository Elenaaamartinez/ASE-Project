workspace "Card Game Backend - La Escoba" "Microservices architecture for the card game La Escoba" {

    model {
        player = person "Player" "User who plays La Escoba matches"
        
        cardGameSystem = softwareSystem "Card Game Backend" "Backend system to play La Escoba online" {
            apiGateway = container "API Gateway" "Single entry point for all requests" "Kong/Nginx" {
                tags "Gateway"
            }
            
            authService = container "Authentication Service" "Handles registration, login and JWT tokens" "Python/Flask" {
                tags "Microservice"
            }
            
            playerService = container "Player Service" "Manages player profiles and stats" "Python/Flask" {
                tags "Microservice"
            }
            
            cardService = container "Card Service" "Provides info about Spanish cards" "Python/Flask" {
                tags "Microservice"
            }
            
            matchService = container "Match Service" "Handles live matches and game logic" "Python/Flask" {
                tags "Microservice"
            }
            
            historyService = container "History Service" "Stores and retrieves match history" "Python/Flask" {
                tags "Microservice"
            }
            
            authDB = container "Auth Database" "User credentials" "PostgreSQL" {
                tags "Database"
            }
            
            playerDB = container "Player Database" "Profiles and stats" "PostgreSQL" {
                tags "Database"
            }
            
            cardDB = container "Card Database" "Info for all 40 cards" "PostgreSQL" {
                tags "Database"
            }
            
            matchDB = container "Match Database" "Active match state" "Redis" {
                tags "Database"
            }
            
            historyDB = container "History Database" "Finished match records" "PostgreSQL" {
                tags "Database"
            }
        }
        
        # External relationships
        player -> apiGateway "Makes HTTP/REST requests" "HTTPS"
        
        # API Gateway relationships
        apiGateway -> authService "Authenticates and authorizes" "HTTPS"
        apiGateway -> playerService "Queries/updates players" "HTTPS"
        apiGateway -> cardService "Gets card info" "HTTPS"
        apiGateway -> matchService "Manages matches" "HTTPS"
        apiGateway -> historyService "Queries history" "HTTPS"
        
        # Inter-microservice relationships
        matchService -> historyService "Saves finished match" "HTTPS"
        matchService -> playerService "Updates stats" "HTTPS"
        playerService -> authService "Validates tokens" "HTTPS"
        
        # Database relationships
        authService -> authDB "Reads/Writes" "SQL"
        playerService -> playerDB "Reads/Writes" "SQL"
        cardService -> cardDB "Reads" "SQL"
        matchService -> matchDB "Reads/Writes" "Redis Protocol"
        historyService -> historyDB "Reads/Writes" "SQL"
    }

    views {
        systemContext cardGameSystem "SystemContext" {
            include *
            autoLayout lr
        }

        container cardGameSystem "Containers" {
            include *
            autoLayout tb
        }

        styles {
            element "Person" {
                shape person
                background #08427b
                color #ffffff
            }
            element "Gateway" {
                shape hexagon
                background #ff6b35
                color #ffffff
            }
            element "Microservice" {
                shape roundedBox
                background #1168bd
                color #ffffff
            }
            element "Database" {
                shape cylinder
                background #438dd5
                color #ffffff
            }
        }

        theme default
    }
}