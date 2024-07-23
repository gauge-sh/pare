# Variables
include .env


.PHONY: deploy
deploy:
	@echo "Deploying API to EC2..."
	ssh -i $(EC2_KEY_LOCATION) $(EC2_USER)@$(EC2_HOST) '\
		if [ ! -d $(REPO_NAME) ]; then \
			mkdir -p $(REPO_NAME)/$(API_DIR); \
		fi \
	'
	scp -i $(EC2_KEY_LOCATION) $(API_DIR)/.env $(EC2_USER)@$(EC2_HOST):$(REPO_NAME)/$(API_DIR)/.env
	scp -i $(EC2_KEY_LOCATION) $(API_DIR)/deploy.sh $(EC2_USER)@$(EC2_HOST):deploy.sh
	ssh -i $(EC2_KEY_LOCATION) $(EC2_USER)@$(EC2_HOST) '\
		chmod +x deploy.sh && \
		./deploy.sh $(REPO_NAME) $(REPO_URL) $(BRANCH) $(VENV_DIR) $(API_DIR) \
	'


.PHONY: logs
logs:
	@echo "Trailing logs..."
	ssh -i $(EC2_KEY_LOCATION) $(EC2_USER)@$(EC2_HOST) '\
		cd $(REPO_NAME)/$(API_DIR) && \
		tail -f gunicorn.log \
	'
