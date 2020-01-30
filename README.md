# S3-QGIS plugins

[![Build Status](https://travis-ci.com/linz/s3-qgis-plugin-repo.svg?token=H9yU2isbwj6ss3KvHYyJ&branch=master)](https://travis-ci.com/linz/s3-qgis-plugin-repo)
[![Build Status](https://github.com/linz/s3-qgis-plugin-repo/workflows/Build/badge.svg)](https://github.com/linz/s3-qgis-plugin-repo/actions)


A Repository for storing and managing QGIS plugins.
* The repository is built around a web API for managing and serving QGIS plugins.
* LINZ uses the repository to make QGIS plugins available to staff during development
  but also host plugins that are not of use to any other communities due to them being
  so tailored to LINZ's workflows and environment.

## Consuming the QGIS Plugins
Once deployed, QGIS needs to be configured to read the plugin repository. To do this,
see the [QGIS documentation](https://docs.qgis.org/2.8/en/docs/training_manual/qgis_plugins/fetching_plugins.html#basic-fa-configuring-additional-plugin-repositories)
for connecting QGIS with plugin repositories.

For the repository's URL please see the repository administrator. The URL path for
connecting QGIS to the repository is `https://<API URL>/plugins.xml`.

## Repository API
### Plugin management endpoints
\* For specifics on API schema see the swagger docs at `<API_URL>/docs`

Plugin Repository endpoints and verbs are as below:
* **`/plugin` `POST`**
  * Upload a new version of a plugin
  * Usage: _```curl -X POST -H 'Content-Type: application/octet-stream' -H "authorization:
    bearer 12345" --data-binary @linz-data-importer-2.0.1.zip https://<API URL>/plugin```
* **`/plugin` `GET`**
  * List the most current version of all plugins
  * Usage: ```curl -X GET "https://<API URL>/plugin"```
* **`/plugin/<plugin_id>` `DELETE`**
  * Archive a plugin so that it is not accessible via QGIS
  * A plugin can be unarchived by POSTing a new version
  * Usage: ```curl -X DELETE -H "authorization: bearer 12345" "https://<API URL>/plugin/<Plugin_id>"```_
* **`/plugin/<plugin_id>` `GET`**
  * List the current version of a specific plugin
  * Usage: _```curl -X GET "https://<API URL>/plugin/<Plugin_id>"```
* **`/plugin/<plugin_id>/revision` `GET`**
  * List all revisions of a specific plugin
  * Usage: ```curl -X GET "https://<API URL>/plugin/<Plugin_id/revision>"```
* **`/plugins.xml` `GET`**
  * Retrieve the XML document describing current Plugins
  * Usage: Most commonly added to QGIS configuration as per the [above details](https://github.com/linz/s3-qgis-plugin-repo/tree/developer-docs#consuming-the-qgis-plugins)
  * Query Parameter Usage: The `qgis` query parameter can be supplied to filter 
    out plugins from the XML document with a qgis maximum version value less than the 
    `qgis` parameter value. This is for example to ensure the QGIS 3 application 
    does not retrieve plugins only compatible with QGIS 2. 
    For example: `curl -X GET "https://<API URL>/plugins?qgis=3.0` (this will
### Development endpoints
Standard Health, Ping and Version endpoints are available.
* `curl -X GET "https://<API URL>/health"`
* `curl -X GET "https://<API URL>/ping"`
* `curl -X GET "https://<API URL>/version"`

## Upload a Plugin
To upload a plugin, the repository's plugin metadata database must already have reference
to the plugin. This is to ensure that only users that have the 'secret' for each plugin
can modify plugins.

### Adding a plugin to metadata database

This can only be performed by a administrator of the repository metadata database.

For each plugin:

**1. A metedata record must be created**
  * This stores the secret that must be validated to
alter the plugin.

```
{
  "id": "<plugin directory name>", # String
  "item_version": "metadata", # String
  "secret": "1b87bf4994a642f78af9a33626b59286"  # String
}
```
_**Above:** An example of creating the metadata record. The plugin id must be the name of
the QGIS plugin's root directory._

**2. A version zero record must be created.**

```
{
  "id": "<plugin directory name>", # String
  "item_version": "000000", # String. Must be 6x0's
  "revisions": 0,  # Number
}
```
_**Above:** An example of creating the version zero record._

Once the initial records have been added to the DynamoDB database as above, anyone with
the "secret" can modify the plugin stored in the repository by POSTing a plugin zipfile
with the same root directory name (id must match plugin root directory name).

## Development


### Create a development environment

Create and activate a virtual env fff

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

### Deployment

#### Serverless
[Serverless](serverless.com) employed to managed deployment of the application.
##### Install plugins

```bash
sls plugin install --name serverless-python-requirements
sls plugin install --name serverless-wsgi
sls plugin install --name serverless-apigw-binary
sls plugin install --name serverless-plugin-git-variables
```

##### Deploy App
The QGIS plugin repository is fully deployable with the use of [serverless](https://serverless.com/)
```
serverless deploy
```

### Arcitecture 
Please see the [/documentation/ARCHITECTURE.md](/documentation/ARCHITECTURE.md) document. 

