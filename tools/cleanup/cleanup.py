#!/usr/bin/env python3

#
# Cleanup old development builds from DigitalOcean Spaces:
# - Keep all tagged releases
# - Keep at least 3 versions of each sub release
#

import os
import re
import boto3

region = "ams3"
bucket_name = "nethsecurity"
s3_client = boto3.session.Session().client(
    's3',
    region_name=region,
    endpoint_url='https://' + region + '.digitaloceanspaces.com',
    aws_access_key_id=os.environ['DO_SPACE_ACCESS_KEY'],
    aws_secret_access_key=os.environ['DO_SPACE_SECRET_KEY']
)
prefix = 'dev'
max_versions = 5
response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=f'{prefix}/', Delimiter='/')

files = [item.get('Prefix') for item in response.get('CommonPrefixes')]
parsed_files = []
for file in files:
    matched = re.match(
        '^' + prefix + '/(?P<version>[^/-]+(?:-[^/-]+)*?)-(?P<commit>[0-9a-f]+)-(?P<timestamp>\\d{14})/$', file)
    if matched is None:
        continue
    parsed_files.append({
        'version': matched.group('version'),
        'commit': matched.group('commit'),
        'timestamp': matched.group('timestamp'),
        'file': file
    })

# keep only the latest 5 dev builds
to_delete = sorted(parsed_files, key=lambda k: k['timestamp'], reverse=True)[:max_versions]
for d in to_delete:
    print(f"Deleting {d['file']} ...")
    objects_to_delete = s3_client.list_objects(Bucket=bucket_name, Prefix=d['file'])
    delete_keys = {'Objects': [{'Key': k['Key']} for k in objects_to_delete.get('Contents', [])]}
    s3_client.delete_objects(Bucket=bucket_name, Delete=delete_keys)
