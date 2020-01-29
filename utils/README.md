
# new_plugin_record.sh
Before a plugin can be added to the repository, metadata records must be created in the plugin 
repository database. This must be done by a user that has admin access to the plugin repository.

The 'new_plugin_record.sh' should be used to add these new records to the database as below.

for example:
`./new_plugin_record.sh --table '<name of repository database table>' --plugin-id '<plugin_id>'`

where: 
```
--table or -t:         Is the table name where the plugin repo metadata is stored
--plugin-id or -p:     Is the plugin's plugin id. This must match the plugins root directory name. 
```

## Secret 
On completion of the successful execution of the `new_plugin_record.sh` script, the secret 
added to the database is returned to the user. This secret must be retained in a secure password
manager as this secret is required when executing all API commands that modify the plugin. 

for example 
```
$ ./new_plugin_record.sh -t <repo table name> -p <plugin id>
> secret=gLKyO/lDPkM91JiU2s3QgHZF4WvW27DK

```

### Environment Variables To Configure the AWS CLI
The `./new_plugin_record.sh` script requires the `AWS_PROFILE` and `AWS_DEFAULT_REGION` 
environment variables to be set. 

If these are not set or the defaults must be overwritten for script's execution, the below can 
be executed prior to running the script.
`export AWS_DEFAULT_REGION=ap-southeast-2`
`export AWS_PROFILE=<profile_name>`

for more on AWS environment variables see the [AWS documentation](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html)
 on this topic.