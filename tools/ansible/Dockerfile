FROM python:3.11-slim

ENV PIP_NO_CACHE_DIR=1

RUN python -m pip install --upgrade pip setuptools wheel && \
    python -m pip install ansible-core==2.18.6 && \
    ansible-galaxy collection install community.docker

WORKDIR /workspace

CMD ["ansible-playbook", "--version"]
