# Copyright 2018, Red Hat, Inc.
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
module: ceph_key_info

author: Teoman ONAY (@asM0deuz)

short_description: Manage Cephx key(s)

version_added: "1.1.0"

description:
    - the module will return in a json format the description of a given keyring.
options:
    cluster:
        description:
            - The ceph cluster name.
        required: false
        type: str
        default: ceph
    name:
        description:
            - name of the CephX key
        type: str
        required: true
    user:
        description:
            - entity used to perform operation. It corresponds to the -n option (--name)
        type: str
        required: false
        default: 'client.admin'
    user_key:
        description:
            - the path to the keyring corresponding to the user being used. It corresponds to the -k option (--keyring)
        type: str
        required: false
    output_format:
        description:
            - The key output format when retrieving the information of an entity.
        type: str
        choices: ['json', 'plain', 'xml', 'yaml']
        required: false
        default: json
    mode:
        description:
            - N/A
        type: raw
    owner:
        description:
            - N/A
        type: str
    group:
        description:
            - N/A
        type: str
    seuser:
        description:
            - N/A
        type: str
    serole:
        description:
            - N/A
        type: str
    selevel:
        description:
            - N/A
        type: str
    setype:
        description:
            - N/A
        type: str
    attributes:
        description:
            - N/A
        type: str
        aliases:
            - attr
    unsafe_writes:
        description:
            - N/A
        type: bool
        default: false
'''

EXAMPLES = '''
- name: info cephx key
  ceph_key_info:
    name: "my_key"

- name: info cephx admin key (plain)
  ceph_key_info:
    name: client.admin
    output_format: plain
  register: client_admin_key
'''

RETURN = '''#  '''


try:
    from ansible_collections.ceph.automation.plugins.module_utils.ceph_common import generate_cmd, \
        is_containerized
except ImportError:
    from module_utils.ceph_common import generate_cmd, is_containerized

try:
    from ansible_collections.ceph.automation.plugins.module_utils.ceph_key_common import exec_commands
except ImportError:
    from module_utils.ceph_key_common import exec_commands

import os
import datetime
from ansible.module_utils.basic import AnsibleModule


def info_key(cluster, name, user, user_key, output_format, container_image=None):  # noqa: E501
    '''
    Get information about a CephX key
    '''

    cmd_list = []

    args = [
        'get',
        name,
        '-f',
        output_format,
    ]

    cmd_list.append(generate_cmd(sub_cmd=['auth'],
                                 args=args,
                                 cluster=cluster,
                                 user=user,
                                 user_key=user_key,
                                 container_image=container_image))

    return cmd_list


def run_module():
    module_args = dict(
        cluster=dict(type='str', required=False, default='ceph'),
        name=dict(type='str', required=True),
        user=dict(type='str', required=False, default='client.admin'),
        user_key=dict(type='str', required=False, default=None, no_log=False),
        output_format=dict(type='str', required=False, default='json', choices=['json', 'plain', 'xml', 'yaml'])  # noqa: E501
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        add_file_common_args=True,
    )

    # Gather module parameters in variables
    name = module.params.get('name')
    cluster = module.params.get('cluster')
    user = module.params.get('user')
    user_key = module.params.get('user_key')
    output_format = module.params.get('output_format')

    changed = False
    cmd = ''
    rc = 0
    out = ''
    err = ''

    result = dict(
        changed=changed,
        stdout='',
        stderr='',
        rc=0,
        start='',
        end='',
        delta='',
    )

    if module.check_mode:
        module.exit_json(**result)

    startd = datetime.datetime.now()

    # will return either the image name or None
    container_image = is_containerized()

    if not user_key:
        user_key_filename = '{}.{}.keyring'.format(cluster, user)
        user_key_dir = '/etc/ceph'
        user_key_path = os.path.join(user_key_dir, user_key_filename)
    else:
        user_key_path = user_key

    rc, cmd, out, err = exec_commands(
        module, info_key(cluster, name, user, user_key_path, output_format, container_image))  # noqa: E501

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

    if rc != 0:
        module.fail_json(msg='non-zero return code', **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
