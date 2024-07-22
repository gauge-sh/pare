# Variables
include .env


.PHONY: deploy
deploy:
	@echo "Deploying API to EC2..."
	ssh -i $(EC2_KEY_LOCATION) $(EC2_USER)@$(EC2_HOST) '\
		if [ ! -d $(REPO_NAME) ]; then \
			git clone $(REPO_URL) $(REPO_NAME); \
		fi && \
		cd $(REPO_NAME) && \
		git fetch --all && \
		git checkout $(BRANCH) && \
		git pull origin $(BRANCH) && \
		if [ ! -d $(VENV_DIR) ]; then \
			python3 -m venv $(VENV_DIR); \
		fi && \
		source $(VENV_DIR)/bin/activate && \
		pip install --upgrade pip pip-tools && \
		pip-compile $(API_DIR)/requirements.in -o $(API_DIR)/requirements.txt && \
		pip install -r $(API_DIR)/requirements.txt && \
		cd $(API_DIR) && \
		if pgrep gunicorn; then \
			pkill gunicorn; \
		fi && \
		gunicorn -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 src.app:app \
	'
	@echo "Deployment completed."