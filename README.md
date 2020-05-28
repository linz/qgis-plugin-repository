
# QGIS plugin Repository

[![Build Status](https://travis-ci.com/linz/s3-qgis-plugin-repo.svg?token=H9yU2isbwj6ss3KvHYyJ&branch=master)](https://travis-ci.com/linz/s3-qgis-plugin-repo)
[![Build Status](https://github.com/linz/s3-qgis-plugin-repo/workflows/Build/badge.svg)](https://github.com/linz/s3-qgis-plugin-repo/actions)


A Repository for storing, managing and serving QGIS plugins.
* The repository is built around a web API for managing and serving QGIS plugins.
* LINZ uses the repository to make QGIS plugins available to staff during development
  but also host plugins that are not of use to any other communities due to them being
  so tailored to LINZ's workflows and environment.

## Consuming the QGIS Plugins
Once deployed, QGIS needs to be configured to read the plugin repository. To do this,
see the [QGIS documentation](https://docs.qgis.org/2.8/en/docs/training_manual/qgis_plugins/fetching_plugins.html#basic-fa-configuring-additional-plugin-repositories)
for connecting QGIS with plugin repositories.

For the repository's URL please see the repository administrator. The URL path for connecting
QGIS to the repository is:
* `https://<API URL>/v1/plugins.xml` for production released plugins
* `https://<API URL>/v1/dev/plugins.xml`for development version of plugins.

## Access

 **IMPORTANT**

Although only plugin admins with a plugin's secret key can modify a plugin as stored in the repository, anyone with the repositories url can access the plugins. **For this reason, only plugins that meet the criteria for open sourcing should be uploaded to the repository**.

To be sure if a plugin can be published, review the directives of NZGOAL. Start with the [exemptions section](https://www.data.govt.nz/manage-data/policies/nzgoal/nzgoal-se/#exceptions). 

In short, do not publish if the plugin contains sensitive information. 

## Repository API

### Plugin  Management API - Dev/Prd  Separation
The plugin repository API can be used to store and serve both a production and a
development version of each plugin. This is to support the workflow where developers release
a production version of the plugin to general users but also want to make a development
version of the same plugin available to users for testing and feedback.

The separation of the plugin versions is via the `?stage` query parameter. When making
a requests to the API without the `?stage` query parameter, the request defaults to production plugins.
To post or get development plugins use query parameter `?stage=dev`

#### QGIS XML Document Dev/Prd  Separation
Unfortunately the QGIS plugin manager configuration does not allow extra query parameters
to be configured (only `?qgis=<qgis_verison> is configured). The result of this is
development/production plugin version separation is via separate URLs

* Production plugins can be found at: `https://<API URL>/v1/plugins.xml`
* Development plugins can be found at: `https://<API URL>/v1/dev/plugins.xml`

##### Separate Dev/Prd QGIS Environments
It is recommended that QGIS users use the [QGIS user profiles functionality](https://docs.qgis.org/3.4/en/docs/user_manual/introduction/qgis_configuration.html#working-with-user-profiles)
to separate QGIS production and development  environments. This means configuring the default
user profile to consume plugins from the production API (`https://<API URL>/v1/plugins.xml`) and
create a QGIS user profile for development plugins that points at  the dev URL
`(https://<API URL>/v1/dev/plugins.xml`). This will ensure there is not the confusion
as to which version of the plugin is installed in the QGIS environment.

### Plugin Management Endpoints
\* For specifics on API schema see the swagger docs at `<API_URL>/docs`



Plugin Repository endpoints, verbs and query params are as below:


* **`GET` `/plugin`**
Lists the most current version of all plugins
  * Usage - Production Plugins: ```curl -X GET "https://<API URL>/v1/plugin"```
  * Usage - Development Plugins: ```curl -X GET "https://<API URL>/v1/plugin?stage=dev"```

* **`POST` `/plugin/<PLUGIN ID>`**
 Upload a new version of a plugin
  * Usage - Production Plugins: ```curl -X POST -H 'Content-Type: application/octet-stream' -H "authorization:
    bearer <SECRET>" --data-binary @<PATH TO PLUGIN ZIPFILE> https://<API URL>/v1/plugin/<PLUGIN ID>```
  * Usage - Development Plugins: ```curl -X POST -H 'Content-Type: application/octet-stream' -H "authorization:
    bearer <SECRET>" --data-binary @<PATH TO PLUGIN ZIPFILE> https://<API URL>/v1/plugin/<PLUGIN ID?stage=dev>```

* **`DELETE` `/plugin/<PLUGIN ID>`**
 Archive a plugin so that it is not accessible to QGIS users
 \* A plugin can be unarchived by POSTing a new version
  * Usage - Production Plugins: ```curl -X DELETE -H "authorization: bearer <SECRET>" "https://<API URL>/v1/plugin/<PLUGIN ID"```
  * Usage - Development Plugins: ```curl -X DELETE -H "authorization: bearer <SECRET>" "https://<API URL>/v1/plugin/<PLUGIN ID>?stage=dev"```

* **`GET` `/plugin/<PLUGIN ID>`**
List the current version of a specific plugin
  * Usage - Production Plugins : ```curl -X GET "https://<API URL>/v1/plugin/<PLUGIN ID>"```
   * Usage - Development Plugins : ```curl -X GET "https://<API URL>/v1/plugin/<PLUGIN ID>?stage=dev"```

* **`GET` `/plugin/<PLUGIN ID>/revision`**
List all revisions of a specific plugin
  *  Usage - Production Plugins :  ```curl -X GET "https://<API URL>/v1/plugin/<PLUGIN ID>/revision>"```
  *  Usage - Development Plugins :  ```curl -X GET "https://<API URL>/v1/plugin/<PLUGIN ID>/revision>?stage=dev"```

* **`GET` `/plugins.xml`**
Retrieve the XML document describing all current plugins
Most commonly added to QGIS configuration as per the [above details](https://github.com/linz/s3-qgis-plugin-repo/tree/developer-docs#consuming-the-qgis-plugins)
  * Usage - Production Plugins: configure QGIS to use the URL `https://<API URL>/v1/plugins.xml`
  * Usage - Development Plugins: configure QGIS to use the URL ``https://<API URL>/v1/dev/plugins.xml``
   * Usage - QGIS Version Query Parameter: The `qgis` query parameter can be supplied to filter
   out plugins not compatible with the users version of QGIS.
   The QGIS plugin manager automatically appends this query parameter to the URL
   as per the version of QGIS being used.

### Development endpoints
Standard Health, Ping and Version endpoints are available.
* `curl -X GET "https://<API URL>/v1/health"`
* `curl -X GET "https://<API URL>/v1/ping"`
* `curl -X GET "https://<API URL>/v1/version"`

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
bearer <SECRET>" --data-binary @<PLUGIN FILE PATH> https://v1/<API URL>/plugin
```

where `<SECRET>` is the secret as stored in the plugin metadata database
and `<PLUGIN FILE PATH>` is the path to the plugin file being added to the plugin repository.

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

#### Deployment - Development Environment

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
serverless deploy --aws-profile <aws_profile> --stage <stage>  --resource-suffix <resource_suffix>
```

Where:

* `aws_profile` is the user aws profile. Most commonly a reference to an entry in `~/.aws/credentials`.
* `stage` the stage being deployed (e.g. dev/prd). If not supplied defaults to dev.
*  `resource_suffix` Suffixed to the S3 bucket and DynamoDB resources for the purpose
of creating unique names but more importantly obscuring these resource names from others.
* `dns` (Not shown in the example as this option is used for development. Do not supply for prd deployments) Ensures correct paths for Swagger documents when not mapping the apigateway url to a domain name. When using raw apigateway urls use `--dns false` to ensure correct SwaggerUI paths

#### Deployment - Production Environment
Deployment to the production environment must be via the GitHub Action. The
Github Action's deployment step is triggered when a tag is pushed. Therefore
to deploy to the production environment all that is required is to push a
relevant tag via git.

###### Changelog
As well as the GitHub action deploying the applicaiton to production on the push of a tag, it also generates a GitHuB release. The release notes are as per the changelog. Therefore, please ensure the changelog is updated as part of each release.  

### Architecture

Please see the [/documentation/ARCHITECTURE.md](/documentation/ARCHITECTURE.md) document.source_suffix>

