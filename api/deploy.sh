#!/bin/bash

# Variables
REPO_NAME=$1
REPO_URL=$2
BRANCH=$3
VENV_DIR=$4
API_DIR=$5

if [ ! -d "$REPO_NAME" ]; then
  git clone $REPO_URL $REPO_NAME
fi

cd $REPO_NAME

git fetch --all
git checkout $BRANCH
git pull origin $BRANCH

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv $VENV_DIR
fi

source $VENV_DIR/bin/activate
pip install --upgrade pip pip-tools
pip-compile $API_DIR/requirements.in -o $API_DIR/requirements.txt
pip install -r $API_DIR/requirements.txt

cd $API_DIR

if pgrep gunicorn; then
  pkill gunicorn
fi

nohup gunicorn \
  -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:8000 \
  --log-file gunicorn.log \
  --log-level DEBUG \
  --capture-output \
  --access-logfile gunicorn.log \
  --error-logfile gunicorn.log \
  --enable-stdio-inheritance \
  src.app:app &
echo "Deployment completed."
