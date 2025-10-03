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
module: ceph_crush_rule_info
short_description: Lists Ceph Crush Replicated/Erasure Rules
version_added: "1.1.0"
description:
    - Retrieves Ceph Crush rule(s).
options:
    name:
        description:
            - The name of the Ceph CRUSH rule.
            - If no value is provided, all Ceph CRUSH rules are returned.
        type: str
        required: false
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
author:
    - Teoman ONAY (@asm0deuz)
'''

EXAMPLES = '''
- name: get a Ceph Crush rule information
  ceph_crush_rule_info:
    name: foo
'''

RETURN = '''#  '''

from ansible.module_utils.basic import AnsibleModule
try:
    from ansible_collections.ceph.automation.plugins.module_utils.ceph_common import \
        build_base_cmd_shell, \
        exit_module, \
        exec_command
except ImportError:
    from module_utils.ceph_common import \
        build_base_cmd_shell, \
        exit_module, \
        exec_command

import datetime


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=False),
            fsid=dict(type='str', required=False),
            image=dict(type='str', required=False),
        ),
        supports_check_mode=True,
    )

    startd = datetime.datetime.now()

    name = module.params.get('name')
    cmd = build_base_cmd_shell(module)
    cmd.extend(['ceph', 'osd', 'crush', 'rule', 'dump', name, '--format=json'])
    rc, cmd, out, err = exec_command(module, cmd)

    exit_module(module=module, out=out, rc=rc, cmd=cmd, err=err, startd=startd, changed=False)  # noqa: E501


if __name__ == '__main__':
    main()
