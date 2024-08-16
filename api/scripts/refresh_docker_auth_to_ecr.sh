#!/bin/bash
set -e

source /home/ec2-user/pare-scripts/.venv/bin/activate
python /home/ec2-user/pare-scripts/refresh_docker_auth_to_ecr.py