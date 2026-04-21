# -*- coding: utf-8 -*-
# Copyright Red Hat
# SPDX-License-Identifier: Apache-2.0

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class ModuleDocFragment(object):

    DOCUMENTATION = r'''
options:
  use_cephadm:
    description:
      - When true (default), run the Ceph CLI through Cephadm shell (``cephadm shell ceph ...``).
      - When false, run the ``ceph`` binary on the target host with keyring authentication
        (for example Proxmox or other non-Cephadm clusters).
      - May be set for all modules in ``group/ceph.automation.ceph_cli`` via ``module_defaults``.
    type: bool
    default: true
    version_added: '1.2.0'
  cluster:
    description:
      - Ceph cluster name used with the native ``ceph`` CLI when ``use_cephadm`` is false.
    type: str
    default: ceph
    version_added: '1.2.0'
  ceph_client:
    description:
      - Ceph client name (``-n``) for the native ``ceph`` CLI when ``use_cephadm`` is false.
    type: str
    default: client.admin
    version_added: '1.2.0'
  keyring:
    description:
      - Path to the keyring file for the native ``ceph`` CLI when ``use_cephadm`` is false.
      - Defaults to ``/etc/ceph/<cluster>.<ceph_client>.keyring``.
    type: str
    required: false
    version_added: '1.2.0'
'''
