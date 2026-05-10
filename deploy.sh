#!/bin/bash

set -e

COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env.docker"
INIT_SQL="init.sql"

show_help() {
    cat << EOF
Chat App Deployment Script

Usage: ./deploy.sh [options]

Options:
    -b, --build      Build images before starting
    --no-cache       Build without using cache
    --logs           View service logs after starting
    --stop           Stop the application
    --clean          Remove containers, volumes, and clean Docker cache
    -h, --help       Show this help message
EOF
}

setup_database() {
    echo "Setting up database..."

    docker compose -f "$COMPOSE_FILE" stop postgres 2>/dev/null || true

    cat > "$INIT_SQL" << 'EOF'
CREATE ROLE dev_user WITH LOGIN PASSWORD '123456';
CREATE DATABASE chat_app OWNER dev_user;
EOF

    docker compose -f "$COMPOSE_FILE" run --rm --user postgres -v "$(pwd)/$INIT_SQL:/init.sql:ro" postgres bash -c "postgres --single -D /var/lib/postgresql/data < /init.sql"

    rm -f "$INIT_SQL"
    echo "Database setup complete."
}

start_app() {
    echo "Starting Chat App..."

    if [ ! -f "$ENV_FILE" ]; then
        echo "Creating $ENV_FILE from example..."
        cp ".env.example.docker" "$ENV_FILE"
    fi

    setup_database

    COMPOSE_ARGS=("compose" "-f" "$COMPOSE_FILE" "up" "-d")

    if [ "$BUILD" = true ]; then
        COMPOSE_ARGS+=("--build")
    fi
    if [ "$NO_CACHE" = true ]; then
        COMPOSE_ARGS+=("--no-cache")
    fi

    docker "${COMPOSE_ARGS[@]}"

    echo ""
    echo "Chat App started successfully!"
    echo "  Frontend: http://localhost"
    echo "  Backend:  http://localhost/api"
    echo ""
    echo "Run with --logs to view service logs"
}

show_logs() {
    docker compose -f "$COMPOSE_FILE" logs -f
}

stop_app() {
    echo "Stopping Chat App..."
    docker compose -f "$COMPOSE_FILE" down
    echo "Chat App stopped."
}

clean_app() {
    echo "Cleaning up Chat App..."
    docker compose -f "$COMPOSE_FILE" down -v --remove-orphans
    docker system prune -f
    echo "Cleanup complete."
}

BUILD=false
NO_CACHE=false
SHOW_LOGS=false
STOP_APP=false
CLEAN_APP=false

while [ $# -gt 0 ]; do
    case "$1" in
        -b|--build)
            BUILD=true
            ;;
        --no-cache)
            NO_CACHE=true
            ;;
        --logs)
            SHOW_LOGS=true
            ;;
        --stop)
            STOP_APP=true
            ;;
        --clean)
            CLEAN_APP=true
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
    shift
done

if [ "$STOP_APP" = true ]; then
    stop_app
elif [ "$CLEAN_APP" = true ]; then
    clean_app
elif [ "$SHOW_LOGS" = true ]; then
    show_logs
else
    start_app
fi