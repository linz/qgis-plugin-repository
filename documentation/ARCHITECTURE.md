# Architecture
This document is to give a brief overview of the systems components and their interactions.
This is to help anyone wanting to understand the API's architecture and operation. 

\*Note: The [serverless.yml](/serverless.yml) deployment document is somewhat self-documenting
and is a good source to view/understand the API's architecture. 

## Overview
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

## Architecture by user workflow examples
The below are user workflows to further demonstrate the API architecture 

### POSTing a plugin to the repository

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

### Make plugin information available to QGIS

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


### Downloading QGIS plugins
Once QGIS has received the plugin repository XML document and displayed the available plugins
 to the QGIS user, the user can then download a plugin from the repository for use in QGIS. 

![image](/documentation/download_plugin.png)
**Above:** User workflow: downloading a plugin from the repository


1. When a QGIS user selects one of the repositories plugins for download, QGIS uses the 
xml documents `download_url` parameter to make a request to S3 for the resource.
2. S3 responds to QGIS with the plugin file that QGIS downloads and adds to the users QGIS 
profile. 
3. Cloud watch stores log and metric information about the operation.

