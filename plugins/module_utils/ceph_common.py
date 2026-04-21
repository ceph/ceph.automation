from __future__ import absolute_import, division, print_function
__metaclass__ = type

import datetime
import os
import time
from typing import TYPE_CHECKING, Any, List, Dict, Callable, Type, TypeVar, Optional

CEPH_CLI_SHARED_OPTIONS = dict(
    use_cephadm=dict(type='bool', required=False, default=True),
    cluster=dict(type='str', required=False, default='ceph'),
    ceph_client=dict(type='str', required=False, default='client.admin'),
    keyring=dict(type='str', required=False, default=None, no_log=True),
)

if TYPE_CHECKING:
    from ansible.module_utils.basic import AnsibleModule  # type: ignore

ExceptionType = TypeVar('ExceptionType', bound=BaseException)


def generate_cmd(cmd='ceph',
                 sub_cmd=None,
                 args=None,
                 user_key=None,
                 cluster='ceph',
                 user='client.admin',
                 container_image=None,
                 interactive=False):
    '''
    Generate 'ceph' command line to execute
    '''

    if user_key is None:
        user_key = '/etc/ceph/{}.{}.keyring'.format(cluster, user)

    cmd = pre_generate_cmd(cmd, container_image=container_image, interactive=interactive)  # noqa: E501

    base_cmd = [
        '-n',
        user,
        '-k',
        user_key,
        '--cluster',
        cluster
    ]

    if sub_cmd is not None:
        base_cmd.extend(sub_cmd)

    cmd.extend(base_cmd) if args is None else cmd.extend(base_cmd + args)

    return cmd


def container_exec(binary, container_image, interactive=False):
    '''
    Build the docker CLI to run a command inside a container
    '''

    container_binary = os.getenv('CEPH_CONTAINER_BINARY')
    command_exec = [container_binary, 'run']

    if interactive:
        command_exec.extend(['--interactive'])

    command_exec.extend(['--rm',
                         '--net=host',
                         '-v', '/etc/ceph:/etc/ceph:z',
                         '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
                         '-v', '/var/log/ceph/:/var/log/ceph/:z',
                         '--entrypoint=' + binary, container_image])
    return command_exec


def is_containerized():
    '''
    Check if we are running on a containerized cluster
    '''

    if 'CEPH_CONTAINER_IMAGE' in os.environ:
        container_image = os.getenv('CEPH_CONTAINER_IMAGE')
    else:
        container_image = None

    return container_image


def pre_generate_cmd(cmd, container_image=None, interactive=False):
    '''
    Generate ceph prefix command
    '''
    if container_image:
        cmd = container_exec(cmd, container_image, interactive=interactive)
    else:
        cmd = [cmd]

    return cmd


def exec_command(module, cmd, stdin=None, check_rc=False):
    '''
    Execute command(s)
    '''

    binary_data = False
    if stdin:
        binary_data = True
    rc, out, err = module.run_command(cmd, data=stdin, binary_data=binary_data, check_rc=check_rc)  # noqa: E501

    return rc, cmd, out, err


def retry(exceptions: Type[ExceptionType], module: "AnsibleModule", retries: int = 20, delay: int = 1) -> Callable:
    def decorator(f: Callable) -> Callable:
        def _retry(*args: Any, **kwargs: Any) -> Callable:
            _tries = retries
            while _tries > 1:
                try:
                    module.debug(_tries)
                    return f(*args, **kwargs)
                except exceptions:
                    time.sleep(delay)
                    _tries -= 1
            module.debug(f, " has failed after ", retries, " retries")
            return f(*args, **kwargs)
        return _retry
    return decorator


def module_use_cephadm(module: "AnsibleModule") -> bool:
    '''
    Resolve whether to run Ceph through cephadm shell or the host ceph binary (default true).
    '''
    params = getattr(module, 'params', None) or {}
    return bool(params.get('use_cephadm', True))


def build_native_ceph_prefix(module: "AnsibleModule") -> List[str]:
    '''
    Build ceph with cluster authentication for non-Cephadm hosts.
    '''
    cluster = module.params.get('cluster') or 'ceph'
    ceph_client = module.params.get('ceph_client') or 'client.admin'
    keyring = module.params.get('keyring')
    if not keyring:
        keyring = '/etc/ceph/{}.{}.keyring'.format(cluster, ceph_client)
    return ['ceph', '-n', ceph_client, '-k', keyring, '--cluster', cluster]


def append_shell_ceph_subargs(module: "AnsibleModule", cmd: List[str], argv: List[str]) -> None:
    '''
    Append arguments to ceph in cephadm shell ceph ...,
    or follow the host ceph when use_cephadm is false.

    :param argv: e.g. ['config', 'set', 'mon', 'foo', 'bar'] without a leading ceph.
    '''
    if module_use_cephadm(module):
        cmd.extend(['ceph'] + argv)
    else:
        cmd.extend(argv)


def append_cephadm_shell_tmpdir_mount(module: "AnsibleModule", cmd: List[str], tmpdirname: str) -> None:
    '''
    Append cephadm shell --mount options so a host temp directory is visible in the container.
    No-op when use_cephadm is false.
    '''
    if not module_use_cephadm(module):
        return
    cmd.extend(['--mount', '{0}:{0}'.format(tmpdirname), '--'])


def build_base_cmd(module: "AnsibleModule") -> List[str]:
    if not module_use_cephadm(module):
        module.fail_json(
            msg='This module only supports Cephadm. Set use_cephadm to true or use a different module.'
        )
    cmd = ['cephadm']
    docker = module.params.get('docker')
    image = module.params.get('image')

    if docker:
        cmd.append('--docker')
    if image:
        cmd.extend(['--image', image])

    return cmd


def build_base_cmd_shell(module: "AnsibleModule") -> List[str]:
    if module_use_cephadm(module):
        cmd = build_base_cmd(module)
        fsid = module.params.get('fsid')

        cmd.append('shell')

        if fsid:
            cmd.extend(['--fsid', fsid])

        return cmd
    return build_native_ceph_prefix(module)


def build_base_cmd_orch(module: "AnsibleModule") -> List[str]:
    cmd = build_base_cmd_shell(module)
    append_shell_ceph_subargs(module, cmd, ['orch'])
    return cmd


def exit_module(module: "AnsibleModule",
                rc: int, cmd: List[str],
                startd: datetime.datetime,
                out: str = '',
                err: str = '',
                changed: bool = False,
                diff: Optional[Dict[str, str]] = None) -> None:
    endd = datetime.datetime.now()
    delta = endd - startd

    result = dict(
        cmd=cmd,
        start=str(startd),
        end=str(endd),
        delta=str(delta),
        rc=rc,
        stdout=out.rstrip("\r\n"),
        stderr=err.rstrip("\r\n"),
        changed=changed,
        diff=diff
    )
    module.exit_json(**result)


def fatal(message: str, module: "AnsibleModule") -> None:
    '''
    Report a fatal error and exit
    '''

    if module:
        module.fail_json(msg=message, rc=1)
    else:
        raise Exception(message)
