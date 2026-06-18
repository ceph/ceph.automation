========================================
Ceph Automation Collection Release Notes
========================================

.. contents:: Topics

v1.2.0
======

Major Changes
-------------

- Import ceph-ansible modules and fixes unittests

Minor Changes
-------------

- Add ``use_cephadm`` (default ``true``) and ``cluster``, ``ceph_client``, ``keyring`` for running Ceph commands through ``cephadm shell`` or the host ``ceph`` binary; register the ``ceph_cli`` action group for ``module_defaults``; add the ``ceph.automation.ceph_cli`` doc fragment; document usage in the README (https://github.com/ceph/ceph.automation/pull/40).
- ceph_crush_rule - refactored to use ``cephadm shell`` command and added the ability to update CRUSH rules. (https://github.com/ceph/ceph.automation/pull/19).
- ceph_crush_rule_common - not used after the refactor and dropped. (https://github.com/ceph/ceph.automation/pull/19).
- ceph_crush_rule_info - refactored to use ``cephadm shell`` command. (https://github.com/ceph/ceph.automation/pull/19).
- ceph_osd_flag - Added support for specifying a custom user key.
- ceph_pool - Added ability to change the 'min_size' option for Ceph pools. (https://github.com/ceph/ceph.automation/pull/17).

Bugfixes
--------

- ceph_orch_apply - Fixed idempotency check for services that do not require the 'service_id' key in the specification and the 'host' service type (https://github.com/ceph/ceph.automation/pull/12).
- ceph_orch_apply - The fix ensures that the existing orchestrator service is loaded when there are multiple YAML documents returning data for the same service.
- ceph_pool: fix Pep8 error

New Modules
-----------

- ceph_fs_volume - Manage volumes, subvolume groups and subvolumes in Ceph filesystem.
- ceph_fs_volume_info - Query CephFS volumes, subvolume groups and subvolumes information.
