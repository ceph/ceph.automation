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
module: ceph_fs_volume
short_description: Manage volumes, subvolume groups and subvolumes in Ceph filesystem.
version_added: "1.2.0"
description:
    - Manage volumes within Ceph File System(s) (higher abstraction for pools, file systems and MDS daemons).
    - Module provides creation, deletion and updates of volumes, subvolume groups and subvolumes.
    - Not all methods (such as tree pinning) are supported at the time.
    - This module intended to work only with orchestrated Ceph deployments (Cephadm).
options:
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
    name:
        description:
            - Name of the entity (volume, subvolume, subvolume group).
        type: str
        required: true
    initial_placement:
        description:
            - Optional string that specifies the Daemon Placement for the MDS.
            - Used only for new volumes, may be used for sub-types (parent_volume will be affected).
            - See the Ceph documentation about L(deploying MDS daemons,
              https://docs.ceph.com/en/latest/cephadm/services/mds/) and for L(placement specification,
              https://docs.ceph.com/en/latest/cephadm/services/#orchestrator-cli-placement-spec).
        type: str
        required: false
    parent_volume:
        description:
            - Name of the parent volume where the subvolume or subvolume group resides.
            - Required for both V(subvolume) and V(subvolume_group) types.
        type: str
        required: false
    parent_group:
        description:
            - Name of the parent subvolume group where the subvolume resides.
            - O(parent_group) may be skipped when a subvolume is placed without group in the volume itself.
        type: str
        required: false
    size:
        description:
            - Quota size for a subvolume group or subvolume in bytes.
            - Default is no quota. To unset quota use O(size=0).
            - The module will not change quota if O(size) is not defined.
            - The module will not reduce the quota to a size smaller than the occupied space in the subvolume(group).
            - You can force shrinking to a smaller size with O(force_shrink).
        type: int
        required: false
    force_shrink:
        description:
            - Tell the module to reduce the quota size of the subvolume group or subvolume to a size smaller
              than the occupied space in the subvolume(group).
        type: bool
        default: false
        required: false
    force_remove:
        description:
            - Allow the module to forcibly delete the CephFS volume (default Ceph config forbids removal of volumes).
        type: bool
        required: false
        default: false
    type:
        description:
            - Type of entity has to be one of V(volume), V(subvolume_group) or V(subvolume).
            - Parent entities (volume and/or subvolume group) will be created if O(state=present)
              and parent entities are not present.
        type: str
        required: false
        choices: ['volume', 'subvolume_group', 'subvolume']
        default: volume
    state:
        description:
            - If V(present) is used, the module creates a volume if it doesn't exist or update it if it already exists.
            - If V(absent) is used, the module will simply delete the volume.
        type: str
        required: false
        choices: ['present', 'absent']
        default: present
author:
    - Castor Sky (@castorsky) <csky57@gmail.com>
'''

EXAMPLES = '''
- name: Create a volume
  ceph.automation.ceph_fs_volume:
    name: first-volume
    initial_placement: "2 label:_mds"
    state: present

- name: Create a subvolume group in the first-volume
  ceph.automation.ceph_fs_volume:
    name: first-subgroup
    type: subvolume_group
    parent_volume: first-volume
    state: present

- name: Create a subvolume in a new volume recursively
  ceph.automation.ceph_fs_volume:
    name: foo-files
    type: subvolume
    parent_group: directories
    parent_volume: users
    size: 1024000
    state: present

- name: >
    Resize created subvolume reducing quota
    even if place is occupied with data
  ceph.automation.ceph_fs_volume:
    name: foo-files
    parent_group: directories
    parent_volume: users
    size: 1024
    force_shrink: true
    state: present

- name: Delete the CephFS volume recursively
  ceph.automation.ceph_fs_volume:
    name: users
    state: absent
'''

RETURN = '''#  '''

from ansible.module_utils.basic import AnsibleModule

try:
    from ansible_collections.ceph.automation.plugins.module_utils.ceph_common import \
        exec_command, build_base_cmd_shell, exit_module
    from ansible_collections.ceph.automation.plugins.module_utils.ceph_fs_volume_common import \
        get_fs_volume
except ImportError:
    from module_utils.ceph_common import exec_command, build_base_cmd_shell, exit_module
    from module_utils.ceph_fs_volume_common import get_fs_volume

import datetime
import json
from typing import List, Tuple


def need_resize(module: AnsibleModule, stdout: str) -> bool:
    """
    Check if the subvolume group or subvolume specified in the user config requires
    resizing (volumes do not have a quota option and cannot be resized).

    :param module: AnsibleModule object with the user configuration.
    :param stdout: Stdout with a JSON string from the function 'get_fs_volume'.
    :return: True if the subvolume group or subvolume requires resizing.
    """

    flag_resize = False
    target_size = module.params.get('size')
    volume_type = module.params.get('type')

    if volume_type != 'volume' and target_size is not None:
        volume_info = json.loads(stdout)
        old_size = str(volume_info.get('bytes_quota'))
        # Command `ceph fs subvolume(group) create` accepts '0' value for 'no quota'
        # Command `ceph fs subvolume(group) resize` accepts 'infinite' value for 'no quota'
        new_size = str(target_size) if target_size > 0 else 'infinite'

        if old_size != new_size:
            flag_resize = True

    return flag_resize


def resize_fs_volume(
        module: AnsibleModule,
        name: str,
        volume_type: str,
        parent_volume: str = None,
        parent_group: str = None,
        size: str = None
) -> Tuple[int, List[str], str, str]:
    """
    Resize a Ceph FS subvolume group or subvolume.

    :param module: AnsibleModule object with the user configuration.
    :param name: Name of the object to remove.
    :param volume_type: Type of the CephFS abstraction ('volume', 'subvolume_group' or 'subvolume').
    :param parent_volume: CephFS volume where this subvolume group or subvolume resides.
    :param parent_group: CephFS subvolume group where this subvolume resides.
    :param size: Size (in bytes) of the CephFS subvolume group or subvolume.
    :return: Tuple of return code, list of command line args, stdout and stderr.
    """

    no_shrink = '--no-shrink' if not module.params['force_shrink'] else None

    resize_fs = build_base_cmd_shell(module)
    resize_fs.extend(['ceph', 'fs'])

    if volume_type == 'subvolume_group':
        resize_fs.extend(['subvolumegroup', 'resize', parent_volume, name, size, no_shrink])

    elif volume_type == 'subvolume':
        resize_fs.extend(['subvolume', 'resize', parent_volume, name, size, parent_group, no_shrink])

    return exec_command(module, resize_fs)


def create_fs_volume(
        module: AnsibleModule,
        name: str,
        volume_type: str,
        parent_volume: str = None,
        parent_group: str = None,
        size: str = None
) -> Tuple[int, List[str], str, str]:
    """
    Create a Ceph FS volume, subvolume group or subvolume.

    :param module: AnsibleModule object with the user configuration.
    :param name: Name of the object to remove.
    :param volume_type: Type of the CephFS abstraction ('volume', 'subvolume_group' or 'subvolume').
    :param parent_volume: CephFS volume where this subvolume group or subvolume resides.
    :param parent_group: CephFS subvolume group where this subvolume resides.
    :param size: Size (in bytes) of the CephFS subvolume group or subvolume.
    :return: Tuple of return code, list of command line args, stdout and stderr.
    :rtype: tuple[int, list, str, str]
    """

    create_fs = build_base_cmd_shell(module)
    create_fs.extend(['ceph', 'fs'])

    if volume_type == 'volume':
        placement = module.params.get('initial_placement', None)
        create_fs.extend(['volume', 'create', name, placement])

    elif volume_type == 'subvolume_group':
        # Verify that parent volume exists. Create it if needed.
        rc, cmd, out, err = create_fs_volume(module, parent_volume, 'volume')
        if rc != 0:
            return rc, cmd, out, err

        create_fs.extend(['subvolumegroup', 'create', parent_volume, name, size])

    elif volume_type == 'subvolume':
        # Verify that all parent entities exist. Create them recursively if needed.
        if parent_group:
            rc, cmd, out, err = create_fs_volume(module, parent_group, 'subvolume_group', parent_volume)
        else:
            rc, cmd, out, err = create_fs_volume(module, parent_volume, 'volume')

        if rc != 0:
            return rc, cmd, out, err

        create_fs.extend(['subvolume', 'create', parent_volume, name, size, parent_group])

    return exec_command(module, create_fs)


def get_remove_allowed_flag(module: AnsibleModule) -> bool:
    """
    Retrieve value of the Ceph 'mon_allow_pool_delete' flag that allows removal of Ceph pools.
    Return safe value 'False' if by any meanings cannot get the current value from the cluster.

    :param module: AnsibleModule object with the user configuration.
    :return: Boolean value of the Ceph 'mon_allow_pool_delete' flag.
    """

    removal_allowed = False
    get_flag = build_base_cmd_shell(module)
    get_flag.extend(['ceph', 'config', 'get', 'mon', 'mon_allow_pool_delete', '--format=json'])
    rc, cmd, out, err = exec_command(module, get_flag)
    if rc == 0:
        removal_allowed = json.loads(out)

    return removal_allowed


def set_remove_allowed_flag(
        module: AnsibleModule,
        flag_value: bool
) -> Tuple[int, List[str], str, str]:
    """
    Set the value of the Ceph flag that allows removal of Ceph pools.

    :param module: AnsibleModule object with the user configuration.
    :param flag_value: Boolean value of the 'mon_allow_pool_delete' flag to set.
    :return: Tuple of return code, list of command line args, stdout and stderr.
    """

    set_flag = build_base_cmd_shell(module)
    set_flag.extend(['ceph', 'config', 'set', 'mon', 'mon_allow_pool_delete', str(flag_value)])

    return exec_command(module, set_flag)


def remove_fs_volume(
        module: AnsibleModule,
        name: str,
        volume_type: str,
        parent_volume: str = None,
        parent_group: str = None
) -> Tuple[int, List[str], str, str]:
    """
    Remove the specified Ceph FS volume, subvolume group or subvolume.

    :param module: AnsibleModule object with the user configuration.
    :param name: Name of the object to remove.
    :param volume_type: Type of the CephFS abstraction ('volume', 'subvolume_group' or 'subvolume').
    :param parent_volume: CephFS volume where this subvolume group or subvolume resides.
    :param parent_group: CephFS subvolume group where this subvolume resides.
    :return: Tuple of return code, list of command line args, stdout and stderr.
    """

    # Removal of volume causes removal of pools which is disabled by default.
    removal_allowed = get_remove_allowed_flag(module)

    remove_volume = build_base_cmd_shell(module)
    remove_volume.extend(['ceph', 'fs'])

    if volume_type == 'volume':
        remove_volume.extend(['volume', 'rm', name, '--yes-i-really-mean-it'])

        if not removal_allowed and not module.params['force_remove']:
            return 1, remove_volume, '', ('Error EPERM: pool deletion is disabled; you '
                                          'must first set the mon_allow_pool_delete config '
                                          'option to true before volumes can be deleted')
        elif not removal_allowed and module.params['force_remove']:
            set_remove_allowed_flag(module, True)

    elif volume_type == 'subvolume_group':
        remove_volume.extend(['subvolumegroup', 'rm', parent_volume, name])
    elif volume_type == 'subvolume':
        remove_volume.extend(['subvolume', 'rm', parent_volume, name, parent_group])

    rc, cmd, out, err = exec_command(module, remove_volume)

    # Revert the original value for 'mon_allow_pool_delete'
    # (despite the result of the removal command).
    if volume_type == 'volume':
        set_remove_allowed_flag(module, removal_allowed)

    return rc, cmd, out, err


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            fsid=dict(type='str', required=False),
            image=dict(type='str', required=False),
            name=dict(type='str', required=True),
            initial_placement=dict(type='str', required=False),
            parent_volume=dict(type='str', required=False),
            parent_group=dict(type='str', required=False),
            size=dict(type='int', required=False),
            force_shrink=dict(type='bool', required=False, default=False),
            force_remove=dict(type='bool', required=False, default=False),
            type=dict(type='str', required=False, choices=['volume', 'subvolume', 'subvolume_group'], default='volume'),
            state=dict(type='str', required=False, choices=['present', 'absent'], default='present'),
        ),
        supports_check_mode=True,
        required_if=[
            ('type', 'subvolume_group', ['parent_volume']),
            ('type', 'subvolume', ['parent_volume']),
        ],
    )

    name = module.params.get('name')
    volume_type = module.params.get('type')
    parent_volume = module.params.get('parent_volume', None)
    parent_group = module.params.get('parent_group', None)
    size = module.params.get('size', None)
    state = module.params.get('state')
    changed = False

    str_size = str(size) if size and size > 0 else None

    if module.check_mode:
        module.exit_json(changed=False, stdout='', stderr='', rc=0, start='', end='', delta='')

    startd = datetime.datetime.now()

    rc, cmd, out, err = get_fs_volume(module, name, volume_type, parent_volume, parent_group)

    if state == "present":
        if rc != 0:
            rc, cmd, out, err = create_fs_volume(module, name, volume_type, parent_volume, parent_group, str_size)
            if rc == 0:
                changed = True
        elif need_resize(module, out):
            rc, cmd, out, err = resize_fs_volume(module, name, volume_type, parent_volume, parent_group, str_size)
            if rc == 0:
                changed = True
    elif state == "absent" and rc == 0:
        rc, cmd, out, err = remove_fs_volume(module, name, volume_type, parent_volume, parent_group)
        if rc == 0:
            changed = True

    exit_module(module=module, out=out, rc=rc, cmd=cmd, err=err, startd=startd, changed=changed)


def main():
    run_module()


if __name__ == '__main__':
    main()
