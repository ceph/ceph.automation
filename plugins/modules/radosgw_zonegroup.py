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

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: radosgw_zonegroup

short_description: Manage RADOS Gateway Zonegroup

version_added: "1.1.0"

description:
    - Manage RADOS Gateway zonegroup(s) creation, deletion and updates.
options:
    cluster:
        description:
            - The ceph cluster name.
        type: str
        required: false
        default: ceph
    name:
        description:
            - name of the RADOS Gateway zonegroup.
        type: str
        required: true
    state:
        description:
            - If 'present' is used, the module creates a zonegroup if it doesn't exist or update it if it already exists.
            - If 'absent' is used, the module will simply delete the zonegroup.
            - If 'info' is used, the module will return all details about the existing zonegroup (json formatted).
        type: str
        required: false
        choices: ['present', 'absent']
        default: present
    realm:
        description:
            - name of the RADOS Gateway realm.
        type: str
        required: true
    endpoints:
        description:
            - endpoints of the RADOS Gateway zonegroup.
        type: list
        elements: str
        required: false
        default: []
    default:
        description:
            - set the default flag on the zonegroup.
        type: bool
        required: false
        default: false
    master:
        description:
            - set the master flag on the zonegroup.
        type: bool
        required: false
        default: false

author:
    - Dimitri Savineau (@dsavineau)
'''

EXAMPLES = '''
- name: create a RADOS Gateway default zonegroup
  radosgw_zonegroup:
    name: foo
    realm: bar
    endpoints:
      - http://192.168.1.10:8080
      - http://192.168.1.11:8080
    default: true

- name: get a RADOS Gateway zonegroup information
  radosgw_zonegroup:
    name: foo
    realm: bar
    state: info

- name: delete a RADOS Gateway zonegroup
  radosgw_zonegroup:
    name: foo
    realm: bar
    state: absent
'''

RETURN = '''#  '''

import os
import json
import datetime
from ansible.module_utils.basic import AnsibleModule

try:
    from ansible_collections.ceph.automation.plugins.module_utils.ceph_common import fatal
except ImportError:
    from module_utils.ceph_common import fatal


def container_exec(binary, container_image):
    '''
    Build the docker CLI to run a command inside a container
    '''

    container_binary = os.getenv('CEPH_CONTAINER_BINARY')
    command_exec = [container_binary,
                    'run',
                    '--rm',
                    '--net=host',
                    '-v', '/etc/ceph:/etc/ceph:z',
                    '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
                    '-v', '/var/log/ceph/:/var/log/ceph/:z',
                    '--entrypoint=' + binary, container_image]
    return command_exec


def is_containerized():
    '''
    Check if we are running on a containerized cluster
    '''

    if 'CEPH_CONTAINER_IMAGE' in os.environ:
        container_image = os.getenv('CEPH_CONTAINER_IMAGE')
    else:
        container_image = None

    return container_image


def pre_generate_radosgw_cmd(container_image=None):
    '''
    Generate radosgw-admin prefix comaand
    '''
    if container_image:
        cmd = container_exec('radosgw-admin', container_image)
    else:
        cmd = ['radosgw-admin']

    return cmd


def generate_radosgw_cmd(cluster, args, container_image=None):
    '''
    Generate 'radosgw' command line to execute
    '''

    cmd = pre_generate_radosgw_cmd(container_image=container_image)

    base_cmd = [
        '--cluster',
        cluster,
        'zonegroup'
    ]

    cmd.extend(base_cmd + args)

    return cmd


def exec_commands(module, cmd):
    '''
    Execute command(s)
    '''

    rc, out, err = module.run_command(cmd)

    return rc, cmd, out, err


def create_zonegroup(module, container_image=None):
    '''
    Create a new zonegroup
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')
    realm = module.params.get('realm')
    endpoints = module.params.get('endpoints')
    default = module.params.get('default')
    master = module.params.get('master')

    args = ['create', '--rgw-realm=' + realm, '--rgw-zonegroup=' + name]

    if endpoints:
        args.extend(['--endpoints=' + ','.join(endpoints)])

    if default:
        args.append('--default')

    if master:
        args.append('--master')

    cmd = generate_radosgw_cmd(cluster=cluster,
                               args=args,
                               container_image=container_image)

    return cmd


def modify_zonegroup(module, container_image=None):
    '''
    Modify a new zonegroup
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')
    realm = module.params.get('realm')
    endpoints = module.params.get('endpoints')
    default = module.params.get('default')
    master = module.params.get('master')

    args = ['modify', '--rgw-realm=' + realm, '--rgw-zonegroup=' + name]

    if endpoints:
        args.extend(['--endpoints=' + ','.join(endpoints)])

    if default:
        args.append('--default')

    if master:
        args.append('--master')

    cmd = generate_radosgw_cmd(cluster=cluster,
                               args=args,
                               container_image=container_image)

    return cmd


def get_zonegroup(module, container_image=None):
    '''
    Get existing zonegroup
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')
    realm = module.params.get('realm')

    args = [
        'get',
        '--rgw-realm=' + realm,
        '--rgw-zonegroup=' + name,
        '--format=json'
    ]

    cmd = generate_radosgw_cmd(cluster=cluster,
                               args=args,
                               container_image=container_image)

    return cmd


def get_realm(module, container_image=None):
    '''
    Get existing realm
    '''

    cluster = module.params.get('cluster')
    realm = module.params.get('realm')

    cmd = pre_generate_radosgw_cmd(container_image=container_image)

    args = [
        '--cluster',
        cluster,
        'realm',
        'get',
        '--rgw-realm=' + realm,
        '--format=json'
    ]

    cmd.extend(args)

    return cmd


def remove_zonegroup(module, container_image=None):
    '''
    Remove a zonegroup
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')
    realm = module.params.get('realm')

    args = ['delete', '--rgw-realm=' + realm, '--rgw-zonegroup=' + name]

    cmd = generate_radosgw_cmd(cluster=cluster,
                               args=args,
                               container_image=container_image)

    return cmd


def exit_module(module, out, rc, cmd, err, startd, changed=False):
    endd = datetime.datetime.now()
    delta = endd - startd

    result = dict(
        cmd=cmd,
        start=str(startd),
        end=str(endd),
        delta=str(delta),
        rc=rc,
        stdout=out.rstrip("\r\n"),
        stderr=err.rstrip("\r\n"),
        changed=changed,
    )
    module.exit_json(**result)


def run_module():
    module_args = dict(
        cluster=dict(type='str', required=False, default='ceph'),
        name=dict(type='str', required=True),
        state=dict(type='str', required=False, choices=['present', 'absent'], default='present'),  # noqa: E501
        realm=dict(type='str', required=True),
        endpoints=dict(type='list', elements='str', required=False, default=[]),
        default=dict(type='bool', required=False, default=False),
        master=dict(type='bool', required=False, default=False),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    # Gather module parameters in variables
    name = module.params.get('name')
    state = module.params.get('state')
    endpoints = module.params.get('endpoints')
    master = module.params.get('master')

    startd = datetime.datetime.now()
    changed = False

    # will return either the image name or None
    container_image = is_containerized()

    rc, cmd, out, err = exec_commands(module, get_zonegroup(module, container_image=container_image))  # noqa: E501
    if state == "present":
        if rc == 0:
            zonegroup = json.loads(out)
            _rc, _cmd, _out, _err = exec_commands(module, get_realm(module, container_image=container_image))  # noqa: E501
            if _rc != 0:
                fatal(_err, module)
            realm = json.loads(_out)
            current = {
                'endpoints': zonegroup['endpoints'],
                'master': zonegroup.get('is_master', False),
                'realm_id': zonegroup['realm_id']
            }
            asked = {
                'endpoints': endpoints,
                'master': master,
                'realm_id': realm['id']
            }
            changed = current != asked
            if changed and not module.check_mode:
                rc, cmd, out, err = exec_commands(module, modify_zonegroup(module, container_image=container_image))  # noqa: E501
        else:
            if not module.check_mode:
                rc, cmd, out, err = exec_commands(module, create_zonegroup(module, container_image=container_image))  # noqa: E501
            changed = True

    elif state == "absent":
        if rc == 0:
            if not module.check_mode:
                rc, cmd, out, err = exec_commands(module, remove_zonegroup(module, container_image=container_image))  # noqa: E501
            changed = True
        else:
            rc = 0
            out = "Zonegroup {} doesn't exist".format(name)

    exit_module(module=module, out=out, rc=rc, cmd=cmd, err=err, startd=startd, changed=changed)  # noqa: E501


def main():
    run_module()


if __name__ == '__main__':
    main()
