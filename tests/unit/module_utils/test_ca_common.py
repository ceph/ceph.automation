from mock.mock import patch, MagicMock
import os
from ansible_collections.ceph.automation.plugins.module_utils import ceph_common
import pytest

fake_container_binary = 'podman'
fake_container_image = 'docker.io/ceph/daemon:latest'


class TestCommon(object):

    def setup_method(self):
        self.fake_binary = 'ceph'
        self.fake_cluster = 'ceph'
        self.fake_container_cmd = [
            fake_container_binary,
            'run',
            '--rm',
            '--net=host',
            '-v', '/etc/ceph:/etc/ceph:z',
            '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
            '-v', '/var/log/ceph/:/var/log/ceph/:z',
            '--entrypoint=' + self.fake_binary,
            fake_container_image
        ]

    @patch.dict(os.environ, {'CEPH_CONTAINER_BINARY': fake_container_binary})
    def test_container_exec(self):
        cmd = ceph_common.container_exec(self.fake_binary, fake_container_image)
        assert cmd == self.fake_container_cmd

    def test_not_is_containerized(self):
        assert ceph_common.is_containerized() is None

    @patch.dict(os.environ, {'CEPH_CONTAINER_IMAGE': fake_container_image})
    def test_is_containerized(self):
        assert ceph_common.is_containerized() == fake_container_image

    @pytest.mark.parametrize('image', [None, fake_container_image])
    @patch.dict(os.environ, {'CEPH_CONTAINER_BINARY': fake_container_binary})
    def test_pre_generate_cmd(self, image):
        if image:
            expected_cmd = self.fake_container_cmd
        else:
            expected_cmd = [self.fake_binary]

        assert ceph_common.pre_generate_cmd(self.fake_binary, image) == expected_cmd  # noqa: E501

    @pytest.mark.parametrize('image', [None, fake_container_image])
    @patch.dict(os.environ, {'CEPH_CONTAINER_BINARY': fake_container_binary})
    def test_generate_cmd(self, image):
        sub_cmd = ['osd', 'pool']
        args = ['create', 'foo']
        if image:
            expected_cmd = self.fake_container_cmd
        else:
            expected_cmd = [self.fake_binary]

        expected_cmd.extend([
            '-n', 'client.admin',
            '-k', '/etc/ceph/ceph.client.admin.keyring',
            '--cluster',
            self.fake_cluster,
            'osd', 'pool',
            'create', 'foo'
        ])
        assert ceph_common.generate_cmd(sub_cmd=sub_cmd, args=args, cluster=self.fake_cluster, container_image=image) == expected_cmd  # noqa: E501

    @pytest.mark.parametrize('image', [None, fake_container_image])
    @patch.dict(os.environ, {'CEPH_CONTAINER_BINARY': fake_container_binary})
    def test_generate_cmd_different_cluster_name(self, image):
        sub_cmd = ['osd', 'pool']
        args = ['create', 'foo']
        if image:
            expected_cmd = self.fake_container_cmd
        else:
            expected_cmd = [self.fake_binary]

        expected_cmd.extend([
            '-n', 'client.admin',
            '-k', '/etc/ceph/foo.client.admin.keyring',
            '--cluster',
            'foo',
            'osd', 'pool',
            'create', 'foo'
        ])
        result = ceph_common.generate_cmd(sub_cmd=sub_cmd, args=args, cluster='foo', container_image=image)  # noqa: E501
        assert result == expected_cmd

    @pytest.mark.parametrize('image', [None, fake_container_image])
    @patch.dict(os.environ, {'CEPH_CONTAINER_BINARY': fake_container_binary})
    def test_generate_cmd_different_cluster_name_and_user(self, image):
        sub_cmd = ['osd', 'pool']
        args = ['create', 'foo']
        if image:
            expected_cmd = self.fake_container_cmd
        else:
            expected_cmd = [self.fake_binary]

        expected_cmd.extend([
            '-n', 'client.foo',
            '-k', '/etc/ceph/foo.client.foo.keyring',
            '--cluster',
            'foo',
            'osd', 'pool',
            'create', 'foo'
        ])
        result = ceph_common.generate_cmd(sub_cmd=sub_cmd, args=args, cluster='foo', user='client.foo', container_image=image)  # noqa: E501
        assert result == expected_cmd

    @pytest.mark.parametrize('image', [None, fake_container_image])
    @patch.dict(os.environ, {'CEPH_CONTAINER_BINARY': fake_container_binary})
    def test_generate_cmd_different_user(self, image):
        sub_cmd = ['osd', 'pool']
        args = ['create', 'foo']
        if image:
            expected_cmd = self.fake_container_cmd
        else:
            expected_cmd = [self.fake_binary]

        expected_cmd.extend([
            '-n', 'client.foo',
            '-k', '/etc/ceph/ceph.client.foo.keyring',
            '--cluster',
            'ceph',
            'osd', 'pool',
            'create', 'foo'
        ])
        result = ceph_common.generate_cmd(sub_cmd=sub_cmd, args=args, user='client.foo', container_image=image)  # noqa: E501
        assert result == expected_cmd

    @pytest.mark.parametrize('stdin', [None, 'foo'])
    def test_exec_command(self, stdin):
        fake_module = MagicMock()
        rc = 0
        stderr = ''
        stdout = 'ceph version 1.2.3'
        fake_module.run_command.return_value = 0, stdout, stderr
        expected_cmd = [self.fake_binary, '--version']
        _rc, _cmd, _out, _err = ceph_common.exec_command(fake_module, expected_cmd, stdin=stdin)  # noqa: E501
        assert _rc == rc
        assert _cmd == expected_cmd
        assert _err == stderr
        assert _out == stdout
