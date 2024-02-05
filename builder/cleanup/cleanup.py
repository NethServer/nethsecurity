#!/usr/bin/env python3

#
# Cleanup old development builds from DigitalOcean Spaces:
# - Keep all tagged releases
# - Keep at least 3 versions of each sub release
#

import os
import re
import boto3
import semver

def owrt_version(release):
    match = re.match(r"^([\d.]+)(?:-(.+))?$", release)
    if match:
        version = match.group(1).split(".")
        return (int(version[0]), int(version[1]) if len(version) > 1 else 0,
                    int(version[2]) if len(version) > 2 else 0)
    else:
        raise ValueError(f"Invalid OpenWrt release format: {release}")

def ns_version(version):
    try:
        return semver.VersionInfo.parse(version)
    except ValueError:
        return semver.VersionInfo.parse('0.0.0')

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
unordered_versions = []
max_versions = 3
response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=f'{prefix}/', Delimiter='/')
for o in response.get('CommonPrefixes'):
    entry = entry = o.get('Prefix').removeprefix(f'{prefix}/').rstrip('/')
    if entry.startswith('8-'):
        unordered_versions.append(entry) 
# Sort by OpenWrt release
owrt_sorted = sorted(unordered_versions, key=lambda x: owrt_version(x))
# Sort by NethSecurity release
sorted_dev = sorted(owrt_sorted, key=lambda v: ns_version(v))
to_delete = []
for version in sorted_dev:
    sversion = ns_version(version[13:])
    # keep at least max_versions of each sub release like 8-23.05.2-ns.0.0.1-beta1-3-g4c5b89a
    if '-' in sversion.prerelease and len(to_delete) < max_versions:
        to_delete.append(version)

for d in to_delete:
    print(f"Deleting {d} ...")
    objects_to_delete = s3_client.list_objects(Bucket=bucket_name, Prefix=f"{prefix}/{d}/")
    delete_keys = {'Objects' : []}
    delete_keys['Objects'] = [{'Key' : k} for k in [obj['Key'] for obj in objects_to_delete.get('Contents', [])] ]
    #s3_client.delete_objects(Bucket=bucket_name, Delete=delete_keys)
