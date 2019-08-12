import boto3, botocore, logging, zipfile, re, os, configparser, io, datetime, json
import xml.etree.ElementTree as ET
from xml.dom import minidom

logger = logging.getLogger()
logger.setLevel(logging.INFO)

S3_RESOURCE_REPO = boto3.resource('s3')
s3_RESOURCE_STAGE = boto3.resource('s3')
S3_CLIENT = boto3.client('s3')

TEMP_FOLDER = '/tmp/'

# as per https://docs.qgis.org/3.4/en/docs/pyqgis_developer_cookbook
#            /plugins/plugins.html#plugin-metadata-table
REQUIRED_METADATA = [
                    'name',
                    'qgisMinimumVersion',
                    'description',
                    #'about', linz have not been using this
                    'version',
                    'author',
                    'email',
                    # 'repository', linz have not been using this
                     ]

def lambda_handler(event, context):
    '''
    Entry Method
    '''

    # Log data
    logger.info(event)
    record = event['Records'][0]
    event_s3_obj_key = record['s3']['object']['key']

    #version - either test, dev, prd (as per bucket folders)
    version, filename = os.path.split(event_s3_obj_key)
    event_type = record['eventName']

    # Resource reference to bucket objects. 
    logger.info(os.environ)

    # Repository
    if os.environ.get('REPO_BUCKET_NAME') is not None:
        repo_bucket_name = os.environ['REPO_BUCKET_NAME']
    else: 
        repo_bucket_name = 'qgis-plugin-repository'
    # Staging
    if os.environ.get('STAGING_BUCKET_NAME') is not None:
        staging_bucket_name = os.environ['STAGING_BUCKET_NAME']
    else: 
        staging_bucket_name = 'qgis-plugin-repository-staging'

    repo_bucket = S3_RESOURCE_REPO.Bucket(repo_bucket_name)
    staging_bucket = s3_RESOURCE_STAGE.Bucket(staging_bucket_name)    
    
    # What type of event was it. If a new plugin has been added,
    # validate it
    validated=True

    if event_type == 'ObjectRemoved:Delete':
        logger.info('Plugin deletion detected')

    if event_type == 'ObjectCreated:Put':
        logger.info('New plugin detected: {0}'.format(event_s3_obj_key))
        validated = validate(event_s3_obj_key, staging_bucket_name)

    logger.info('validated == {0}'.format(validated))
    if validated:
        # Sync the staging and plugin repository buckets
        sync(staging_bucket, repo_bucket, version)
        # Update the plugins.xml that discribles the repositories contents 
        update_xml(repo_bucket, version)

def remove_zip(file):
    '''
    Delete the downloaded zip file to free up mem
    '''

    if os.path.exists(file):
        os.remove(file)
    else:
        logger.info(file+": does not exist")

def download_pl_file(bucket, key, clean=True):
    '''
    Returns a zipfile obj
    '''

    download_dest = TEMP_FOLDER+os.path.basename(key)

    logger.info('Downloading from - Bucket: {0}, Key: {1} to: {2}'.format(bucket,
                                                                          key, 
                                                                          download_dest))

    S3_CLIENT.download_file(bucket, key, download_dest)
    plugin_zip = zipfile.ZipFile(download_dest)
    if clean: 
        remove_zip(download_dest)
    return plugin_zip

def get_metadata_path(plugin_zip):
    '''
    Returns a list of possible metadata.txt matches
    The regex applied to the zipfles namelist only matches 
    one dir deep - therefore it will either return an list with
    one item (path to metadata.txt) else an empty list. If its 
    is a empty list that is returned, the metadata.txt was not found
    '''

    plugin_files = plugin_zip.namelist()
    metadata_path = ([i for i in plugin_files if re.search(r'^\w*\/{1}metadata.txt', i) ])
    return metadata_path

def metadata_exists(metadata_path):
    '''
    Check the plugin has a metadata.txt file
    '''

    if len(metadata_path) == 0:
        logger.error('ERROR: metadata.txt not found')
        return False
    logger.info('validation passed: metadata.txt exists')
    return True

def metadata_fields_exist(plugin_zip, metadata_path):
    '''
    Check required metadata fields exist
    '''

    missing_fields = []
    logger.info('plugin_zip: {0}, metadata_path: {1}'.format(plugin_zip, metadata_path))
    plugn_metadata = metadata_contents(plugin_zip, metadata_path)
    for required in REQUIRED_METADATA:
        if not plugn_metadata.has_option('general', required):
            missing_fields.append(required)
    if missing_fields:
        logger.error('ERROR: The following is missing from the metadata.txt: {0}'.format(missing_fields))
        return False
    logger.info('validation passed: metadata.txt required fields present')
    return True

def validate(event_s3_obj_key, staging_bucket_name):
    '''
    Test the metadata.txt is present in the plugin zipfile
    and that the contents of the metadata.txt contains the
    required fields. 
    '''

    logger.info('validating s3 object key: '+event_s3_obj_key)
    plugin_zip = download_pl_file(staging_bucket_name, event_s3_obj_key)
    metadata_path = get_metadata_path(plugin_zip)
    
    # Check files exists
    if not metadata_exists(metadata_path):
        return False

    # Check contents
    if  not metadata_fields_exist(plugin_zip , metadata_path[0]):
        return False
    
    return True

def sync(staging_bucket, repo_bucket, version):
    '''
    Sync the staging bucket and qgis plugin repository bucket
    '''

    staging_keys = get_buckets_contents(staging_bucket, version)
    plugin_repo_keys = get_buckets_contents(repo_bucket, version)

    # Copy Plugins from staging to published repository 
    for obj_key in staging_keys:
        if obj_key not in plugin_repo_keys:
            copy_source = {'Bucket': staging_bucket.name,'Key': obj_key}
            logger.info('copying: {0}/{1} to {2}/{1}'.format(staging_bucket.name,obj_key, repo_bucket.name))
            S3_RESOURCE_REPO.meta.client.copy(copy_source, repo_bucket.name, obj_key)
    # remove plugins in repo that are no longer in staging
    for obj_key in plugin_repo_keys:
        ext = os.path.splitext(obj_key)[1]
        if obj_key not in staging_keys and ext != '.xsl':
            obj = S3_RESOURCE_REPO.Object(repo_bucket.name, obj_key)
            obj.delete()

def get_buckets_contents(bucket, version):
    '''
    Fetch the keys for a folder in the bucket
    '''
    keys = {}
    bucket_objs = S3_CLIENT.list_objects(Bucket=bucket.name, Prefix=version+'/', Delimiter='/')
    if 'Contents' in bucket_objs:
        keys = [d['Key'] for d in bucket_objs['Contents'] if d['Key'] != version+'/' ]

    logger.info('get_buckets_contents: '+str(keys))

    return keys

def metadata_contents(plugin_zip, metadata_path):
    '''
    Return metadata.txt contents that is stored in
    the plugin .zip file
    '''

    metadata = plugin_zip.open(metadata_path)
    metadata = str(metadata.read(), 'utf-8')
    config = configparser.ConfigParser()
    config.readfp(io.StringIO(metadata))

    return config


def extract_metadata(bucket, key, version):
    '''
    Read the metadata.txt file and return a dictionary mapping
    '''

    pugin_metadata = {}
    plugin_zip = download_pl_file(bucket.name, key)
    metadata_path = get_metadata_path(plugin_zip)
    plugin_metadata = metadata_contents(plugin_zip, metadata_path[0])

    plugin_name = plugin_metadata['general']['name']+'-'+plugin_metadata['general']['version']
    location = S3_CLIENT.get_bucket_location(Bucket=bucket.name)['LocationConstraint']
    location = location+'/'+version

    last_modified = S3_RESOURCE_REPO.Object(bucket_name=bucket.name, key=key).last_modified # THIS IS VERY SLOW!
    last_modified = last_modified.strftime("%Y-%m-%d")


    return { 
            plugin_name : {
                'name': plugin_metadata['general']['name'],
                'description': plugin_metadata['general']['description'],
                #'about' : plugin_metadata['general']['about'],
                'version': plugin_metadata['general']['version'],
                'qgis_minimum_version': plugin_metadata['general']['qgisMinimumVersion'],
                'homepage': plugin_metadata['general']['homepage'],
                #'email': plugin_metadata['general']['email'],
                #'repository': plugin_metadata['general']['repository'],
                'author_name': plugin_metadata['general']['author'],
                'download_url':  'https://{0}.s3-{1}.amazonaws.com/{2}'.format(bucket.name, location.strip('/'+version), key),
                'file_name': key,
                'create_date': last_modified,
                'update_date': last_modified,
                #'uploaded_by': plugin_metadata['general']['author']
                }
            }

def create_xml(repo_bucket, pl_metadata, version):
    '''
    Generate the xml document describing all 
    plugins in the plugin repository
    '''
    
    location = S3_CLIENT.get_bucket_location(Bucket=repo_bucket.name)['LocationConstraint']
    xsl_url = 'https://{0}.s3-{1}.amazonaws.com/{2}'.format(repo_bucket.name, location.strip('/'+version), version+'/plugins.xsl')
    root = ET.Element('plugins')
    
    for plugin, metadata in pl_metadata.items():
        current_group = ET.SubElement(root, 'pyqgis_plugin', {'name':metadata['name'], 'version':metadata['version']})
        for k,v in metadata.items():
            if k not in ('name'):
                new=ET.Element(k)
                new.text=v
                current_group.append(new)

    # HACK: xml.etree does not support processing instructions
    # xmxl is not a stanadard Lambda lib. so...
    xml = ET.tostring(root)
    dom = minidom.parseString(xml)
    pi = dom.createProcessingInstruction('xml-stylesheet',
                                     'type="text/xsl" href="{0}"'.format(xsl_url))
    root = dom.firstChild
    dom.insertBefore(pi, root)
    return dom

    
def update_xml(repo_bucket, version):
    '''
    Write the plugin repository xml document
    '''

    pl_metadata={}
    repo_plugin_key = get_buckets_contents(repo_bucket, version)
    for key in repo_plugin_key:
        if  os.path.splitext(key)[1] == '.zip':
            pl_metadata.update(extract_metadata(repo_bucket, key, version))
    logger.info('extracted metadata: '+json.dumps(pl_metadata))

    
    # Build the plugins.xml
    xml = create_xml(repo_bucket, pl_metadata, version)
    # write plugin.xml
    S3_RESOURCE_REPO.Bucket(repo_bucket.name).put_object(Key=version+'/plugins.xml',
                                                         Body=xml.toprettyxml(indent="  ", 
                                                                              newl="\n", 
                                                                              encoding='UTF-8'),
                                                         ACL='public-read')
