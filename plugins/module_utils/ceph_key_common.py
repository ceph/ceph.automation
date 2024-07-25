from __future__ import absolute_import, division, print_function
__metaclass__ = type


def exec_commands(module, cmd_list):
    '''
    Execute command(s)
    '''

    for cmd in cmd_list:
        rc, out, err = module.run_command(cmd)
        if rc != 0:
            return rc, cmd, out, err

    return rc, cmd, out, err
