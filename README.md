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
Plugin Repository endpoints are as below:
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

### Development endpoints
Standard Health, Ping and Version endpoints are avaiable.
* `curl -X GET "https://<API URL>/health"`
* `curl -X GET "https://<API URL>/ping"`
* `curl -X GET "https://<API URL>/version"`

## Upload a Plugin
To upload a plugin, the repository's plugin metadata database must already have reference
to the plugin. This reference contains the 'secret' that allows users to modify plugins.
This is used to ensure that only users that have the 'secret' can alter the plugins state
in the plugin repository.

The adding of this initial plugin record should be via the 
[new_plugin_record.sh](/utils/new_plugin_record.sh) script. Details on using this 
script can be found in the [utils sub-directory README.md](/utils/README.md)

Once this initial metadata record has been added to the database, the initial plugin file 
and all subsequent plugin versions can be added to the repository via the API. 

Example of adding a plugin via the API:

```
curl -X POST -H 'Content-Type: application/octet-stream' -H "authorization:
bearer <SECRET>" --data-binary @<PLUGIN FILE PATH> https://<API URL>/plugin
```

where `<SECRET>` is the secret as stored in the plugin metadata database 
and `<PLUGIN FILE PATH>` is the path to the plugin file being added to the plugin repository. 

## Development

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

## Deployment

### Serverless
[Serverless](serverless.com) employed to managed deployment of the application.
#### Install plugins

```bash
sls plugin install --name serverless-python-requirements
sls plugin install --name serverless-wsgi
sls plugin install --name serverless-apigw-binary
sls plugin install --name serverless-plugin-git-variables
```

#### Deploy App
The QGIS plugin repository is fully deployable with the use of [serverless](https://serverless.com/)
```
serverless deploy --aws-profile <aws_profile> --stage <stage>  --resource-suffix <resource_suffix>
```

Where: 
* `aws_profile` is the user aws profile. Most commonly a reference to an entry in `~/.aws/credentials`.
* `stage` the stage being deployed (e.g. dev/prd). If not supplied defaults to dev.
*  `resource_suffix` Suffixed to the S3 bucket and DynamoDB resources for the purpose
of creating unique names but more importantly obscuring these resource names from others. 
