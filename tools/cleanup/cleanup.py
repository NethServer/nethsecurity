#!/usr/bin/env python3

#
# Cleanup old development builds from DigitalOcean Spaces:
# - Keep all tagged releases
# - Keep at least 3 versions of each sub release
#

import os
import boto3
from semver import VersionInfo

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
min_versions = 5
response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=f'{prefix}/', Delimiter='/')

files = [item.get('Prefix') for item in response.get('CommonPrefixes')]
parsed_files = []
for file in files:
    file_name = file.lstrip(f'{prefix}/').rstrip('/')
    version_parsed = VersionInfo.parse(file_name)
    if version_parsed.build is None:
        print(f'Skipping {file_name} as it is not a development build.')
        continue
    build_split = version_parsed.build.split('.')
    parsed_files.append({
        'timestamp': build_split[1],
        'file': file
    })

# keep only the latest 5 dev builds
to_delete = sorted(parsed_files, key=lambda k: k['timestamp'], reverse=True)[min_versions:]
for d in to_delete:
    print(f"Deleting {d['file']} ...")
    objects_to_delete = s3_client.list_objects(Bucket=bucket_name, Prefix=d['file'])
    delete_keys = {'Objects': [{'Key': k['Key']} for k in objects_to_delete.get('Contents', [])]}
    s3_client.delete_objects(Bucket=bucket_name, Delete=delete_keys)
