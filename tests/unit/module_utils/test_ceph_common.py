from ansible_collections.ceph.automation.plugins.module_utils.ceph_common import (
    build_base_cmd_orch,
    build_base_cmd_shell,
    fatal,
)
import pytest
from mock.mock import MagicMock


class TestCephCommon(object):
    def setup_method(self):
        self.fake_module = MagicMock()
        self.fake_params = {'foo': 'bar'}
        self.fake_module.params = self.fake_params

    def test_build_base_cmd_orch_with_fsid_arg(self):
        expected_cmd = ['cephadm', 'shell', '--fsid', '123', 'ceph', 'orch']
        self.fake_module.params = {'fsid': '123'}
        cmd = build_base_cmd_orch(self.fake_module)
        assert cmd == expected_cmd

    def test_build_base_cmd_orch_with_image_arg(self):
        expected_cmd = ['cephadm', '--image', 'quay.io/ceph-ci/ceph:main', 'shell', 'ceph', 'orch']
        self.fake_module.params = {'image': 'quay.io/ceph-ci/ceph:main'}
        cmd = build_base_cmd_orch(self.fake_module)
        assert cmd == expected_cmd

    def test_build_base_cmd_orch_with_docker_arg(self):
        expected_cmd = ['cephadm', '--docker', 'shell', 'ceph', 'orch']
        self.fake_module.params = {'docker': True}
        cmd = build_base_cmd_orch(self.fake_module)
        assert cmd == expected_cmd

    def test_build_base_cmd_orch_no_arg(self):
        expected_cmd = ['cephadm', 'shell', 'ceph', 'orch']
        cmd = build_base_cmd_orch(self.fake_module)
        assert cmd == expected_cmd

    def test_build_base_cmd_orch_native_default_keyring(self):
        self.fake_module.params = {'use_cephadm': False}
        expected_cmd = [
            'ceph', '-n', 'client.admin', '-k', '/etc/ceph/ceph.client.admin.keyring',
            '--cluster', 'ceph', 'orch',
        ]
        cmd = build_base_cmd_orch(self.fake_module)
        assert cmd == expected_cmd

    def test_build_base_cmd_shell_native_custom_cluster(self):
        self.fake_module.params = {
            'use_cephadm': False,
            'cluster': 'foo',
            'ceph_client': 'client.admin',
            'keyring': '/etc/ceph/custom.keyring',
        }
        expected_cmd = [
            'ceph', '-n', 'client.admin', '-k', '/etc/ceph/custom.keyring',
            '--cluster', 'foo',
        ]
        cmd = build_base_cmd_shell(self.fake_module)
        assert cmd == expected_cmd

    def test_fatal(self):
        fatal("error", self.fake_module)
        self.fake_module.fail_json.assert_called_with(msg='error', rc=1)
        with pytest.raises(Exception):
            fatal("error", False)
