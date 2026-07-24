#!/usr/bin/python3

#
# Copyright (C) 2024 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

"""
Reverse proxy helper functions

All the functions in this module are meant to be used by the reverse proxy api and migration script.
Be careful when using them in other contexts.
"""

import ipaddress
import os
import subprocess

from euci import EUci

from nethsec import utils


def set_proxy_pass(e_uci, location, proxy_pass):
    """
    Set the proxy pass for the specified location.
    This function is a mere workaround for nginx to allow non-resolvable domains to be used as proxy_pass.

    Args:
      - e_uci: EUci object
      - location: nginx config location id
      - proxy_pass: string of the proxy pass to set
    """
    prefix = proxy_pass.split('://')[0]
    destination = proxy_pass.split('://')[1]
    address = destination.split('/')[0]
    if len(destination.split('/')) > 1:
        path = '/' + '/'.join(destination.split('/')[1:])
    else:
        path = ''

    try:
        ipaddress.ip_address(address)
        e_uci.set('nginx', location, 'proxy_pass', proxy_pass)
    except ValueError:
        e_uci.set('nginx', location, 'resolver', '127.0.0.1')
        e_uci.set('nginx', location, 'set', [f'$upstream {address}'])
        e_uci.set('nginx', location, 'proxy_pass', f'{prefix}://$upstream{path}')


def create_location(e_uci, uci_server, location, proxy_pass, domain='', allow=None):
    """
    Create a new location in the nginx config.

    Args:
      - e_uci: EUci object
      - uci_server: where the location is defined
      - location: path where the location will answer
      - proxy_pass: where the location will proxy to
      - domain: optional domain to set in the Host header
      - allow: array of allowed ip addresses

    Returns:
        location id of the created location
    """
    if allow is None:
        allow = []
    location_id = utils.get_random_id()
    e_uci.set('nginx', location_id, 'location')
    # defaults
    e_uci.set('nginx', location_id, 'proxy_http_version', '1.1')
    default_headers = [
        'X-Forwarded-For $proxy_add_x_forwarded_for',
        'X-Real-IP $remote_addr',
        'Upgrade $http_upgrade',
        'Connection "upgrade"'
    ]
    if domain:
        default_headers.append(f'Host {domain}')
    e_uci.set('nginx', location_id, 'proxy_set_header', default_headers)
    # set body limit to 1GB: same value of NethServer 7
    e_uci.set('nginx', location_id, 'client_max_body_size', '1024m')
    # setup location
    e_uci.set('nginx', location_id, 'uci_server', uci_server)
    e_uci.set('nginx', location_id, 'location', location)
    if len(allow) > 0:
        e_uci.set('nginx', location_id, 'allow', allow)
    set_proxy_pass(e_uci, location_id, proxy_pass)

    return location_id


def add_path(path, destination, description, allow):
    """
    Add a new location to the _lan server.

    Args:
      - path: path where the location will answer
      - destination: destination endpoint
      - description: description of the location
      - allow: array of allowed ip addresses
    """
    e_uci = EUci()
    location = create_location(e_uci, '_lan', path, destination, allow=allow)
    e_uci.set('nginx', location, 'uci_description', description)
    # defaults
    e_uci.set('nginx', location, 'proxy_ssl_verify', 'off')
    # add location to _lan server
    includes = list(e_uci.get('nginx', '_lan', 'include', list=True))
    if 'conf.d/_lan[.]proxy' not in includes:
        includes.append('conf.d/_lan[.]proxy')
        e_uci.set('nginx', '_lan', 'include', includes)

    e_uci.save('nginx')


def add_domain(domain, destination, certificate, description, allow):
    """
    Add a new server to the nginx config.

    Args:
      - domain: domain to answer to
      - destination: where to proxy the request to
      - certificate: certificate to be used, beware the certificate must be in the list of certificates
      - description: easy description of the server
      - allow: ip addresses allowed to access the server
    """
    e_uci = EUci()
    # create server instance
    server_name = utils.get_random_id()
    e_uci.set('nginx', server_name, 'server')
    # create default location
    create_location(e_uci, server_name, '/', destination, domain, allow)
    # defaults
    e_uci.set('nginx', server_name, 'proxy_ssl_verify', 'off')
    e_uci.set('nginx', server_name, 'ssl_session_timeout', '64m')
    e_uci.set('nginx', server_name, 'ssl_session_cache', 'shared:SSL:32k')
    e_uci.set('nginx', server_name, 'listen', ['443 ssl', '[::]:443 ssl'])
    e_uci.set('nginx', server_name, 'include', [f'conf.d/{server_name}.proxy'])
    e_uci.set('nginx', server_name, 'access_log', 'syslog:server=unix:/dev/log')
    e_uci.set('nginx', server_name, 'error_log', 'syslog:server=unix:/dev/log')
    # setup server
    valid_certificates = {name: certificate for (name, certificate) in certificate_list(e_uci).items()
                          if 'cert_path' in certificate}
    e_uci.set('nginx', server_name, 'server_name', domain)
    e_uci.set('nginx', server_name, 'ssl_certificate', valid_certificates[certificate]['cert_path'])
    e_uci.set('nginx', server_name, 'ssl_certificate_key', valid_certificates[certificate]['key_path'])
    e_uci.set('nginx', server_name, 'uci_description', description)

    e_uci.save('nginx')


def certificate_list(uci: EUci):
    """
    List all the certificates in the system.

    Args:
      - uci: euci object
    """
    default_certificate = uci.get('nginx', '_lan', 'ssl_certificate')

    servers = utils.get_all_by_type(uci, 'nginx', 'server')
    certificate_domain = {}
    for server in servers:
        if 'ssl_certificate' in servers[server]:
            if server not in certificate_domain:
                certificate_domain[servers[server]['ssl_certificate']] = []
            certificate_domain[servers[server]['ssl_certificate']].append(servers[server]['server_name'])

    certificates = {}

    # scan default certificates
    for entry in os.scandir('/etc/nginx/conf.d'):
        if entry.is_file() and entry.name.endswith('.crt') and os.path.isfile(entry.path[:-4] + '.key'):
            certificates[entry.name[:-4]] = {
                'type': 'self-signed',
                'cert_path': entry.path,
                'key_path': entry.path[:-4] + '.key',
                'default': default_certificate == entry.path,
            }

    # scan custom certificates
    if not os.path.isdir('/etc/nginx/custom_certs'):
        os.mkdir('/etc/nginx/custom_certs')
    for entry in os.scandir('/etc/nginx/custom_certs'):
        if entry.is_file() and entry.name.endswith('.crt') and os.path.isfile(entry.path[:-4] + '.key'):
            certificates[entry.name[:-4]] = {
                'type': 'custom',
                'cert_path': entry.path,
                'key_path': entry.path[:-4] + '.key',
                'default': default_certificate == entry.path,
            }

    # scan acme certificates
    requested_certificates = utils.get_all_by_type(uci, 'acme', 'cert')
    enabled_certificates = [certificate for certificate in requested_certificates
                            if requested_certificates[certificate]['enabled'] == '1']
    for certificate in enabled_certificates:
        domain = requested_certificates[certificate]['domains'][0]
        cert_path = f'/etc/ssl/acme/{domain}.fullchain.crt'
        key_path = f'/etc/ssl/acme/{domain}.key'
        if os.path.isfile(cert_path):
            certificates[certificate] = {
                'type': 'acme',
                'pending': False,
                'requested_domains': requested_certificates[certificate]['domains'],
                'cert_path': cert_path,
                'key_path': key_path,
                'default': default_certificate == cert_path
            }
        else:
            certificates[certificate] = {
                'type': 'acme',
                'pending': True,
                'requested_domains': requested_certificates[certificate]['domains'],
            }

    for certificate in certificates:
        if 'cert_path' in certificates[certificate]:
            # get certificate details
            details = subprocess.run(
                ['openssl', 'x509', '-noout', '-text', '-in', certificates[certificate]['cert_path']],
                check=True, capture_output=True, text=True)
            # get certificate expiration
            expiration = subprocess.run(['openssl', 'x509', '-noout', '-enddate', '-dateopt', 'iso_8601', '-in',
                                         certificates[certificate]['cert_path']],
                                        check=True, capture_output=True, text=True)
            # fetch subject common name
            subject = subprocess.run(['openssl', 'x509', '-noout', '-subject', '-nameopt', 'multiline', '-in',
                                      certificates[certificate]['cert_path']],
                                     check=True, capture_output=True, text=True)
            cn = ''
            for row in subject.stdout.split('\n'):
                if 'commonName' in row:
                    cn = row.split('=')[1].strip()
                    break

            # get certificate assigned domains
            servers = []
            if certificates[certificate]['cert_path'] in certificate_domain:
                servers = certificate_domain[certificates[certificate]['cert_path']]

            # store certificate details
            certificates[certificate]['details'] = details.stdout
            certificates[certificate]['expiration'] = expiration.stdout.split('=')[1].strip()
            certificates[certificate]['servers'] = servers
            certificates[certificate]['domain'] = cn

    return certificates
