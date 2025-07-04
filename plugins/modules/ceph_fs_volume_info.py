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

DOCUMENTATION = r"""
module: ceph_fs_volume_info
short_description: Query CephFS volumes, subvolume groups and subvolumes information.
version_added: "1.2.0"
description:
    - Retrieve information about volumes in the Ceph cluster.
    - Query can be recursive to get information about all existent volumes, subvolume groups and subvolumes.
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
    recurse:
        description:
            - Controls whether to recurse into volumes and gather information about
              all contained subvolume groups and subvolumes.
        type: bool
        required: false
        default: false
author:
    - Castor Sky (@castorsky) <csky57@gmail.com>
"""

EXAMPLES = r"""
- name: Get info about volumes in the Ceph cluster
  ceph.automation.ceph_fs_volume_info:
  register: volumes_info

- name: Display the name of the first data pool for volume 'vol01'
  ansible.builtin.debug:
    msg: >
      {{ volumes_info['volumes'] | selectattr('name', 'equalto', 'vol01') |
      map(attribute='pools') | map(attribute='data') |
      first | map(attribute='name') }}

- name: Get info about volumes and all their descendants
  ceph.automation.ceph_fs_volume_info:
    recurse: true
  register: volumes_info
"""

RETURN = r"""
# In addition to common values for this collection (rc, cmd, out, err) this module returns:
# (Some fields returned by Ceph CLI omitted.)
volumes:
    description: List of volumes found in the Ceph cluster.
    type: list
    elements: dict
    returned: always
    contains:
        name:
            description: Name of the volume.
            type: str
            sample: "vol01"
            returned: always
        pools:
            description: Dict with information about data and metadata pools.
            type: dict
            elements: dict
            returned: always
        subvolumes:
            description: List of subvolumes contained in the volume directly (without subvolume groups).
            type: list
            elements: dict
            returned: When O(recurse=true) is specified.
            contains:
                name:
                    description: Name of the subvolume.
                    type: str
                    sample: "vol03-nogr-sub01"
                path:
                    description: Full path to the subvolume that can be used for mounting on the client side.
                    type: str
                    sample: "/volumes/_nogroup/vol03-nogr-sub01/c6b831cb-f264-46f6-a810-5646f245e4eb"
                data_pool:
                    description: Subvolume groups stores data in this data pool.
                    type: str
                    sample: "cephfs.vol03.data"
                bytes_quota:
                    description: Size of the subvolume (quota) in bytes.
                    type: int
                    sample: 2048
                bytes_used:
                    description: Size of the occupied space in the subvolume in bytes.
                    type: int
                    sample: 1024
        subvolume_groups:
            description: List of subvolume groups contained in the volume.
            type: list
            elements: dict
            returned: When O(recurse=true) is specified.
            contains:
                name:
                    description: Name of the subvolume group.
                    type: str
                    sample: "vol01-gr01"
                data_pool:
                    description: Subvolume groups stores data in this data pool.
                    type: str
                    sample: "cephfs.vol01.data"
                bytes_quota:
                    description: Size of the subvolume group (quota) in bytes.
                    type: int
                    sample: 2048
                bytes_used:
                    description: Size of the occupied space in the subvolume group in bytes.
                    type: int
                    sample: 1024
                subvolumes:
                    description: List of subvolumes contained in the subvolume group.
                    type: list
                    elements: dict
                    sample: see sample for subvolumes above (volumes/subvolumes)
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from ansible_collections.ceph.automation.plugins.module_utils.ceph_common import exit_module
    from ansible_collections.ceph.automation.plugins.module_utils.ceph_fs_volume_common import \
        list_fs_volumes, get_fs_volume
except ImportError:
    from module_utils.ceph_common import exit_module
    from module_utils.ceph_fs_volume_common import list_fs_volumes, get_fs_volume

import datetime
import json
from typing import Tuple, List, Callable, Any


def get_descendants_info(
        module: AnsibleModule,
        lister_func: Callable,
        getter_func: Callable,
        descendant_type: str = 'volume',
        parent_volume: str = None,
        parent_group: str = None) -> Tuple[List[Any], int, List[str], str, str]:
    """
    List volumes, subvolume groups or subvolumes inside specified parent volume and/or group.

    :param module: AnsibleModule object with the user configuration.
    :param lister_func: Function used to list volumes.
    :param getter_func: Function used to get object information.
    :param descendant_type: Type of the CephFS abstraction ('volume', 'subvolume_group' or 'subvolume').
    :param parent_volume: CephFS volume where this subvolume group or subvolume resides.
    :param parent_group: CephFS subvolume group where this subvolume resides.
    :param size: Size of the CephFS subvolume group or subvolume (bytes).
    :return: Tuple of found objects, return code, list of command line args, stdout and stderr.
    """

    # List descendants under this object.
    descendant_list = []
    rc, cmd, out, err = lister_func(module, descendant_type, parent_volume, parent_group)
    if rc == 0:
        descendant_list.extend(json.loads(out))

    if len(descendant_list) > 0:
        for descendant in descendant_list:
            # Get info about this descendant
            rc, cmd, out, err = getter_func(module, descendant['name'], descendant_type, parent_volume, parent_group)
            if rc == 0:
                descendant.update(json.loads(out))
            else:
                break

    return descendant_list, rc, cmd, out, err


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            fsid=dict(type='str', required=False),
            image=dict(type='str', required=False),
            recurse=dict(type='bool', required=False, default=False),
        ),
        supports_check_mode=True,
    )
    changed = False

    recurse = module.params.get('recurse')
    startd = datetime.datetime.now()

    volume_list, rc, cmd, out, err = get_descendants_info(
        module=module,
        lister_func=list_fs_volumes,
        getter_func=get_fs_volume,
    )
    if rc != 0:
        exit_module(module=module, out=out, rc=rc, cmd=cmd, err=err,
                    startd=startd, changed=changed)

    if recurse:
        for volume in volume_list:
            subvolume_list, rc, cmd, out, err = get_descendants_info(
                module=module,
                lister_func=list_fs_volumes,
                getter_func=get_fs_volume,
                descendant_type='subvolume',
                parent_volume=volume['name'],
            )
            if rc != 0:
                exit_module(module=module, out=out, rc=rc, cmd=cmd, err=err,
                            startd=startd, changed=changed)
            volume['subvolumes'] = subvolume_list

            group_list, rc, cmd, out, err = get_descendants_info(
                module=module,
                lister_func=list_fs_volumes,
                getter_func=get_fs_volume,
                descendant_type='subvolume_group',
                parent_volume=volume['name'],
            )
            if rc != 0:
                exit_module(module=module, out=out, rc=rc, cmd=cmd, err=err,
                            startd=startd, changed=changed)

            if len(group_list) > 0:
                for group in group_list:
                    # List subvolumes under this group
                    subgroup_volume_list, rc, cmd, out, err = get_descendants_info(
                        module=module,
                        lister_func=list_fs_volumes,
                        getter_func=get_fs_volume,
                        descendant_type='subvolume',
                        parent_volume=volume['name'],
                        parent_group=group['name'],
                    )
                    if rc != 0:
                        exit_module(module=module, out=out, rc=rc, cmd=cmd, err=err,
                                    startd=startd, changed=changed)
                    group['subvolumes'] = subgroup_volume_list

            volume['subvolume_groups'] = group_list

    # Copypaste from the 'ceph_fs_volume_common' to add one returned argument - 'volumes'
    endd = datetime.datetime.now()
    delta = endd - startd
    result = dict(
        start=str(startd),
        end=str(endd),
        delta=str(delta),
        stdout=out.rstrip("\r\n"),
        stderr=err.rstrip("\r\n"),
        changed=changed,
        volumes=volume_list,
    )
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
