# S3-QGIS plugins


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
