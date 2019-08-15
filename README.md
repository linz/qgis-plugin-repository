# S3-QGIS plugins

[![Build Status](https://travis-ci.com/linz/s3-qgis-plugin-repo.svg?token=H9yU2isbwj6ss3KvHYyJ&branch=master)](https://travis-ci.com/linz/s3-qgis-plugin-repo)

Store QGIS plugins in S3

## Development

Install the required dependencies

```bash
poetry install
```

Lint and format

```bash
poetry run black .
poetry run pylint src
```

## Serverless

### install plugins

```bash
sls plugin install --name  serverless-plugin-aws-alerts
sls plugin install --name  serverless-s3-deploy
```
