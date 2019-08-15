# S3-QGIS plugins

[![Build Status](https://travis-ci.com/linz/s3-qgis-plugin-repo.svg?token=H9yU2isbwj6ss3KvHYyJ&branch=master)](https://travis-ci.com/linz/s3-qgis-plugin-repo)

Store QGIS plugins in S3

## Development

Create and activate a virtual env

```bash
virtualenv .venv
source .venv/bin/activate
```

Install the required dependencies

```bash
pip install -r requirements-dev.txt
pip install -r requirements.txt
```

Lint and format

```bash
black src/ --diff --check
pylint src
```

## Serverless

### install plugins

```bash
sls plugin install --name serverless-python-requirements
sls plugin install --name serverless-s3-deploy
```
