#!/usr/bin/env python3

#
# Cleanup old development builds from DigitalOcean Spaces:
# - Keep the latest 5 versions of each channel
#
# Version format: 8.7.2-dev.<timestamp>.<hash> or 8.7.2-branch.<timestamp>.<hash>

import os
import boto3
from semver import Version as VersionInfo

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
    try:
        version_parsed = VersionInfo.parse(file_name)
    except ValueError:
        print(f'Skipping {file_name} - not a valid semver version.')
        continue
    
    # Check if it's a development build (has prerelease segment)
    if version_parsed.prerelease is None:
        print(f'Skipping {file_name} as it is not a development build.')
        continue
    
    # Extract timestamp from prerelease segment: "dev.<timestamp>.<hash>" or "branch.<timestamp>.<hash>"
    prerelease_parts = version_parsed.prerelease.split('.')
    if len(prerelease_parts) < 3:
        print(f'Skipping {file_name} - prerelease segment does not contain timestamp.')
        continue
    
    timestamp = prerelease_parts[1]  # middle part is the timestamp
    parsed_files.append({
        'timestamp': timestamp,
        'file': file,
        'version': file_name
    })

# Keep only the latest 5 dev builds, sorted by timestamp (descending)
to_delete = sorted(parsed_files, key=lambda k: k['timestamp'], reverse=True)[min_versions:]
for d in to_delete:
    print(f"Deleting {d['version']} ...")
    objects_to_delete = s3_client.list_objects(Bucket=bucket_name, Prefix=d['file'])
    delete_keys = {'Objects': [{'Key': k['Key']} for k in objects_to_delete.get('Contents', [])]}
    s3_client.delete_objects(Bucket=bucket_name, Delete=delete_keys)

