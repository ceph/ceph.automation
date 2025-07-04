from __future__ import absolute_import, division, print_function, annotations

__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule

try:
    from ansible_collections.ceph.automation.plugins.module_utils.ceph_common import \
        exec_command, build_base_cmd_shell
except ImportError:
    from module_utils.ceph_common import exec_command, build_base_cmd_shell

from typing import List, Tuple, Union


def list_fs_volumes(
        module: AnsibleModule,
        volume_type: str = 'volume',
        parent_volume: Union[str, None] = None,
        parent_group: Union[str, None] = None
) -> Tuple[int, List[str], str, str]:
    """
    List all existent volumes of the specified type (and optionally parents) in the Ceph cluster.

    :param module: AnsibleModule object with the user configuration.
    :param volume_type: Type of the CephFS abstraction ('volume', 'subvolume_group' or 'subvolume').
    :param parent_volume: CephFS volume where this subvolume group or subvolume resides.
    :param parent_group: CephFS subvolume group where this subvolume resides.
    :return: Tuple of return code, list of command line args, stdout and stderr.
    """

    list_fs = build_base_cmd_shell(module)
    list_fs.extend(['ceph', 'fs'])

    if volume_type == 'volume':
        list_fs.extend(['volume', 'ls', '--format=json'])
    elif volume_type == 'subvolume_group':
        list_fs.extend(['subvolumegroup', 'ls', parent_volume, '--format=json'])
    elif volume_type == 'subvolume':
        list_fs.extend(['subvolume', 'ls', parent_volume, parent_group, '--format=json'])

    return exec_command(module, list_fs)


def get_fs_volume(
        module: AnsibleModule,
        name: str,
        volume_type: str,
        parent_volume: Union[str, None],
        parent_group: Union[str, None]
) -> Tuple[int, List[str], str, str]:
    """
    Get info about the specified Ceph FS volume, subvolume group or subvolume.

    :param module: AnsibleModule object with the user configuration.
    :param name: Name of the object to remove.
    :param volume_type: Type of the CephFS abstraction ('volume', 'subvolume_group' or 'subvolume').
    :param parent_volume: CephFS volume where this subvolume group or subvolume resides.
    :param parent_group: CephFS subvolume group where this subvolume resides.
    :return: Tuple of return code, list of command line args, stdout and stderr.
    """

    get_fs = build_base_cmd_shell(module)
    get_fs.extend(['ceph', 'fs'])

    if volume_type == 'volume':
        get_fs.extend(['volume', 'info', name, '--format=json'])
    elif volume_type == 'subvolume_group':
        get_fs.extend(['subvolumegroup', 'info', parent_volume, name, '--format=json'])
    elif volume_type == 'subvolume':
        get_fs.extend(['subvolume', 'info', parent_volume, name, parent_group, '--format=json'])

    return exec_command(module, get_fs)
