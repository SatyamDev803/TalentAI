GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'
.PHONY: help auth-start auth-test job-test start stop test

help:
	@echo "TalentAI - Available Commands:"
	@echo "  make auth-start    - Start auth service"
	@echo "  make auth-test     - Test auth service"
	@echo "  make job-start    - Start job service"
	@echo "  make job-test      - Test job service"
	@echo "  make start         - Start all services"
	@echo "  make test          - Run all tests"
	@echo "  make stop          - Stop all services"

auth-start:
	@echo "$(GREEN)Starting Auth Service...$(NC)"
	@bash ./backend/scripts/services/auth/start_auth.sh

auth-test:
	@bash ./backend/scripts/services/auth/test.sh

job-start:
	@echo "$(GREEN)Starting Job Service...$(NC)"
	@bash ./backend/scripts/services/job/start_job.sh

job-test:

start:
	@docker-compose up

stop:
	@docker-compose down

test:
