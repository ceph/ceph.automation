#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2020, Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import, division, print_function, annotations
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ceph_crush_rule
short_description: Manage Ceph Crush Replicated/Erasure Rule
version_added: "1.1.0"
description:
    - Manage Ceph Crush rule(s) creation, deletion and updates.
    - Erasure-coded rules cannot be updated at the time.
options:
    name:
        description:
            - The name of the Ceph CRUSH rule.
        type: str
        required: true
    fsid:
        description:
            - Identifier (FSID) of the Ceph cluster to interact with.
        type: str
        required: false
    image:
        description:
            - The Ceph container image to use.
        type: str
        required: false
    state:
        description:
            - If 'present' is used, the module creates a rule if it doesn't exist or update it if it already exists.
            - If 'absent' is used, the module will simply delete the rule.
        type: str
        required: false
        choices: ['present', 'absent']
        default: present
    rule_type:
        description:
            - The ceph CRUSH rule type.
        type: str
        required: false
        choices: ['replicated', 'erasure']
    bucket_root:
        description:
            - The ceph bucket root for replicated rule.
        type: str
        required: false
    bucket_type:
        description:
            - The ceph bucket type for replicated rule.
        type: str
        required: false
        choices: ['osd', 'host', 'chassis', 'rack', 'row', 'pdu', 'pod',
                 'room', 'datacenter', 'zone', 'region', 'root']
    device_class:
        description:
            - The ceph device class for replicated rule.
        type: str
        required: false
    profile:
        description:
            - The ceph erasure profile for erasure rule.
        type: str
        required: false
author:
    - Dimitri Savineau (@dsavineau)
'''

EXAMPLES = '''
- name: Create a Ceph Crush replicated rule
  ceph.automation.ceph_crush_rule:
    name: foo
    bucket_root: default
    bucket_type: host
    device_class: ssd
    rule_type: replicated

- name: >
    Update the failure domain and remove the device
    class in the created replication rule
  ceph.automation.ceph_crush_rule:
    name: foo
    bucket_root: default
    bucket_type: datacenter
    rule_type: replicated

- name: Create a Ceph Crush erasure rule
  ceph.automation.ceph_crush_rule:
    name: foo
    profile: bar
    rule_type: erasure

- name: Delete a Ceph Crush rule
  ceph.automation.ceph_crush_rule:
    name: foo
    state: absent
'''

RETURN = '''#  '''

from ansible.module_utils.basic import AnsibleModule

try:
    from ansible_collections.ceph.automation.plugins.module_utils.ceph_common import \
        exit_module, \
        build_base_cmd_shell, \
        exec_command
except ImportError:
    from module_utils.ceph_common import \
        exit_module, \
        build_base_cmd_shell, \
        exec_command

from typing import Dict, List, Tuple
import datetime
import json
import tempfile
import os
import re

RULE_TYPES = {
    1: 'replicated',
    3: 'erasure',
}


def create_rule(module: AnsibleModule) -> List[str]:
    """
    Compose command to create a new CRUSH replicated/erasure rule.

    :param module: AnsibleModule object with the user configuration.
    :return: Shell command in the list of strings form
    """

    name = module.params.get('name')
    rule_type = module.params.get('rule_type')
    bucket_root = module.params.get('bucket_root')
    bucket_type = module.params.get('bucket_type')
    device_class = module.params.get('device_class')
    profile = module.params.get('profile')

    cmd = build_base_cmd_shell(module)
    cmd.extend(['ceph', 'osd', 'crush', 'rule'])

    if rule_type == 'replicated':
        cmd.extend(['create-replicated', name, bucket_root, bucket_type])
        if device_class:
            cmd.append(device_class)
    else:
        cmd.extend(['create-erasure', name])
        if profile:
            cmd.append(profile)

    return cmd


def remove_rule(module: AnsibleModule) -> List[str]:
    """
    Compose command to remove the CRUSH rule specified in the configuration.

    :param module: AnsibleModule object with the user configuration.
    :return: Shell command in the list of strings form
    """

    name = module.params.get('name')

    cmd = build_base_cmd_shell(module)
    cmd.extend(['ceph', 'osd', 'crush', 'rule', 'rm', name])

    return cmd


def need_changes(module: AnsibleModule, rule: Dict) -> bool:
    """
    Compare the rule requested by the user and the existing rule.

    :param module: AnsibleModule object with the user configuration.
    :param rule: Dict with existing rule that was dumped from cluster.
    :return: True if configuration needs to be changed.
    """
    bucket_root = module.params.get('bucket_root')
    bucket_type = module.params.get('bucket_type')
    device_class = module.params.get('device_class')

    for step in rule['steps']:
        if step['op'] == 'take':
            root_string = step['item_name']
            exist_bucket_root = root_string.split('~')
            exist_root = exist_bucket_root[0]
            exist_class = exist_bucket_root[1] if len(exist_bucket_root) > 1 else None
            if exist_root != bucket_root or exist_class != device_class:
                return True
        elif step['op'] == 'chooseleaf_firstn':
            if step['type'] != bucket_type:
                return True

    return False


def decompile_crushmap(module: AnsibleModule) -> Tuple[int, List[str], str, str]:
    """
    Retrieve full CRUSH map from the cluster to a binary file with 'ceph osd getcrushmap'
    and decompile the map with the 'crushtool' command.

    :param module: AnsibleModule object with the user configuration.
    :return: RC, CMD, Contents of the decompiled CRUSH map file as string, STDERR.
    """
    crushmap_content = None

    with tempfile.TemporaryDirectory() as tmpdirname:
        binary_map = os.path.join(tmpdirname, '_raw_crushmap.bin')
        decompiled_map = os.path.join(tmpdirname, '_crushmap.txt')

        cmd = build_base_cmd_shell(module)
        cmd.extend(['--mount', '{0}:{0}'.format(tmpdirname), '--'])

        dump_crush_map = cmd.copy()
        dump_crush_map.extend(['ceph', 'osd', 'getcrushmap', '-o', binary_map])

        res = exec_command(module, dump_crush_map)
        if res[0] != 0:
            return res[0], res[1], 'dump of the CRUSH map failed with output: {}'.format(res[2]), res[3]

        decompile_map = cmd.copy()
        decompile_map.extend(['crushtool', '-d', binary_map, '-o', decompiled_map])

        res = exec_command(module, decompile_map)
        if res[0] != 0:
            return res[0], res[1], 'decompile of the CRUSH map failed with output: {}'.format(res[2]), res[3]

        with open(decompiled_map, 'r') as f:
            crushmap_content = f.read()

    return 0, decompile_map, crushmap_content, ''


def patch_content(module: AnsibleModule, crushmap_content: str) -> str:
    """
    Patche the contents of the CRUSH map file according to the user settings for
    bucket_root, device_class and bucket_type (the failure domain for the specified rule).

    :param module: AnsibleModule object with the user configuration.
    :param crushmap_content: String containing the CRUSH map content.
    :return: String containing the patched CRUSH map content.
    """
    rule_name = module.params.get('name')
    bucket_root = module.params.get('bucket_root')
    failure_domain = module.params.get('bucket_type')
    device_class = module.params.get('device_class')

    crushmap = crushmap_content.splitlines()

    inside_rule_block = False
    reg_bucket_root = re.compile(r'^\s*step take (\S+)( class (\S+))?$')
    reg_failure_domain = re.compile(r'^\s*step chooseleaf firstn 0 type (\S+)$')
    for i in range(len(crushmap)):
        line = crushmap[i]
        # Work only with the specified rule, skip other rule blocks.
        if line.startswith('rule {}'.format(rule_name)):
            inside_rule_block = True
            continue
        elif inside_rule_block and line.startswith('}'):
            break

        if inside_rule_block:
            # Check if this line is 'step take {bucket_root} <class {device_class}>'
            root_match = reg_bucket_root.match(line)
            if root_match:
                exist_root = root_match.group(1)
                crushmap[i] = line.replace(exist_root, bucket_root)
                # Add device class if specified in the config but missing.
                if device_class and root_match.group(3) is None:
                    crushmap[i] = crushmap[i] + ' class {}'.format(device_class)
                # Remove device class if unspecified in the user configuration.
                elif device_class is None and root_match.group(3):
                    crushmap[i] = crushmap[i].replace(root_match.group(2), '')
                # Change device class name if exists and specified in the user config.
                elif device_class and root_match.group(3):
                    crushmap[i] = crushmap[i].replace(root_match.group(3), device_class)
                continue

            # Check if this line is 'step chooseleaf firstn 0 type {failure_domain}'
            domain_match = reg_failure_domain.match(line)
            if domain_match:
                exist_dom = domain_match.group(1)
                crushmap[i] = line.replace(exist_dom, failure_domain)
                continue

    result = '\n'.join(crushmap)
    return result


def install_crushmap(module: AnsibleModule, crushmap_content: str) -> Tuple[int, List[str], str, str]:
    """
    Install the CRUSH map file from the 'crushmap_content' string variable to the Ceph cluster.

    :param module: AnsibleModule object with the user configuration.
    :param crushmap_content: String with the CRUSH map content.
    :return: RC, CMD, STDOUT, STDERR of the latest executed command.
    """
    with tempfile.TemporaryDirectory() as tmpdirname:
        patched_map = os.path.join(tmpdirname, '_patched_crushmap.txt')
        binary_map = os.path.join(tmpdirname, '_raw_patched_crushmap.bin')

        with open(patched_map, 'w') as f:
            f.write(crushmap_content)

        cmd = build_base_cmd_shell(module)
        cmd.extend(['--mount', '{0}:{0}'.format(tmpdirname), '--'])

        compile_map = cmd.copy()
        compile_map.extend(['crushtool', '-c', patched_map, '-o', binary_map])

        res = exec_command(module, compile_map)
        if res[0] != 0:
            return res[0], res[1], 'compilation of the CRUSH map failed with output: {}'.format(res[2]), res[3]

        install_map = cmd.copy()
        install_map.extend(['ceph', 'osd', 'setcrushmap', '-i', binary_map])

        res = exec_command(module, install_map)
        if res[0] != 0:
            return res[0], res[1], 'installation of the CRUSH map failed with output: {}'.format(res[2]), res[3]

    return res


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            fsid=dict(type='str', required=False),
            image=dict(type='str', required=False),
            state=dict(type='str', required=False, choices=['present', 'absent'], default='present'),
            rule_type=dict(type='str', required=False, choices=['replicated', 'erasure']),
            bucket_root=dict(type='str', required=False),
            bucket_type=dict(
                type='str',
                required=False,
                choices=['osd', 'host', 'chassis', 'rack', 'row', 'pdu',
                         'pod', 'room', 'datacenter', 'zone', 'region', 'root']
            ),
            device_class=dict(type='str', required=False),
            profile=dict(type='str', required=False)
        ),
        supports_check_mode=True,
        required_if=[
            ('state', 'present', ['rule_type']),
            ('state', 'present', ['name']),
            ('state', 'absent', ['name']),
            ('rule_type', 'replicated', ['bucket_root', 'bucket_type']),
            ('rule_type', 'erasure', ['profile'])
        ]
    )

    # Gather module parameters in variables
    name = module.params.get('name')
    state = module.params.get('state')
    rule_type = module.params.get('rule_type')

    if module.check_mode:
        module.exit_json(
            changed=False,
            stdout='',
            stderr='',
            rc=0,
            start='',
            end='',
            delta='',
        )

    startd = datetime.datetime.now()
    changed = False

    get_rule = build_base_cmd_shell(module)
    get_rule.extend(['ceph', 'osd', 'crush', 'rule', 'dump', name, '--format=json'])
    rc, cmd, out, err = exec_command(module, get_rule)

    if state == "present":
        if rc != 0:
            rc, cmd, out, err = exec_command(module, create_rule(module))
            changed = True
        else:
            rule = json.loads(out)
            if rule_type != RULE_TYPES[rule['type']]:
                module.fail_json(
                    msg="Can not convert crush rule {} to {}".format(name, rule_type),
                    changed=False, rc=1
                )
            if rule_type == 'replicated' and need_changes(module, rule):
                rc, cmd, out, err = decompile_crushmap(module)
                if rc != 0:
                    exit_module(module=module, out=out, rc=rc, cmd=cmd, err=err, startd=startd, changed=changed)
                patched_crushmap = patch_content(module, out)
                rc, cmd, out, err = install_crushmap(module, patched_crushmap)
                changed = True

    elif state == "absent":
        if rc == 0:
            rc, cmd, out, err = exec_command(module, remove_rule(module))
            changed = True
        else:
            rc = 0
            out = "Crush Rule {} doesn't exist".format(name)
    else:
        pass

    exit_module(module=module, out=out, rc=rc, cmd=cmd, err=err, startd=startd, changed=changed)


if __name__ == '__main__':
    main()
