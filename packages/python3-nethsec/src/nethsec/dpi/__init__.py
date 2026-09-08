#!/usr/bin/python3

#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

"""
Library that handles the DPI rules.
"""

import ipaddress
import json
import subprocess
import syslog

import math
from euci import EUci

from nethsec import objects, utils
from nethsec.utils import ValidationError


def __load_applications() -> dict[int, str]:
    """
    Reads the applications from the netify-apps.conf file.

    Returns:
        dict of applications, each dict contains the property "id" and "name"
    """
    applications = dict[int, str]()
    with open('/etc/netifyd/netify-apps.conf', 'r') as file:
        for line in file.readlines():
            if line.startswith('app'):
                line_split = line.strip().removesuffix('\n').removeprefix('app:').split(":")
                applications[int(line_split[0])] = line_split[1]
    return applications


def load_applications() -> dict[int, str]:
    """
    Reads the applications loaded in memory by the engine, using the netifyd --dump-apps command.

    Returns:
        dict of applications, the key is the application id and the value is the application name
    """
    result = subprocess.run(['netifyd', '--dump-apps'], check=True, capture_output=True)
    applications = dict[int, str]()
    for line in result.stdout.decode().splitlines():
        # lines can be empty
        if len(line.strip()) < 1:
            continue
        line_split = line.split(":", 1)
        if len(line_split) < 2:
            continue
        try:
            application_id = int(line_split[0].strip())
        except ValueError:
            # skip lines not in the "id: name" format, like headers
            continue
        applications[application_id] = line_split[1].strip()

    return applications


def __load_application_categories() -> dict[int, dict[str]]:
    """
    Reads the application categories from the netify-categories.json file.

    Returns:
        dict of application categories, each dict contains the property "id" and "name"
    """
    categories = dict[int, dict[str]]()
    with open('/etc/netifyd/netify-categories.json', 'r') as file:
        categories_file = json.load(file)

        categories_names = dict[int, str]()
        if 'application_tag_index' not in categories_file:
            for category_name, applications in categories_file['application_index'].items():
                for application in applications:
                    categories[application] = {
                        'name': category_name
                    }
        else:
            categories_application_tag_index: dict[str, int] = categories_file['application_tag_index']
            for category_name, category_id in categories_application_tag_index.items():
                categories_names[category_id] = category_name

            categories_application_index: list[int, list[int]] = categories_file['application_index']
            for category_id, applications_id in categories_application_index:
                for application_id in applications_id:
                    categories[application_id] = {
                        'name': categories_names[category_id]
                    }

    return categories


def load_protocols() -> dict[int, str]:
    """
    Reads the protocols from the netifyd --dump-protos command.

    Returns:
        dict of protocols, each dict contains the property "id" and "name"
    """
    result = subprocess.run(['netifyd', '--dump-protos'], check=True, capture_output=True)
    protocols = dict[int, str]()
    for line in result.stdout.decode().splitlines():
        # lines can be empty
        if len(line) < 1:
            continue
        line_split = line.split(":")
        protocols[int(line_split[0].strip())] = line_split[1].strip()

    return protocols


def __load_protocol_categories() -> dict[int, dict[str]]:
    """
    Reads the protocol categories from the netify-categories.json file.

    Returns:
        dict of protocol categories, each dict contains the property "id" and "name"
    """
    categories = dict[int, dict[str]]()
    with open('/etc/netifyd/netify-categories.json', 'r') as file:
        categories_file = json.load(file)

        categories_names = dict[int, str]()

        if 'protocol_tag_index' not in categories_file:
            for category_name, protocols in categories_file['protocol_index'].items():
                for protocol in protocols:
                    categories[protocol] = {
                        'name': category_name
                    }
        else:
            categories_protocol_tag_index: dict[str, int] = categories_file['protocol_tag_index']
            for category_name, category_id in categories_protocol_tag_index.items():
                categories_names[category_id] = category_name

            categories_protocol_index: list[int, list[int]] = categories_file['protocol_index']
            for category_id, protocol_ids in categories_protocol_index:
                for protocol_id in protocol_ids:
                    categories[protocol_id] = {
                        'name': categories_names[category_id]
                    }

    return categories


def __load_blocklist() -> list[dict[str]]:
    """
    Format the applications and protocols into a list of dicts.

    Returns:
        list of dicts, each dict contains the property "id", "name", "type" and "category"
    """
    result = list[dict[str]]()
    try:
        applications = load_applications()
    except Exception:
        # the engine can't be queried, fall back to the signatures file
        applications = __load_applications()
    application_categories = __load_application_categories()

    for application_id, application_name in applications.items():
        result_application = {
            'id': application_id,
            'name': application_name,
            'type': 'application'
        }
        if application_id in application_categories:
            result_application['category'] = application_categories[application_id]
        result.append(result_application)

    protocols = load_protocols()
    protocol_categories = __load_protocol_categories()

    for protocol_id, protocol_name in protocols.items():
        result_protocol = {
            'id': protocol_id,
            'name': protocol_name,
            'type': 'protocol'
        }
        if protocol_id in protocol_categories:
            result_protocol['category'] = protocol_categories[protocol_id]
        result.append(result_protocol)

    return result


def list_applications(search: str = None, limit: int = None, page: int = 1) -> dict:
    """
    List applications available for filtering.

    Args:
      - search: search string
      - limit: limit the number of results
      - page: page number

    Returns:
        list of dicts, each dict contains the property "code" and "name"
    """
    result = __load_blocklist()

    if search is not None:
        # lower string so we can do a case-insensitive search
        search = search.lower()
        # I'm aware it's far from a readable code, but list comprehension is the fastest way to filter.
        result = [item for item in result if
                  item.get('name', '').lower().find(search) != -1 or
                  item.get('category', {}).get('name', '').lower().find(search) != -1]

    total = len(result)

    if limit is not None:
        result = result[limit * (page - 1):limit * page]
        last_page = math.ceil(total / limit)
    else:
        last_page = 1

    return {
        'data': result,
        'meta': {
            'last_page': last_page,
            'total': total,
        }
    }


def __apply(e_uci: EUci):
    """
    Commit the dpi config and reload the dpi service.

    Used by the schema migration only: it runs at boot with nobody around to confirm the pending uci
    changes, so it must take effect on its own. Rule and appgroup CRUD go through the normal pending
    uci changes instead, applied later by ns.commit like every other section.
    """
    e_uci.commit('dpi')
    subprocess.run(["/etc/init.d/dpi", "reload"], check=True)


def __toggle_engine(e_uci: EUci):
    count_enabled = 0
    for section in e_uci.get_all('dpi'):
        if e_uci.get('dpi', section, default="") == "rule" and e_uci.get('dpi', section, 'enabled', default="0") == "1":
            count_enabled = count_enabled + 1

    if count_enabled > 0:
        e_uci.set('dpi', 'config', 'enabled', '1')
    else:
        e_uci.set('dpi', 'config', 'enabled', '0')


# Application groups: a NethSecurity abstraction, the netifyd plugin has no group primitive.
# A group is a named set of match members, expanded into an inline expression at generation time.

NETIFYD_DATA_DIR = '/etc/netifyd'

# UCI list name of every member kind, mapped to the API parameter it is fed by
APPGROUP_MEMBERS = {
    'app': 'applications',
    'app_category': 'application_categories',
    'proto': 'protocols',
    'proto_category': 'protocol_categories'
}

# validation error message of every member kind
__APPGROUP_MEMBER_ERRORS = {
    'app': 'invalid_application',
    'app_category': 'invalid_application_category',
    'proto': 'invalid_protocol',
    'proto_category': 'invalid_protocol_category'
}

# characters that would let a member value escape its quoted literal, or terminate the expression
__APPGROUP_FORBIDDEN_CHARS = '\'"\\;()\n\r\t'

APPGROUP_NAME_MAX_LENGTH = 64


def load_categories() -> dict[str, dict[int, str]]:
    """
    Reads the categories loaded in memory by the engine, using the netifyd --dump-categories command.

    The dump reports one category per line, as "<id>: <type>: <tag>".

    Returns:
        dict of categories indexed by type, e.g. `{'application': {1: 'adult'}, 'protocol': {2: 'database'}}`.
        Ids are the ones the agent uses internally: they do not match the ids of the downloaded catalogs,
        so categories must always be crossed by tag.
    """
    result = subprocess.run(['netifyd', '--dump-categories'], check=True, capture_output=True)
    categories = dict[str, dict[int, str]]()
    for line in result.stdout.decode().splitlines():
        line_split = line.split(":", 2)
        if len(line_split) < 3:
            continue
        try:
            category_id = int(line_split[0].strip())
        except ValueError:
            # skip lines not in the "id: type: tag" format, like headers
            continue
        category_type = line_split[1].strip()
        categories.setdefault(category_type, dict[int, str]())[category_id] = line_split[2].strip()

    return categories


def __load_catalog_tags(filename: str) -> set[str]:
    """
    Reads the tags of a downloaded catalog, one of the `/etc/netifyd/netify-*.json` files.

    Args:
      - filename: name of the catalog file inside the netifyd data directory

    Returns:
        set of the tags the catalog lists
    """
    with open(f'{NETIFYD_DATA_DIR}/{filename}', 'r') as file:
        return {entry['tag'] for entry in json.load(file) if entry.get('tag')}


def __appgroup_vocabulary(kind: str) -> set[str] | None:
    """
    Values a member of the given kind can take, lowercased.

    The engine is the authority: only what it has loaded can be matched. The downloaded catalog backs
    applications up, so that a group stays editable on a machine that lost its premium signatures.

    Args:
      - kind: one of the keys of `APPGROUP_MEMBERS`

    Returns:
        set of accepted values, or None when no source is available and the values cannot be checked
    """
    vocabulary = set[str]()
    try:
        if kind == 'app':
            vocabulary |= {value.lower() for value in load_applications().values()}
        elif kind == 'proto':
            vocabulary |= {value.lower() for value in load_protocols().values()}
        else:
            category_type = 'application' if kind == 'app_category' else 'protocol'
            vocabulary |= {value.lower() for value in load_categories().get(category_type, {}).values()}
    except Exception:
        # the engine can't be queried, fall back to the downloaded catalogs below
        pass

    if kind != 'proto':
        # protocol names come from the agent itself and have no counterpart in the catalog, where the
        # same protocol is listed under a different tag: the catalog would accept unmatchable values
        catalogs = {
            'app': 'netify-application-catalog.json',
            'app_category': 'netify-application-categories.json',
            'proto_category': 'netify-protocol-categories.json'
        }
        try:
            vocabulary |= {value.lower() for value in __load_catalog_tags(catalogs[kind])}
        except Exception:
            pass

    # an unknown value never matches, so a missing vocabulary is a reason to skip the check, not to refuse
    return vocabulary if vocabulary else None


def __validate_appgroup_members(kind: str, values: list[str]) -> list[str]:
    """
    Validate the members of one kind, stripping and deduplicating them.

    Args:
      - kind: one of the keys of `APPGROUP_MEMBERS`
      - values: list of member values

    Returns:
        the sanitized list of members

    Raises:
      - ValidationError: if a member is empty, holds a character that would break the expression, or is
        unknown to both the engine and the catalog
    """
    parameter = APPGROUP_MEMBERS[kind]
    message = __APPGROUP_MEMBER_ERRORS[kind]
    if not values:
        return []

    vocabulary = __appgroup_vocabulary(kind)
    members = []
    seen = set[str]()
    for value in values:
        if not isinstance(value, str):
            raise ValidationError(parameter, message, value)
        member = value.strip()
        if not member or any(char in member for char in __APPGROUP_FORBIDDEN_CHARS):
            raise ValidationError(parameter, message, value)
        if vocabulary is not None and member.lower() not in vocabulary:
            raise ValidationError(parameter, message, member)
        if member.lower() not in seen:
            seen.add(member.lower())
            members.append(member)

    return members


def __validate_appgroup(e_uci: EUci, name: str, applications: list[str], application_categories: list[str],
                        protocols: list[str], protocol_categories: list[str],
                        config_name: str = None) -> tuple[str, dict[str, list[str]]]:
    """
    Validate a group before it is stored.

    Args:
      - e_uci: euci instance
      - name: name of the group
      - applications: list of application names
      - application_categories: list of application category tags
      - protocols: list of protocol names
      - protocol_categories: list of protocol category tags
      - config_name: config name of the group being edited, excluded from the name uniqueness check

    Returns:
        a tuple with the sanitized name and the sanitized members, indexed by UCI list name

    Raises:
      - ValidationError: if the name or any member is invalid, or if the group has no members
    """
    if not isinstance(name, str) or not name.strip():
        raise ValidationError('name', 'name_required', name)
    name = name.strip()
    if len(name) > APPGROUP_NAME_MAX_LENGTH:
        raise ValidationError('name', 'name_too_long', name)
    for section, group in (utils.get_all_by_type(e_uci, 'dpi', 'appgroup') or {}).items():
        if section != config_name and group.get('ns_name', '').strip().lower() == name.lower():
            raise ValidationError('name', 'name_already_exists', name)

    members = {
        'app': __validate_appgroup_members('app', applications),
        'app_category': __validate_appgroup_members('app_category', application_categories),
        'proto': __validate_appgroup_members('proto', protocols),
        'proto_category': __validate_appgroup_members('proto_category', protocol_categories)
    }
    if not any(members.values()):
        # an empty group would expand to an empty criteria, which takes the agent down
        raise ValidationError('members', 'appgroup_is_empty', '')

    return name, members


def __save_appgroup_data(e_uci: EUci, config_name: str, name: str, members: dict[str, list[str]]):
    e_uci.set('dpi', config_name, 'ns_name', name)
    for uci_list, values in members.items():
        if values:
            e_uci.set('dpi', config_name, uci_list, values)
        else:
            # an emptied list must be removed, not stored empty
            e_uci.delete('dpi', config_name, uci_list)


def is_used_appgroup(e_uci: EUci, config_name: str) -> tuple[bool, list[str]]:
    """
    Check if an application group is referenced by a rule.

    Args:
      - e_uci: euci instance
      - config_name: config name of the group

    Returns:
        A tuple with:
        - True if the group is referenced by at least one rule, False otherwise
        - a list of the rule sections referencing it
    """
    matches = []
    for section, rule in (utils.get_all_by_type(e_uci, 'dpi', 'rule') or {}).items():
        if config_name in rule.get('appgroup', []):
            matches.append(f'dpi/{section}')
    return len(matches) > 0, matches


def list_appgroups(e_uci: EUci, search: str = None, limit: int = None, page: int = 1,
                   used_info: bool = True) -> dict:
    """
    List the application groups, ordered by name.

    Args:
      - e_uci: euci instance
      - search: search string, matched against the group name
      - limit: limit the number of results, all of them if not given
      - page: page number
      - used_info: include the used and matches info

    Returns:
        dict with the "data" list and the "meta" pagination info
    """
    groups = []
    for section, group in (utils.get_all_by_type(e_uci, 'dpi', 'appgroup') or {}).items():
        data_group = {'id': section, 'name': group.get('ns_name', '')}
        for uci_list, parameter in APPGROUP_MEMBERS.items():
            data_group[parameter] = list(group.get(uci_list, []))
        groups.append(data_group)

    # pagination needs a deterministic order, the UCI one is not
    groups.sort(key=lambda group: group['name'].lower())

    if search:
        search = search.lower()
        groups = [group for group in groups if search in group['name'].lower()]

    total = len(groups)

    if limit is not None:
        groups = groups[limit * (page - 1):limit * page]
        last_page = math.ceil(total / limit)
    else:
        last_page = 1

    if used_info:
        # only for the returned page: every check walks the rules
        for group in groups:
            group['used'], group['matches'] = is_used_appgroup(e_uci, group['id'])

    return {
        'data': groups,
        'meta': {
            'last_page': last_page,
            'total': total,
        }
    }


def add_appgroup(e_uci: EUci, name: str, applications: list[str] = None,
                 application_categories: list[str] = None, protocols: list[str] = None,
                 protocol_categories: list[str] = None) -> str:
    """
    Store a new application group.

    Args:
      - e_uci: euci instance
      - name: name of the group
      - applications: list of application names, as the engine reports them
      - application_categories: list of application category tags
      - protocols: list of protocol names, as the engine reports them
      - protocol_categories: list of protocol category tags

    Returns:
        config name of the group created

    Raises:
      - ValidationError: if the name or any member is invalid, or if the group has no members
    """
    name, members = __validate_appgroup(e_uci, name, applications, application_categories, protocols,
                                        protocol_categories)
    config_name = utils.get_random_id()
    e_uci.set('dpi', config_name, 'appgroup')
    __save_appgroup_data(e_uci, config_name, name, members)
    e_uci.save('dpi')
    return config_name


def edit_appgroup(e_uci: EUci, config_name: str, name: str, applications: list[str] = None,
                  application_categories: list[str] = None, protocols: list[str] = None,
                  protocol_categories: list[str] = None) -> str:
    """
    Edit an application group.

    Args:
      - e_uci: euci instance
      - config_name: config name of the group to edit
      - name: name of the group
      - applications: list of application names, as the engine reports them
      - application_categories: list of application category tags
      - protocols: list of protocol names, as the engine reports them
      - protocol_categories: list of protocol category tags

    Returns:
        config name of the group edited

    Raises:
      - ValidationError: if the group does not exist, or if the name or any member is invalid
    """
    if e_uci.get('dpi', config_name, default=None) != 'appgroup':
        raise ValidationError('id', 'appgroup_does_not_exists', config_name)

    name, members = __validate_appgroup(e_uci, name, applications, application_categories, protocols,
                                        protocol_categories, config_name)
    __save_appgroup_data(e_uci, config_name, name, members)
    e_uci.save('dpi')
    return config_name


def delete_appgroup(e_uci: EUci, config_name: str) -> str:
    """
    Delete an application group.

    Args:
      - e_uci: euci instance
      - config_name: config name of the group to delete

    Returns:
        config name of the group deleted

    Raises:
      - ValidationError: if the group does not exist or is referenced by a rule
    """
    if e_uci.get('dpi', config_name, default=None) != 'appgroup':
        raise ValidationError('id', 'appgroup_does_not_exists', config_name)

    used, matches = is_used_appgroup(e_uci, config_name)
    if used:
        raise ValidationError('id', 'appgroup_is_used', matches)

    e_uci.delete('dpi', config_name)
    e_uci.save('dpi')
    return config_name


def expand_appgroups(e_uci: EUci, config_names: list[str]) -> str:
    """
    Expand application groups into the parenthesised OR block of an action criteria.

    Members of several groups are merged and deduplicated; categories are never expanded into their
    applications, so a category keeps following the signature updates. Groups that do not exist are
    skipped.

    Args:
      - e_uci: euci instance
      - config_names: config names of the groups to expand

    Returns:
        the expression, e.g. `(app == 'netify.amazon' || proto == 'http/connect')`, or an empty string
        if the groups hold no member
    """
    terms = []
    seen = set[str]()
    for uci_list in APPGROUP_MEMBERS:
        for config_name in config_names:
            if e_uci.get('dpi', config_name, default=None) != 'appgroup':
                continue
            for value in e_uci.get('dpi', config_name, uci_list, list=True, default=[]):
                # protocol and category names are matched lowercased, application tags already are
                value = value if uci_list == 'app' else value.lower()
                term = f"{uci_list} == '{value}'"
                if term not in seen:
                    seen.add(term)
                    terms.append(term)

    if not terms:
        return ''
    return f"({' || '.join(terms)})"


# Rules: ordered by priority, first match wins. A rule matches application groups only, optionally
# narrowed to a source; what it does is decided by its action.

# 'allow' attaches a label no nft rule matches: it exists so a rule can win the first-match race and
# shield its traffic from the block rules below it
DPI_RULE_ACTIONS = ('block', 'allow')

DPI_RULE_NAME_MAX_LENGTH = 64

DPI_RULE_POSITIONS = ('top', 'bottom')


def __sorted_rules(e_uci: EUci) -> list[tuple[str, dict]]:
    """
    Rule sections in priority order. Rules with no priority, i.e. written by hand, go last keeping
    their config order.
    """
    def sort_key(item: tuple[str, dict]):
        try:
            return 0, int(item[1].get('priority'))
        except (TypeError, ValueError):
            return 1, 0

    return sorted((utils.get_all_by_type(e_uci, 'dpi', 'rule') or {}).items(), key=sort_key)


def __renumber_rules(e_uci: EUci, order: list[str] = None):
    """
    Give every rule a dense priority, starting at 1. The generator keeps 0 for its own action, so no
    user rule can be evaluated before it.
    """
    if order is None:
        order = [section for section, _ in __sorted_rules(e_uci)]
    for priority, section in enumerate(order, start=1):
        e_uci.set('dpi', section, 'priority', priority)


def __is_rule(e_uci: EUci, config_name: str) -> bool:
    return e_uci.get('dpi', config_name, default=None) == 'rule'


def __validate_rule_name(name: str) -> str:
    if not isinstance(name, str) or not name.strip():
        raise ValidationError('name', 'name_required', name)
    name = name.strip()
    if len(name) > DPI_RULE_NAME_MAX_LENGTH:
        raise ValidationError('name', 'name_too_long', name)
    return name


def __validate_source(values: list[str]) -> list[str]:
    """
    Validate the source of a rule: addresses, networks and ranges, IPv4 and IPv6 alike. An empty
    source means the rule matches every host.
    """
    sources = []
    for value in values or []:
        if not isinstance(value, str) or not value.strip():
            raise ValidationError('source', 'invalid_source', value)
        source = value.strip()
        try:
            if '-' in source:
                first, last = (ipaddress.ip_address(part.strip()) for part in source.split('-', 1))
                if first.version != last.version or first > last:
                    raise ValueError(source)
            else:
                ipaddress.ip_network(source, strict=False)
        except ValueError:
            raise ValidationError('source', 'invalid_source', value)
        if source not in sources:
            sources.append(source)
    return sources


def __validate_appgroups(e_uci: EUci, config_names: list[str], require_appgroup: bool = True) -> list[str]:
    """
    Validate the groups a rule matches. At least one is required by default: a rule with a source and
    no group would be an IP-level rule, which the firewall does better, and a rule with neither would
    expand to an empty criteria.

    `require_appgroup=False` lifts that requirement for a rule migrated from a global exemption: it is
    a source-only Allow rule by design, a shape the drawer cannot produce and never will.
    """
    appgroups = []
    for config_name in config_names or []:
        if not isinstance(config_name, str) or e_uci.get('dpi', config_name, default=None) != 'appgroup':
            raise ValidationError('appgroups', 'appgroup_does_not_exists', config_name)
        if config_name not in appgroups:
            appgroups.append(config_name)
    if require_appgroup and not appgroups:
        raise ValidationError('appgroups', 'appgroups_required', appgroups)
    return appgroups


def expand_source(values: list[str]) -> list[str]:
    """
    Expand the source of a rule into values a criteria can match: ranges become CIDR blocks, addresses
    and networks are left as they are.

    Args:
      - values: source entries of the rule

    Returns:
        list of addresses and CIDR blocks
    """
    expanded = []
    for value in values:
        if '-' in value:
            first, last = (ipaddress.ip_address(part.strip()) for part in value.split('-', 1))
            expanded.extend(str(network) for network in ipaddress.summarize_address_range(first, last))
        else:
            expanded.append(value)
    return expanded


def build_rule_criteria(e_uci: EUci, rule: dict, require_appgroup: bool = True) -> str:
    """
    Build the criteria of a managed rule: the source, when set, ANDed with the union of its groups.

    Args:
      - e_uci: euci instance
      - rule: the rule section, as returned by `uci.get_all`
      - require_appgroup: when False, a rule with a source and no group emits a source-only criteria
        instead of being treated as matching nothing. Used for a rule migrated from a global exemption,
        the one shape of source-only Allow rule the drawer cannot produce and never will.

    Returns:
        the semicolon-terminated expression, or an empty string when the rule matches nothing and must
        not be emitted
    """
    match = expand_appgroups(e_uci, list(rule.get('appgroup', [])))
    sources = [f'local_ip == {source}' for source in expand_source(list(rule.get('source', [])))]

    if not match:
        if require_appgroup or not sources:
            return ''
        return f"({' || '.join(sources)});"

    if sources:
        return f"({' || '.join(sources)}) && {match};"
    return f'{match};'


def list_rules(e_uci: EUci) -> list[dict]:
    """
    List the rules in priority order, the order they are evaluated in.

    Rules hidden with `ns_visible '0'` are left out: they are system entries the user must not touch.

    Args:
      - e_uci: euci instance

    Returns:
        list of dicts, each dict contains the property "id", "name", "enabled", "action", "source",
        "appgroups", "managed" and "index", plus "criteria" for the rules the API did not create
    """
    groups = {section: group.get('ns_name', '')
              for section, group in (utils.get_all_by_type(e_uci, 'dpi', 'appgroup') or {}).items()}
    rules = []
    for section, rule in __sorted_rules(e_uci):
        if rule.get('ns_visible', '1') == '0':
            continue
        data_rule = {
            'id': section,
            'name': rule.get('ns_name', ''),
            'enabled': rule.get('enabled', '1') == '1',
            'action': rule.get('action', ''),
            'source': list(rule.get('source', [])),
            'appgroups': [{'id': group, 'name': groups.get(group, group)}
                          for group in rule.get('appgroup', [])],
            # a rule the UI did not create can be renamed, toggled, reordered and deleted, but not edited
            'managed': rule.get('ns_managed', '0') == '1',
            'index': len(rules)
        }
        if 'criteria' in rule:
            data_rule['criteria'] = rule.get('criteria')
        rules.append(data_rule)

    return rules


def __save_rule_data(e_uci: EUci, config_name: str, name: str, enabled: bool, action: str,
                     source: list[str], appgroups: list[str]):
    e_uci.set('dpi', config_name, 'ns_name', name)
    e_uci.set('dpi', config_name, 'ns_managed', '1')
    e_uci.set('dpi', config_name, 'enabled', enabled)
    e_uci.set('dpi', config_name, 'action', action)
    if appgroups:
        e_uci.set('dpi', config_name, 'appgroup', appgroups)
    else:
        # a rule migrated from a global exemption has no group: the option must go, not stay empty
        e_uci.delete('dpi', config_name, 'appgroup')
    if source:
        e_uci.set('dpi', config_name, 'source', source)
    else:
        # no source means every host: the option must go, not stay empty
        e_uci.delete('dpi', config_name, 'source')


def add_rule(e_uci: EUci, name: str, enabled: bool, action: str, source: list[str],
             appgroups: list[str], position: str = 'bottom', require_appgroup: bool = True) -> str:
    """
    Store a new rule.

    Args:
      - e_uci: euci instance
      - name: name of the rule
      - enabled: enable the rule
      - action: 'block' or 'allow'
      - source: list of addresses, networks or ranges, empty to match every host
      - appgroups: config names of the application groups the rule matches, at least one unless
        `require_appgroup` is False
      - position: 'top' to evaluate the rule before every other one, 'bottom' after them
      - require_appgroup: set to False only when migrating a global exemption into a source-only Allow
        rule, a shape the drawer cannot produce and never will

    Returns:
        config name of the rule created

    Raises:
      - ValidationError: if any argument is invalid
    """
    name = __validate_rule_name(name)
    if action not in DPI_RULE_ACTIONS:
        raise ValidationError('action', 'invalid_action', action)
    if position not in DPI_RULE_POSITIONS:
        raise ValidationError('position', 'invalid_position', position)
    source = __validate_source(source)
    appgroups = __validate_appgroups(e_uci, appgroups, require_appgroup)

    config_name = utils.get_random_id()
    e_uci.set('dpi', config_name, 'rule')
    __save_rule_data(e_uci, config_name, name, enabled, action, source, appgroups)

    order = [section for section, _ in __sorted_rules(e_uci) if section != config_name]
    order.insert(0, config_name) if position == 'top' else order.append(config_name)
    __renumber_rules(e_uci, order)

    __toggle_engine(e_uci)
    e_uci.save('dpi')
    return config_name


def edit_rule(e_uci: EUci, config_name: str, name: str, enabled: bool, action: str, source: list[str],
              appgroups: list[str]) -> str:
    """
    Edit a rule. Only rules created through the API can be edited: a rule carrying a hand-written
    criteria has no source and no group to fill the form with, and rewriting it would change what it
    matches.

    Args:
      - e_uci: euci instance
      - config_name: config name of the rule to edit
      - name: name of the rule
      - enabled: enable the rule
      - action: 'block' or 'allow'
      - source: list of addresses, networks or ranges, empty to match every host
      - appgroups: config names of the application groups the rule matches, at least one

    Returns:
        config name of the rule edited

    Raises:
      - ValidationError: if the rule does not exist, is not managed, or any argument is invalid
    """
    if not __is_rule(e_uci, config_name):
        raise ValidationError('id', 'rule_not_found', config_name)
    if e_uci.get('dpi', config_name, 'ns_managed', default='0') != '1':
        raise ValidationError('id', 'rule_not_managed', config_name)

    name = __validate_rule_name(name)
    if action not in DPI_RULE_ACTIONS:
        raise ValidationError('action', 'invalid_action', action)
    source = __validate_source(source)
    appgroups = __validate_appgroups(e_uci, appgroups)

    __save_rule_data(e_uci, config_name, name, enabled, action, source, appgroups)
    __toggle_engine(e_uci)
    e_uci.save('dpi')
    return config_name


def delete_rule(e_uci: EUci, config_name: str) -> str:
    """
    Delete a rule and close the gap its priority leaves behind.

    Args:
      - e_uci: euci instance
      - config_name: config name of the rule to delete

    Returns:
        config name of the rule deleted

    Raises:
      - ValidationError: if the rule does not exist
    """
    if not __is_rule(e_uci, config_name):
        raise ValidationError('id', 'rule_not_found', config_name)

    e_uci.delete('dpi', config_name)
    __renumber_rules(e_uci)
    __toggle_engine(e_uci)
    e_uci.save('dpi')
    return config_name


def rename_rule(e_uci: EUci, config_name: str, name: str) -> str:
    """
    Rename a rule, managed or not.

    Args:
      - e_uci: euci instance
      - config_name: config name of the rule to rename
      - name: new name of the rule

    Returns:
        config name of the rule renamed

    Raises:
      - ValidationError: if the rule does not exist or the name is invalid
    """
    if not __is_rule(e_uci, config_name):
        raise ValidationError('id', 'rule_not_found', config_name)

    e_uci.set('dpi', config_name, 'ns_name', __validate_rule_name(name))
    e_uci.save('dpi')
    return config_name


def enable_rule(e_uci: EUci, config_name: str) -> str:
    """
    Enable a rule, managed or not.

    Args:
      - e_uci: euci instance
      - config_name: config name of the rule to enable

    Returns:
        config name of the rule enabled

    Raises:
      - ValidationError: if the rule does not exist
    """
    if not __is_rule(e_uci, config_name):
        raise ValidationError('id', 'rule_not_found', config_name)

    e_uci.set('dpi', config_name, 'enabled', '1')
    __toggle_engine(e_uci)
    e_uci.save('dpi')
    return config_name


def disable_rule(e_uci: EUci, config_name: str) -> str:
    """
    Disable a rule, managed or not.

    Args:
      - e_uci: euci instance
      - config_name: config name of the rule to disable

    Returns:
        config name of the rule disabled

    Raises:
      - ValidationError: if the rule does not exist
    """
    if not __is_rule(e_uci, config_name):
        raise ValidationError('id', 'rule_not_found', config_name)

    e_uci.set('dpi', config_name, 'enabled', '0')
    __toggle_engine(e_uci)
    e_uci.save('dpi')
    return config_name


def order_rules(e_uci: EUci, order: list[str]) -> list[str]:
    """
    Reorder every rule, renumbering the priorities densely from the given order.

    The whole set must be listed, hidden rules included: a partial order would silently move the rules
    left out, which with a paginated list is a rule the caller never saw.

    Args:
      - e_uci: euci instance
      - order: config names of every rule, in the order they must be evaluated

    Returns:
        the list of the ordered rules

    Raises:
      - ValidationError: if the order does not name every rule exactly once
    """
    rules = [section for section, _ in __sorted_rules(e_uci)]
    for section in order:
        if section not in rules:
            raise ValidationError('order', 'rule_not_found', section)
    if len(order) != len(set(order)) or len(order) != len(rules):
        raise ValidationError('order', 'invalid_order', order)

    __renumber_rules(e_uci, order)
    e_uci.save('dpi')
    return order


# Migration: one-time, in-place bump of /etc/config/dpi from the schema used before application groups
# existed. A rule from that schema carries `device`, `application`, `protocol` or `category` — fields
# only that API ever wrote, so their presence is a permanent, unambiguous marker regardless of whether
# `priority` was since assigned to it by an unrelated add/edit/delete. A global exemption is identified
# by its section type, which this migration removes once every exemption has become a rule.

def freeze_legacy_criteria(e_uci: EUci, rule: dict) -> str:
    """
    Build the criteria of a rule written before application groups existed, the way `dpi-config` has
    always generated it: source, application, protocol and category turned into an expression narrowed
    to the rule's device, with the VLAN rewrite applied when the device names a VLAN. Used by the
    generator for a legacy rule the migration has not converted yet, and by the migration itself to
    freeze a rule's behaviour verbatim before clearing those fields.

    Args:
      - e_uci: euci instance
      - rule: the rule section, as returned by `uci.get_all`

    Returns:
        the semicolon-terminated expression
    """
    device = rule.get('device', '*')

    if 'criteria' in rule:
        # criteria has precedence over source, protocol, category and application
        criteria = rule['criteria'].replace('"', "'")
    else:
        sources = []
        for source in rule.get('source', []):
            if objects.is_object_id(source):
                for ip in objects.get_object_ips(e_uci, source):
                    sources.append(f'local_ip == {ip}')
            else:
                sources.append(f'local_ip == {source}')

        applications = []
        for app in rule.get('application', []):
            applications.append(f"app == '{app}'")
        for proto in rule.get('protocol', []):
            applications.append(f"proto == '{proto.lower()}'")
        for cat in rule.get('category', []):
            applications.append(f"category == '{cat.lower()}'")

        sources_s = ' or '.join(sources)
        applications_s = ' or '.join(applications)
        criteria = f"(iface_nfq_src == '{device}' or iface_nfq_dst == '{device}') && "
        if len(sources) < 1:
            criteria += f'({applications_s}) ;'
        elif len(applications) < 1:
            criteria += f'({sources_s}) ;'
        else:
            criteria += f'({sources_s}) && ({applications_s}) ;'

    vlan_id = None
    base_if = None
    for item in utils.get_all_by_type(e_uci, 'network', 'device').values():
        if item.get('vid', None) is not None and item.get('name', '') == device:
            vlan_id = item.get('vid', None)
            base_if = item.get('ifname', None)
            break

    if vlan_id is not None and base_if is not None:
        criteria = f'vlan_id == {vlan_id} && {criteria}'

    return criteria


def __exemption_source(e_uci: EUci, criteria: str) -> list[str] | None:
    """
    Turn a global exemption's criteria into a rule source. A firewall object is expanded into its
    member addresses; a plain address, network or range is kept as is.

    Returns:
        the source list, or None when the criteria is empty or does not resolve to at least one
        address, telling the caller to fall back to an unmanaged rule carrying it verbatim
    """
    if not criteria:
        return None
    if objects.is_object_id(criteria):
        return objects.get_object_ips(e_uci, criteria) or None
    try:
        return __validate_source([criteria])
    except ValidationError:
        return None


def migrate_schema(e_uci: EUci) -> bool:
    """
    Migrate every rule and exemption from the schema used before application groups existed.

    Each legacy rule (`device`, `application`, `protocol` or `category` set) is turned into an unmanaged
    rule with its behaviour frozen verbatim into `criteria` — see `freeze_legacy_criteria`. A rule whose
    action is a retired QoS value, carries a per-rule exemption (a field no recent API ever wrote), or
    ends up matching nothing is dropped instead, with a log line naming it.

    Each global exemption becomes an Allow rule at the top of the list: a managed, source-only rule
    (`require_appgroup=False`) when its criteria is a plain address, CIDR or firewall object; an
    unmanaged one carrying the criteria verbatim otherwise. Disabled exemptions become disabled rules.
    The `exemption` section type, `firewall_exemption` and `popular_filters` are then removed.

    Safe to call unconditionally on every boot: a box with nothing left in the old schema returns False
    without touching UCI.

    Args:
      - e_uci: euci instance

    Returns:
        True if the config was changed (and therefore committed and reloaded), False otherwise
    """
    exemptions = utils.get_all_by_type(e_uci, 'dpi', 'exemption') or {}
    rules = utils.get_all_by_type(e_uci, 'dpi', 'rule') or {}
    legacy_fields = ('device', 'application', 'protocol', 'category')
    legacy_rules = {section for section, rule in rules.items()
                    if any(field in rule for field in legacy_fields)}

    if not exemptions and not legacy_rules:
        return False

    order = []

    exemption_count = 0
    for section, exemption in exemptions.items():
        exemption_count += 1
        name = f'Migrated exception {exemption_count}'
        enabled = exemption.get('enabled', '1') == '1'
        criteria = (exemption.get('criteria') or '').strip()
        source = __exemption_source(e_uci, criteria)

        e_uci.delete('dpi', section)
        if source is not None:
            rule_id = add_rule(e_uci, name, enabled, 'allow', source, [], require_appgroup=False)
        else:
            rule_id = utils.get_random_id()
            e_uci.set('dpi', rule_id, 'rule')
            e_uci.set('dpi', rule_id, 'ns_name', name)
            e_uci.set('dpi', rule_id, 'enabled', '1' if enabled else '0')
            e_uci.set('dpi', rule_id, 'action', 'allow')
            e_uci.set('dpi', rule_id, 'criteria', criteria if criteria.endswith(';') else f'{criteria};')
        order.append(rule_id)

    rule_count = 0
    for section, rule in rules.items():
        if section not in legacy_rules:
            order.append(section)
            continue

        action = rule.get('action')
        if action != 'block':
            syslog.syslog(syslog.LOG_WARNING, f"dpi migration: dropping {section}, unsupported action {action!r}")
            e_uci.delete('dpi', section)
            continue
        if rule.get('exemption'):
            syslog.syslog(syslog.LOG_WARNING,
                          f"dpi migration: dropping the per-rule exemption on {section}, no longer supported")
        if not any(rule.get(field) for field in ('criteria', 'source', 'application', 'protocol', 'category')):
            syslog.syslog(syslog.LOG_WARNING, f"dpi migration: dropping {section}, it matches nothing")
            e_uci.delete('dpi', section)
            continue

        rule_count += 1
        criteria = freeze_legacy_criteria(e_uci, rule)
        for field in (*legacy_fields, 'source', 'exemption'):
            e_uci.delete('dpi', section, field)
        e_uci.set('dpi', section, 'criteria', criteria)
        e_uci.set('dpi', section, 'ns_name', f'Migrated rule {rule_count}')
        order.append(section)

    __renumber_rules(e_uci, order)
    e_uci.delete('dpi', 'config', 'firewall_exemption')
    e_uci.delete('dpi', 'config', 'popular_filters')
    __toggle_engine(e_uci)
    e_uci.save('dpi')
    __apply(e_uci)
    return True
