#!/usr/bin/python
# -*- coding: utf-8 -*-

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
module: ceph_authtool
short_description: ceph keyring manipulation
version_added: "1.1.0"
description:
    - Create, view, and modify a Ceph keyring file.
options:
    name:
        description:
            - specify entityname to operate on
        type: str
        required: false
    create_keyring:
        description:
            - will create a new keyring, overwriting any existing keyringfile
        type: bool
        required: false
        default: false
    gen_key:
        description:
            - will generate a new secret key for the specified entityname
        type: bool
        required: false
        default: false
    add_key:
        description:
            - will add an encoded key to the keyring
        type: str
        required: false
    import_keyring:
        description:
            - will import the content of a given keyring to the keyringfile
        type: str
        required: false
    caps:
        description:
            - will set the capability for given subsystem
        type: dict
        required: false
    path:
        description:
            - where the caps file will be created
        type: str
        required: true
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
author:
    - guillaume abrioux (@guits)
'''

EXAMPLES = '''
- name: Create admin keyring
  ceph_authtool:
    name: client.admin
    path: "/etc/ceph/ceph.client.admin.keyring"
    owner: 'ceph'
    group: 'ceph'
    mode: "0400"
    caps:
      mon: allow *
      mgr: allow *
      osd: allow *
      mds: allow *
    create_keyring: true
    gen_key: true
    add_key: admin_secret
'''

RETURN = '''#  '''

from ansible.module_utils.basic import AnsibleModule  # type: ignore
try:
    from ansible_collections.ceph.automation.plugins.module_utils.ceph_common import container_exec, is_containerized  # type: ignore
except ImportError:
    from module_utils.ceph_common import container_exec, is_containerized

import datetime
import os


class KeyringExists(Exception):
    pass


def build_cmd(create_keyring=False,
              gen_key=False,
              import_keyring=None,
              caps=None,
              name=None,
              path=None,
              container_image=None):

    auth_tool_binary: str = 'ceph-authtool'

    if container_image:
        c = container_exec(auth_tool_binary,
                           container_image)
    else:
        c = [auth_tool_binary]

    if name:
        c.extend(['-n', name])
    if create_keyring:
        if os.path.exists(path):
            raise KeyringExists
        c.append('-C')
    if gen_key:
        c.append('-g')
    if caps:
        for k, v in caps.items():
            c.extend(['--cap'] + [k] + [v])

    c.append(path)

    if import_keyring:
        c.extend(['--import-keyring', import_keyring])

    return c


def run_module():
    module_args = dict(
        name=dict(type='str', required=False),
        create_keyring=dict(type='bool', required=False, default=False),
        gen_key=dict(type='bool', required=False, default=False),
        add_key=dict(type='str', required=False, default=None, no_log=False),
        import_keyring=dict(type='str', required=False, default=None, no_log=False),
        caps=dict(type='dict', required=False, default=None),
        path=dict(type='str', required=True),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        add_file_common_args=True,
    )

    cmd = []
    changed = False

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
    try:
        cmd = build_cmd(**module.params, container_image=container_image)
    except KeyringExists:
        rc = 0
        out = f"{module.params['path']} already exists. Skipping"
        err = ""
    else:
        rc, out, err = module.run_command(cmd)
        if rc == 0:
            changed = True

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

    # file_args = module.load_file_common_arguments(module.params)
    # module.set_fs_attributes_if_different(file_args, False)
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
