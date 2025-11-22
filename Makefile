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
	@echo "  make resume-parser-start    - Start resume parser service"
	@echo "  make matching_engine-start    - Start matching engine service"
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

resume-parser-start:
	@echo "$(GREEN)Starting Resume Parser Service...$(NC)"
	@bash ./backend/scripts/services/resume_parser/start_resume_parser.sh

resume-parser-test:

matching-engine-start:
	@echo "$(GREEN)Starting Matching Engine Service...$(NC)"
	@bash ./backend/scripts/services/matching_engine/start_matching_engine.sh


matching-engine-test:


start:
	@docker-compose up

stop:
	@docker-compose down

test:
