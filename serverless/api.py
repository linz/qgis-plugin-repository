import os
import json
from flask import Flask, request
from werkzeug import secure_filename
import logging
import boto3
from botocore.exceptions import ClientError

# UPLOAD_ FOLDER = '/tmp/'
UPLOAD_FOLDER = '/home/splanzer/temp/test'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Repository
if os.environ.get('REPO_BUCKET_NAME') is not None:
    REPO_BUCKET_NAME = os.environ['REPO_BUCKET_NAME']
else:
    REPO_BUCKET_NAME = 'qgis-plugin-repository'

# local testing only


def format_response(success, http_code, reason='', data={}):
    res_body = {'success': success,
                'reason': reason,
                'data': data}
    response = app.response_class(response=json.dumps(res_body),
                                  status=http_code,
                                  mimetype='application/json')
    return response


def upload_file_to_s3(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then same as file_name
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False, e
    return True, response


@app.route('/list', methods=['GET'])
def list_all():

    f = request.files['file']
    f.save(secure_filename(f.filename))
    return 'file uploaded successfully'


@app.route('/upload', methods=['POST'])
def upload():
    if "file" not in request.files:
        return "No user_file key in request.files"

    file = request.files["file"]

    if file and os.path.splitext(file.filename)[-1] == '.zip':
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # upload the file
        success, response = upload_file_to_s3(filepath, REPO_BUCKET_NAME, filename)
        if success:
            # logging.info('File was uploaded')
            return format_response('true', 201)
        else:
            return format_response('false', 400, response)

    else:
        return format_response('false', 415, 'file must be of type .zip')


@app.route('/remove', methods=['DELETE'])
def remove():

    f = request.files['file']
    f.save(secure_filename(f.filename))
    return 'file uploaded successfully'


if __name__ == '__main__':
    app.run(debug=True)
