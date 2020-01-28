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


### Architecture
The plugin repository is built using aws components as per the below diagram. 

\*Note: The [serverless.yml](/serverless.yml) deployment document is somewhat self-documenting
and is a good source to view the API architecture. 

#### Overview

![image](/documentation/overview.png)
**Above:** Overview of API architecture.  
 
1. An entry is added to Amazon Route 53 for DNS mapping. This allows the mapping of a custom 
domain name to the 
obscure API Gateway hostname.
2. All requests to the API are via the Amazon API Gateway. The 
[serverless-wsgi plugin](https://www.npmjs.com/package/serverless-wsgi) translates the 
API Gateway requests to and from standard WSGI requests as to interface with Flask.
3. Amazon Lambda is an event-driven, serverless computing platform. This is where the API's
 logic is invoked. This API logic is built into the Lambda function using Python and the 
 [Flask Python web framework](https://www.palletsprojects.com/p/flask/). The Lambda function 
 logic takes the request and invokes the appropriate actions based on the URL endpoint and
  HTTP verb. For more on API functionality see the [Repository API section](https://github.com/linz/s3-qgis-plugin-repo/tree/developer-docs#repository-api) 
  above.
4. When a new plugin is POSTed to the repository, the Lambda function reads the metadata 
from the plugins metadata.txt file and adds the metadata to the Amazon DynamoDB. 
Each record is unique based on a composite key comprising of the  Primary Partition Key: `id` 
(the is the plugin Id and is taken from the plugins root  directory name and is how QGIS 
considers unique plugins.) and the Primary Sort Key: `item_version`. The `item_version` record 
allows each plugin added to the repository  to be tracked via database versioning and is 
implemented via [Amazon DynamoDB recommendations of version control best practises](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-sort-keys.html#bp-sort-keys-version-control).
5. When a plugin file is POSTed to the API, the lambda function adds the plugin file to the
repositories S3 data store. 
6. Cloudwatch is configured to collect service logs and metrics. 

#### Architecture by user workflow examples
The below are user workflows to further demonstrate the API architecture 

##### POSTing a plugin to the repository

![image](/documentation/postplugin.png)
**Above:** User workflow: Adding a plugin to the repository

1. When making a request, the Route 53 DNS entry allows the user to use the human sensical URL.
2. The user makes a POST request to the API (see [above](https://github.com/linz/s3-qgis-plugin-repo/tree/developer-docs#repository-api) 
on how to perform this request) with the plugin file as the payload. 
3. API gateway maps this request to the Lambda function / Flask APP
4. The Lambda function is invoked
5. The lambda function adds the plugins metadata to the DynamoDB table
6. The lambda function adds the plugin to the S3 data store
7. A standard HTTP response is returned to the user (see swagger documentation on exact responses.
This is found at the API endpoint `<API_URL>/docs`)
8. Cloud watch stores log and metric information concerning the operation.

##### Make plugin information available to QGIS

![image](/documentation/getxml.png)
**Above:** User workflow: Get plugins xml document

1. Route S3 is used for DNS mapping
2. The user adds `https://<API URL>/plugins.xml` as a QGIS plugin repository source (see [above](https://github.com/linz/s3-qgis-plugin-repo/tree/developer-docs#consuming-the-qgis-plugins) 
for details on configuring QGIS repository sources). QGIS then makes the request to the 
API for the XML document describing available plugins. 
3. The http request is via API gateway
4. & 5. Lambda handles the request and invokes a DynamoDB query for all current QGIS plugins stored 
in the repo. The result of this query is then used to generate an XML document that 
indicates to qgis / the user which plugins are available for download.
6. The plugin xml document is returned to QGIS.
7. Cloud watch stores log and metric information about the operation.


##### Downloading QGIS plugins
Once QGIS has received the plugin repository XML document and displayed the available plugins
 to the QGIS user, the user can then download a plugin from the repository for use in QGIS. 

![image](/documentation/download_plugin.png)
**Above:** User workflow: downloading a plugin from the repository


1. When a QGIS user selects one of the repositories plugins for download, QGIS uses the 
xml documents `download_url` parameter to make a request to S3 for the resource.
2. S3 responds to QGIS with the plugin file that QGIS downloads and adds to the users QGIS 
profile. 
3. Cloud watch stores log and metric information about the operation.

