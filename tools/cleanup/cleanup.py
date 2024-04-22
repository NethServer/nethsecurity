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
    # convert from 0.0.1-beta1-3-g4c5b89a to 0.0.1-beta1.3
    # to correctly sort build part
    if version.count('-') > 1:
      parts = version.split('-')
      version = parts[0] + '-' + parts[1] + '.' + parts[2]
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
sorted_dev = sorted(owrt_sorted, key=lambda v: ns_version(v[13:]), reverse=True)
to_delete = []
keep = 0
for version in sorted_dev:
    sversion = ns_version(version[13:])
    # keep at least max_versions of each sub release like 8-23.05.2-ns.0.0.1-beta1-3-g4c5b89a
    if sversion.prerelease and '.' in sversion.prerelease:
        keep += 1
        if keep > max_versions:
            to_delete.append(version)

for d in to_delete:
    print(f"Deleting {d} ...")
    objects_to_delete = s3_client.list_objects(Bucket=bucket_name, Prefix=f"{prefix}/{d}/")
    delete_keys = {'Objects' : []}
    delete_keys['Objects'] = [{'Key' : k} for k in [obj['Key'] for obj in objects_to_delete.get('Contents', [])] ]
    s3_client.delete_objects(Bucket=bucket_name, Delete=delete_keys)

# Cleanup image targets from rolling repository
images = []
bins = []
manifests = []
builders = []
response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=f'{prefix}/', Delimiter='/')
for o in response.get('CommonPrefixes'):
    version = o.get('Prefix').removeprefix(f'{prefix}/').rstrip('/')
    if version.startswith('8-'):
        continue
    # match only elements where prefix is like 'dev/23.05.2/'
    if re.match(r'^(\d+\.\d+\.\d+)$', version):
        target_dir = f'{prefix}/{version}/targets/x86/64/'
        for i in s3_client.list_objects_v2(Bucket=bucket_name, Prefix=target_dir).get('Contents'):
            # calculate basename of key
            key = i['Key'].removeprefix(target_dir)
            if re.match(rf'^nethsecurity-8-.*\.gz$', key):
                images.append((i['Key'], i['LastModified']))
            elif re.match(rf'^nethsecurity-8-.*\.bin$', key):
                bins.append((i['Key'], i['LastModified']))
            elif re.match(rf'^nethsecurity-8-.*\.manifest$', key):
                manifests.append((i['Key'], i['LastModified']))
            elif re.match(rf'^nethsecurity-imagebuilder-8-.*\.tar\.xz$', key):
                builders.append((i['Key'], i['LastModified']))

# sort images by date, more recent first
images.sort(key=lambda x: x[1], reverse=True)
# keep only 2 latest images (rootfs + combined)
image_to_keep = images[:4]
for image in images:
    # delete image if not in image_to_keep
    if image not in image_to_keep:
        print(f"Deleting {image[0]} ...")
        s3_client.delete_object(Bucket=bucket_name, Key=image[0])

# sort bins by date, more recent first
bins.sort(key=lambda x: x[1], reverse=True)
# keep only 2 latest bins
bins_to_keep = bins[:2]
for bin in bins:
    # delete bin if not in bins_to_keep
    if bin not in bins_to_keep:
        print(f"Deleting {bin[0]} ...")
        s3_client.delete_object(Bucket=bucket_name, Key=bin[0])

# sort manifests by date, more recent first
manifests.sort(key=lambda x: x[1], reverse=True)
# keep only 2 latest manifests
manifests_to_keep = manifests[:2]
for manifest in manifests:
    # delete manifest if not in manifests_to_keep
    if manifest not in manifests_to_keep:
        print(f"Deleting {manifest[0]} ...")
        s3_client.delete_object(Bucket=bucket_name, Key=manifest[0])

# sort builders by date, more recent first
builders.sort(key=lambda x: x[1], reverse=True)
# keep only 2 latest builders
builders_to_keep = builders[:2]
for builder in builders:
    # delete builder if not in builders_to_keep
    if builder not in builders_to_keep:
        print(f"Deleting {builder[0]} ...")
        s3_client.delete_object(Bucket=bucket_name, Key=builder[0])
