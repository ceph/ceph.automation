#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright Red Hat
# SPDX-License-Identifier: Apache-2.0
# Author: Guillaume Abrioux <gabrioux@redhat.com>
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
module: ceph_orch_apply
short_description: apply service spec
version_added: "1.0.0"
description:
    - Manage and apply service specifications.
    - This module is designed to apply a single service specification per execution.
    - Multiple service specifications can be applied by using a loop.
    - If any default key in the service specification is missing, the module will indicate a changed status.
    - To prevent unnecessary changes, ensure all keys with their default values are included in the service specification.
options:
    fsid:
        description:
            - the fsid of the Ceph cluster to interact with.
        type: str
        required: false
    image:
        description:
            - The Ceph container image to use.
        type: str
        required: false
    docker:
        description:
            - Use docker instead of podman
        type: bool
        required: false
        default: false
    spec:
        description:
            - The service spec to apply
        type: str
        required: true
author:
    - Guillaume Abrioux (@guits)
'''

EXAMPLES = '''
- name: apply cluster spec
  ceph.automation.ceph_orch_apply:
    spec: "{{ item }}"
  loop:
    - service_type: "nfs"
      service_id: "iac"
      placement:
        count: 1
        label: "nfs"
      spec:
        port: 5001
    - service_type: "ingress"
      service_id: "nfs.iac"
      placement:
        count: 1
        label: "nfs"
      spec:
        backend_service: "nfs.iac"
        first_virtual_router_id: 51
        frontend_port: 2049
        monitor_port: 9001
        virtual_ip: "172.16.20.11/24"
'''

RETURN = '''#  '''

import traceback
from ansible.module_utils.basic import missing_required_lib
try:
    import yaml
except ImportError:
    HAS_ANOTHER_LIBRARY = False
    ANOTHER_LIBRARY_IMPORT_ERROR = traceback.format_exc()
else:
    HAS_ANOTHER_LIBRARY = True
    ANOTHER_LIBRARY_IMPORT_ERROR = None

from typing import List, Tuple, Dict
import datetime

from ansible.module_utils.basic import AnsibleModule  # type: ignore
try:
    from ansible_collections.ceph.automation.plugins.module_utils.ceph_common import exit_module, build_base_cmd_orch  # type: ignore
except ImportError:
    from module_utils.ceph_common import exit_module, build_base_cmd_orch


def parse_spec(spec: str) -> Dict:
    """ parse spec string to yaml """
    yaml_spec = yaml.safe_load(spec)
    return yaml_spec


def retrieve_current_spec(module: AnsibleModule, expected_spec: Dict) -> Dict:
    """ retrieve current config of the service """
    service: str = expected_spec["service_type"]
    # Key "service_id" is mandatory only for exact subset of services.
    # https://docs.ceph.com/en/latest/cephadm/services/#ceph.deployment.service_spec.ServiceSpec.service_id
    if service in ["iscsi", "nvmeof", "mds", "nfs", "osd", "rgw", "container", "ingress"]:
        srv_name: str = "%s.%s" % (service, expected_spec["service_id"])
    else:
        srv_name: str = service
    cmd = build_base_cmd_orch(module)
    # Hosts are not services but can be deployed with `ceph orch apply` like regular services.
    # And `ceph orch` has different syntax to list hosts.
    if service != "host":
        cmd.extend(['ls', service, srv_name, '--format=yaml'])
    else:
        cmd.extend(['host', 'ls', '--host-pattern', expected_spec['hostname'], '--format=yaml'])
    out = module.run_command(cmd)
    if isinstance(out, str):
        # if there is no existing service, cephadm returns the string 'No services reported'
        return {}
    else:
        return yaml.safe_load(out[1])


def apply_spec(module: "AnsibleModule",
               data: str) -> Tuple[int, List[str], str, str]:
    cmd = build_base_cmd_orch(module)
    cmd.extend(['apply', '-i', '-'])
    rc, out, err = module.run_command(cmd, data=data)

    if rc:
        raise RuntimeError(err)

    return rc, cmd, out, err


def change_required(current: Dict, expected: Dict) -> bool:
    """ checks if the current config differs from what is expected """
    if not current:
        return True

    # Listing of hosts never returns 'service_type', but expected spec has it.
    if expected['service_type'] == 'host':
        current['service_type'] = 'host'

    for key, value in expected.items():
        if key in current:
            if current[key] != value:
                return True
            continue
        else:
            # "Location" key in the host spec is a one-time use key - it is not stored in the database.
            # This key should not appear in the "current" spec, and it is safe to skip this key.
            if key != 'location':
                return True
    return False


def run_module() -> None:

    module_args = dict(
        spec=dict(type='str', required=True),
        fsid=dict(type='str', required=False),
        docker=dict(type='bool',
                    required=False,
                    default=False),
        image=dict(type='str', required=False)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if not HAS_ANOTHER_LIBRARY:
        module.fail_json(
            msg=missing_required_lib('another_library'),
            exception=ANOTHER_LIBRARY_IMPORT_ERROR)

    startd = datetime.datetime.now()
    spec = module.params.get('spec')

    if module.check_mode:
        exit_module(
            module=module,
            out='',
            rc=0,
            cmd=[],
            err='',
            startd=startd,
            changed=False
        )

    # Idempotency check
    expected = parse_spec(module.params.get('spec'))
    current_spec = retrieve_current_spec(module, expected)

    if change_required(current_spec, expected):
        rc, cmd, out, err = apply_spec(module, spec)
        changed = True
    else:
        rc = 0
        cmd = []
        out = ''
        err = ''
        changed = False

    exit_module(
        module=module,
        out=out,
        rc=rc,
        cmd=cmd,
        err=err,
        startd=startd,
        changed=changed
    )


def main() -> None:
    run_module()


if __name__ == '__main__':
    main()
