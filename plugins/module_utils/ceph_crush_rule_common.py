from __future__ import absolute_import, division, print_function
__metaclass__ = type


try:
    from ansible_collections.ceph.automation.plugins.module_utils.ceph_common import generate_cmd
except ImportError:
    from module_utils.ceph_common import generate_cmd


def get_rule(module, container_image=None):
    '''
    Get existing crush rule
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')

    args = ['dump', name, '--format=json']

    cmd = generate_cmd(sub_cmd=['osd', 'crush', 'rule'],
                       args=args,
                       cluster=cluster,
                       container_image=container_image)

    return cmd
