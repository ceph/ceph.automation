from ansible_collections.ceph.automation.plugins.module_utils.ceph_fs_volume_common import \
    list_fs_volumes, get_fs_volume
from mock.mock import MagicMock

module_args = dict(
    fsid=dict(type='str', required=False),
    image=dict(type='str', required=False),
)
fake_volume = 'vol01'
fake_subvolume_group = 'vol01-gr01'
fake_subvolume = 'vol01-gr01-sub01'


class TestCephFsVolumeCommon(object):
    def setup_method(self):
        self.fake_module = MagicMock()
        self.fake_params = {'foo': 'bar'}
        self.fake_module.params = self.fake_params
        self.rcode = 0
        self.stderr = ''

    def test_list_fs_volumes(self):
        stdout = '[{{"name":"{}"}}]'.format(fake_volume)
        self.fake_module.run_command.return_value = self.rcode, stdout, self.stderr

        expected_cmd = ['cephadm', 'shell', 'ceph', 'fs', 'volume', 'ls', '--format=json']

        result = list_fs_volumes(self.fake_module)
        assert result[0] == self.rcode
        assert result[1] == expected_cmd
        assert result[2] == stdout
        assert result[3] == self.stderr

    def test_list_fs_subvolume_groups(self):
        stdout = '[{{"name":"{}"}}]'.format(fake_subvolume_group)
        self.fake_module.run_command.return_value = self.rcode, stdout, self.stderr

        expected_cmd = [
            'cephadm', 'shell', 'ceph', 'fs', 'subvolumegroup', 'ls', fake_volume, '--format=json'
        ]

        result = list_fs_volumes(
            module=self.fake_module,
            volume_type='subvolume_group',
            parent_volume=fake_volume,
        )
        assert result[0] == self.rcode
        assert result[1] == expected_cmd
        assert result[2] == stdout
        assert result[3] == self.stderr

    def test_list_fs_subvolumes(self):
        stdout = '[{{"name":"{}"}}]'.format(fake_subvolume)
        self.fake_module.run_command.return_value = self.rcode, stdout, self.stderr

        expected_cmd = [
            'cephadm', 'shell', 'ceph', 'fs', 'subvolume',
            'ls', fake_volume, fake_subvolume_group, '--format=json'
        ]

        result = list_fs_volumes(
            self.fake_module,
            volume_type='subvolume',
            parent_volume=fake_volume,
            parent_group=fake_subvolume_group,
        )
        assert result[0] == self.rcode
        assert result[1] == expected_cmd
        assert result[2] == stdout
        assert result[3] == self.stderr

    def test_get_fs_volume(self):
        stdout = ('{{"mon_addrs": "endpoint_list",'
                  '"pools":{{"data":[{{"name":"cephfs.{vol}.data"}}],'
                  '"metadata":[{{"name":"cephfs.{vol}.meta"]}}}}').format(vol=fake_volume)
        self.fake_module.run_command.return_value = self.rcode, stdout, self.stderr

        expected_cmd = ['cephadm', 'shell', 'ceph', 'fs', 'volume', 'info', fake_volume, '--format=json']
        result = get_fs_volume(
            self.fake_module,
            volume_type='volume',
            name=fake_volume,
            parent_volume=None,
            parent_group=None,
        )
        assert result[0] == self.rcode
        assert result[1] == expected_cmd
        assert result[2] == stdout
        assert result[3] == self.stderr

    def test_get_fs_subvolume_group(self):
        stdout = ('{{"atime":"","bytes_pcent":"1.52","bytes_quota":9000,"bytes_used":137,'
                  '"created_at":"","ctime":"","data_pool":"cephfs.{0}.data",'
                  '"gid":0,"mode":16877,"mtime":"","uid":0}}').format(fake_volume)
        self.fake_module.run_command.return_value = self.rcode, stdout, self.stderr

        expected_cmd = [
            'cephadm', 'shell', 'ceph', 'fs', 'subvolumegroup',
            'info', fake_volume, fake_subvolume_group, '--format=json'
        ]

        result = get_fs_volume(
            self.fake_module,
            volume_type='subvolume_group',
            name=fake_subvolume_group,
            parent_volume=fake_volume,
            parent_group=None,
        )
        assert result[0] == self.rcode
        assert result[1] == expected_cmd
        assert result[2] == stdout
        assert result[3] == self.stderr

    def test_get_fs_subvolume(self):
        stdout = ('{{"atime":"","bytes_pcent":"0.00","bytes_quota":18000,"bytes_used":0,'
                  '"created_at":"","ctime":"","data_pool":"cephfs.{}.data","earmark":"",'
                  '"path":"/volumes/{}/{}/UUID","pool_namespace":"","state":"complete",'
                  '"type":"subvolume","uid":0}}').format(fake_volume, fake_subvolume_group, fake_subvolume)
        self.fake_module.run_command.return_value = self.rcode, stdout, self.stderr

        expected_cmd = [
            'cephadm', 'shell', 'ceph', 'fs', 'subvolume',
            'info', fake_volume, fake_subvolume, fake_subvolume_group, '--format=json'
        ]

        result = get_fs_volume(
            self.fake_module,
            volume_type='subvolume',
            name=fake_subvolume,
            parent_volume=fake_volume,
            parent_group=fake_subvolume_group,
        )
        assert result[0] == self.rcode
        assert result[1] == expected_cmd
        assert result[2] == stdout
        assert result[3] == self.stderr
