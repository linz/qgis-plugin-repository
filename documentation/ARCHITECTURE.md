# Architecture
This document is to give a brief overview of the systems components and their interactions.
This is to help anyone wanting to understand the API's architecture and operation. 

\*Note: The [serverless.yml](/serverless.yml) deployment document is somewhat self-documenting
and is a good source to view/understand the API's architecture. 

## Overview
![image](/documentation/overview.png)
**Above:** Overview of API architecture.  
 
1. An entry is added to Route 53 for DNS mapping.
2. All requests to the API are via API Gateway.
3. API logic is built into the Lambda function using Python and the 
 [Flask Python web framework](https://www.palletsprojects.com/p/flask/). For details on 
 specific API functionality, see the [README.md](https://github.com/linz/qgis-plugin-repository/blob/master/README.md#repository-api) 
 document. 
4. When a plugin is POSTed to the repository, the Lambda function reads 
from the plugins metadata.txt file and adds this metadata to the DynamoDB Database. Each record is 
unique based on a composite key comprising of the  Primary Partition Key: `id` (this being the plugin Id 
taken from the plugin's root directory name. QGIS also uses this name when considering if a 
plugin is unique) and the Primary Sort Key: `item_version`. The `item_version` record allows 
each plugin added to the repository to be tracked via database versioning and is implemented
via [Amazon DynamoDB recommendations of version control best practises](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-sort-keys.html#bp-sort-keys-version-control).
5. When a plugin file is POSTed to the API, the lambda function adds the plugin file to the 
   repositories S3 data store. 

## Architecture by user workflow examples
The below are user workflows to further demonstrate the API architecture 

### POSTing a plugin to the repository

![image](/documentation/postplugin.png)
**Above:** User workflow: Adding a plugin to the repository

1. Route 53 is used for DNS mapping.
2. The user makes a POST request to the API with the plugin file as the payload. 
3. API gateway maps this request to the Lambda function / Flask app.
4. The Lambda function is invoked.
5. The lambda function adds the plugins metadata to the DynamoDB table.
6. The lambda function adds the plugin to the S3 data store.
7. A standard HTTP response is returned to the user (see swagger documentation on exact responses.
This is found at the API endpoint `<API_URL>/docs`)

### Make plugin repository data available to QGIS

![image](/documentation/getxml.png)
**Above:** User workflow: Get plugins xml document

1. Route 53 is used for DNS mapping
2. The user adds `https://<API URL>/plugins.xml` as a QGIS plugin repository source (see the [README.md](https://github.com/linz/qgis-plugin-repository/blob/master/README.md#consuming-the-qgis-plugins) 
for details on configuring QGIS repository sources). QGIS then makes the request to the 
API for the XML document describing available plugins. 
3. The http request is via API gateway
4. & 5. Lambda handles the request and invokes a DynamoDB query for all current QGIS plugins stored 
in the repo. The result of this query is then used to generate an XML document that describes the 
plugins available for download.
6. The plugin xml document is returned to QGIS.


### Downloading QGIS plugins
Once QGIS has received the plugin repository XML document and displayed the available plugins
 to the QGIS user, the user can then download a plugin from the repository for use in QGIS. 

![image](/documentation/download_plugin.png)
**Above:** User workflow: downloading a plugin from the repository


1. When a QGIS user selects one of the repositories plugins for download, QGIS uses the 
xml documents `download_url` parameter to make a request to S3 for the resource.
2. S3 responds to QGIS with the plugin file that QGIS downloads and adds to the users QGIS 
profile. 

