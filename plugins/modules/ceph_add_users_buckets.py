#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2018, Red Hat, Inc.
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
module: ceph_add_users_buckets
short_description: bulk create user and buckets
version_added: "1.1.0"
description:
    - Bulk create Ceph Object Storage users and buckets
options:
    rgw_host:
        description:
            - a radosgw host in the ceph cluster
        type: str
        required: true
    port:
        description:
            - tcp port of the radosgw host
        type: int
        required: true
    is_secure:
        description:
            - boolean indicating whether the instance is running over https
        type: bool
        required: false
        default: false
    admin_access_key:
        description:
            - radosgw admin user's access key
        type: str
        required: true
    admin_secret_key:
        description:
            - radosgw admin user's secret key
        type: str
        required: true
    users:
        description:
            - list of users to be created containing sub options
        type: list
        elements: dict
        required: false
        suboptions:
            username:
                description:
                    - username for new user
                required: true
                type: str
            fullname:
                description:
                    - fullname for new user
                type: str
                required: true
            email:
                description:
                    - email for new user
                type: str
                required: false
            maxbucket:
                description:
                    - max bucket for new user
                type: int
                required: false
                default: 1000
            suspend:
                description:
                    - suspend a new user apon creation
                type: bool
                required: false
                default: false
            autogenkey:
                description:
                    - auto generate keys for new user
                type: bool
                required: false
                default: true
            accesskey:
                description:
                    - access key for new user
                type: str
                required: false
            secretkey:
                description:
                    - secret key for new user
                type: str
                required: false
            userquota:
                description:
                    - enable/disable user quota for new user
                type: bool
                required: false
                default: false
            usermaxsize:
                description:
                    - with user quota enabled specify quota size in kb
                type: str
                required: false
                default: '-1'
            usermaxobjects:
                description:
                    - with user quota enabled specify maximum number of objects
                type: int
                required: false
                default: -1
            bucketquota:
                description:
                    - enable/disable bucket quota for new user
                type: bool
                required: false
                default: false
            bucketmaxsize:
                description:
                    - with bucket quota enabled specify bucket size in kb
                type: str
                required: false
                default: '-1'
            bucketmaxobjects:
                description:
                    - with bucket quota enabled specify maximum number of objects  # noqa: E501
                type: int
                required: false
                default: -1
    buckets:
        description:
            - list of buckets to be created containing sub options
        type: list
        elements: dict
        required: false
        suboptions:
            bucket:
                description:
                    - name for new bucket
                type: str
                required: true
            user:
                description:
                    - user new bucket will be linked too
                type: str
                required: true


requirements: ['radosgw', 'boto']

author:
    - Daniel Pivonka (@Daniel-Pivonka)

'''

EXAMPLES = '''
# single basic user
- name: single basic user
  ceph_add_users_buckets:
    rgw_host: '172.16.0.12'
    port: 8080
    admin_access_key: 'N61I8625V4XTWGDTLBLL'
    admin_secret_key: 'HZrkuHHO9usUurDWBQHTeLIjO325bIULaC7DxcoV'
    users:
      - username: 'test1'
        fullname: 'tester'


# single complex user
- name: single complex user
  ceph_add_users_buckets:
    rgw_host: '172.16.0.12'
    port: 8080
    admin_access_key: 'N61I8625V4XTWGDTLBLL'
    admin_secret_key: 'HZrkuHHO9usUurDWBQHTeLIjO325bIULaC7DxcoV'
    users:
      - username: 'test1'
        fullname: 'tester'
        email: 'dan@email.com'
        maxbucket: 666
        suspend: true
        autogenkey: true
        accesskey: 'B3AR4Q33L59YV56A9A2F'
        secretkey: 'd84BRnMysnVGSyZiRlYUMduVgIarQWiNMdKzrF76'
        userquota: true
        usermaxsize: '1000'
        usermaxobjects: 3
        bucketquota: true
        bucketmaxsize: '1000'
        bucketmaxobjects: 3

# multi user
- name: multi user
  ceph_add_users_buckets:
    rgw_host: '172.16.0.12'
    port: 8080
    admin_access_key: 'N61I8625V4XTWGDTLBLL'
    admin_secret_key: 'HZrkuHHO9usUurDWBQHTeLIjO325bIULaC7DxcoV'
    users:
      - username: 'test1'
        fullname: 'tester'
        email: 'dan@email.com'
        maxbucket: 666
        suspend: true
        autogenkey: true
        accesskey: 'B3AR4Q33L59YV56A9A2F'
        secretkey: 'd84BRnMysnVGSyZiRlYUMduVgIarQWiNMdKzrF76'
        userquota: true
        usermaxsize: '1000K'
        usermaxobjects: 3
        bucketquota: true
        bucketmaxsize: '1000K'
        bucketmaxobjects: 3
      - username: 'test2'
        fullname: 'tester'

# single bucket
- name: single basic user
  ceph_add_users_buckets:
    rgw_host: '172.16.0.12'
    port: 8080
    admin_access_key: 'N61I8625V4XTWGDTLBLL'
    admin_secret_key: 'HZrkuHHO9usUurDWBQHTeLIjO325bIULaC7DxcoV'
    buckets:
      - bucket: 'heyimabucket1'
        user: 'test1'

# multi bucket
- name: single basic user
  ceph_add_users_buckets:
    rgw_host: '172.16.0.12'
    port: 8080
    admin_access_key: 'N61I8625V4XTWGDTLBLL'
    admin_secret_key: 'HZrkuHHO9usUurDWBQHTeLIjO325bIULaC7DxcoV'
    buckets:
      - bucket: 'heyimabucket1'
        user: 'test1'
      - bucket: 'heyimabucket2'
        user: 'test2'
      - bucket: 'heyimabucket3'
        user: 'test2'

# buckets and users
- name: single basic user
  ceph_add_users_buckets:
    rgw_host: '172.16.0.12'
    port: 8080
    admin_access_key: 'N61I8625V4XTWGDTLBLL'
    admin_secret_key: 'HZrkuHHO9usUurDWBQHTeLIjO325bIULaC7DxcoV'
    users:
      - username: 'test1'
        fullname: 'tester'
        email: 'dan@email.com'
        maxbucket: 666
      - username: 'test2'
        fullname: 'tester'
        email: 'dan1@email.com'
        accesskey: 'B3AR4Q33L59YV56A9A2F'
        secretkey: 'd84BRnMysnVGSyZiRlYUMduVgIarQWiNMdKzrF76'
        userquota: true
        usermaxsize: '1000'
        usermaxobjects: 3
        bucketquota: true
        bucketmaxsize: '1000'
        bucketmaxobjects: 3
    buckets:
      - bucket: 'heyimabucket1'
        user: 'test1'
      - bucket: 'heyimabucket2'
        user: 'test2'
      - bucket: 'heyimabucket3'
        user: 'test2'
'''

RETURN = '''
error_messages:
    description: error for failed user or bucket.
    returned: always
    type: list
    sample: [
            "test2: could not modify user: unable to modify user, cannot add duplicate email\n"  # noqa: E501
        ]

failed_users:
    description: users that were not created.
    returned: always
    type: str
    sample: "test2"

added_users:
    description: users that were created.
    returned: always
    type: str
    sample: "test1"

failed_buckets:
    description: buckets that were not created.
    returned: always
    type: str
    sample: "heyimabucket3"

added_buckets:
    description: buckets that were created.
    returned: always
    type: str
    sample: "heyimabucket1, heyimabucket2"

'''

from ansible.module_utils.basic import AnsibleModule  # type: ignore
import traceback
from ansible.module_utils.basic import missing_required_lib
from socket import error as socket_error

try:
    import boto
except ImportError:
    HAS_ANOTHER_LIBRARY = False
    ANOTHER_LIBRARY_IMPORT_ERROR = traceback.format_exc()
else:
    HAS_ANOTHER_LIBRARY = True
    ANOTHER_LIBRARY_IMPORT_ERROR = None

try:
    import radosgw
except ImportError:
    HAS_ANOTHER_LIBRARY = False
    ANOTHER_LIBRARY_IMPORT_ERROR = traceback.format_exc()
else:
    HAS_ANOTHER_LIBRARY = True
    ANOTHER_LIBRARY_IMPORT_ERROR = None


def create_users(rgw, users, result):

    added_users = []
    failed_users = []

    for user in users:

        # get info
        username = user['username']
        fullname = user['fullname']
        email = user['email']
        maxbucket = user['maxbucket']
        suspend = user['suspend']
        autogenkey = user['autogenkey']
        accesskey = user['accesskey']
        secretkey = user['secretkey']
        userquota = user['userquota']
        usermaxsize = user['usermaxsize']
        usermaxobjects = user['usermaxobjects']
        bucketquota = user['bucketquota']
        bucketmaxsize = user['bucketmaxsize']
        bucketmaxobjects = user['bucketmaxobjects']

        fail_flag = False

        #  check if user exists
        try:
            user_info = rgw.get_user(uid=username)
        except radosgw.exception.RadosGWAdminError:
            # it doesnt exist
            user_info = None

        # user exists can not create
        if user_info:
            result['error_messages'].append(username + ' UserExists')
            failed_users.append(username)
        else:
            # user doesnt exist create it
            if email:
                if autogenkey:
                    try:
                        rgw.create_user(username, fullname, email=email, key_type='s3',  # noqa: E501
                                        generate_key=autogenkey,
                                        max_buckets=maxbucket, suspended=suspend)  # noqa: E501
                    except radosgw.exception.RadosGWAdminError as e:
                        result['error_messages'].append(username + ' ' + e.get_code())  # noqa: E501
                        fail_flag = True
                else:
                    try:
                        rgw.create_user(username, fullname, email=email, key_type='s3',  # noqa: E501
                                        access_key=accesskey, secret_key=secretkey,  # noqa: E501
                                        max_buckets=maxbucket, suspended=suspend)  # noqa: E501
                    except radosgw.exception.RadosGWAdminError as e:
                        result['error_messages'].append(username + ' ' + e.get_code())  # noqa: E501
                        fail_flag = True
            else:
                if autogenkey:
                    try:
                        rgw.create_user(username, fullname, key_type='s3',
                                        generate_key=autogenkey,
                                        max_buckets=maxbucket, suspended=suspend)  # noqa: E501
                    except radosgw.exception.RadosGWAdminError as e:
                        result['error_messages'].append(username + ' ' + e.get_code())  # noqa: E501
                        fail_flag = True
                else:
                    try:
                        rgw.create_user(username, fullname, key_type='s3',
                                        access_key=accesskey, secret_key=secretkey,  # noqa: E501
                                        max_buckets=maxbucket, suspended=suspend)  # noqa: E501
                    except radosgw.exception.RadosGWAdminError as e:
                        result['error_messages'].append(username + ' ' + e.get_code())  # noqa: E501
                        fail_flag = True

            if not fail_flag and userquota:
                try:
                    rgw.set_quota(username, 'user', max_objects=usermaxobjects,
                                  max_size_kb=usermaxsize, enabled=True)
                except radosgw.exception.RadosGWAdminError as e:
                    result['error_messages'].append(username + ' ' + e.get_code())  # noqa: E501
                    fail_flag = True

            if not fail_flag and bucketquota:
                try:
                    rgw.set_quota(username, 'bucket', max_objects=bucketmaxobjects,  # noqa: E501
                                  max_size_kb=bucketmaxsize, enabled=True)
                except radosgw.exception.RadosGWAdminError as e:
                    result['error_messages'].append(username + ' ' + e.get_code())  # noqa: E501
                    fail_flag = True

            if fail_flag:
                try:
                    rgw.delete_user(username)
                except radosgw.exception.RadosGWAdminError:
                    pass
                failed_users.append(username)
            else:
                added_users.append(username)

        result['added_users'] = ", ".join(added_users)
        result['failed_users'] = ", ".join(failed_users)


def create_buckets(rgw, buckets, result):

    added_buckets = []
    failed_buckets = []

    for bucket_info in buckets:
        bucket = bucket_info['bucket']
        user = bucket_info['user']

        #  check if bucket exists
        try:
            bucket_info = rgw.get_bucket(bucket_name=bucket)
        except TypeError:
            # it doesnt exist
            bucket_info = None

        # if it exists add to failed list
        if bucket_info:
            failed_buckets.append(bucket)
            result['error_messages'].append(bucket + ' BucketExists')
        else:
            # bucket doesn't exist, so we need to create it
            bucket_info = create_bucket(rgw, bucket)
            if bucket_info:
                # bucket created ok, link to user

                #  check if user exists
                try:
                    user_info = rgw.get_user(uid=user)
                except radosgw.exception.RadosGWAdminError:
                    # it doesnt exist
                    user_info = None

                # user exists, link
                if user_info:
                    try:
                        rgw.link_bucket(bucket_name=bucket,
                                        bucket_id=bucket_info.id,
                                        uid=user)
                        added_buckets.append(bucket)
                    except radosgw.exception.RadosGWAdminError as e:
                        result['error_messages'].append(bucket + e.get_code())
                        try:
                            rgw.delete_bucket(bucket, purge_objects=True)
                        except radosgw.exception.RadosGWAdminError:
                            pass
                        failed_buckets.append(bucket)

                else:
                    # user doesnt exist cant be link delete bucket
                    try:
                        rgw.delete_bucket(bucket, purge_objects=True)
                    except radosgw.exception.RadosGWAdminError:
                        pass
                    failed_buckets.append(bucket)
                    result['error_messages'].append(bucket + ' could not be linked' + ', NoSuchUser ' + user)  # noqa: E501

            else:
                # something went wrong
                failed_buckets.append(bucket)
                result['error_messages'].append(bucket + ' could not be created')  # noqa: E501

        result['added_buckets'] = ", ".join(added_buckets)
        result['failed_buckets'] = ", ".join(failed_buckets)


def create_bucket(rgw, bucket):
    conn = boto.connect_s3(aws_access_key_id=rgw.provider._access_key,
                           aws_secret_access_key=rgw.provider._secret_key,
                           host=rgw._connection[0],
                           port=rgw.port,
                           is_secure=rgw.is_secure,
                           calling_format=boto.s3.connection.OrdinaryCallingFormat(),  # noqa: E501
                           )

    try:
        conn.create_bucket(bucket_name=bucket)
        bucket_info = rgw.get_bucket(bucket_name=bucket)
    except boto.exception.S3ResponseError:
        return None
    else:
        return bucket_info


def main():
    # arguments/parameters that a user can pass to the module
    fields = dict(rgw_host=dict(type='str', required=True),
                  port=dict(type='int', required=True),
                  is_secure=dict(type='bool',
                                 required=False,
                                 default=False),
                  admin_access_key=dict(type='str', required=True, no_log=False),
                  admin_secret_key=dict(type='str', required=True, no_log=False),
                  buckets=dict(type='list', required=False, elements='dict',
                               options=dict(bucket=dict(type='str', required=True),  # noqa: E501
                                            user=dict(type='str', required=True))),  # noqa: E501
                  users=dict(type='list', required=False, elements='dict',
                             options=dict(username=dict(type='str', required=True),  # noqa: E501
                                          fullname=dict(type='str', required=True),  # noqa: E501
                                          email=dict(type='str', required=False),  # noqa: E501
                                          maxbucket=dict(type='int', required=False, default=1000),  # noqa: E501
                                          suspend=dict(type='bool', required=False, default=False),  # noqa: E501
                                          autogenkey=dict(type='bool', required=False, default=True),  # noqa: E501
                                          accesskey=dict(type='str', required=False, no_log=False),  # noqa: E501
                                          secretkey=dict(type='str', required=False, no_log=False),  # noqa: E501
                                          userquota=dict(type='bool', required=False, default=False),  # noqa: E501
                                          usermaxsize=dict(type='str', required=False, default='-1'),  # noqa: E501
                                          usermaxobjects=dict(type='int', required=False, default=-1),  # noqa: E501
                                          bucketquota=dict(type='bool', required=False, default=False),  # noqa: E501
                                          bucketmaxsize=dict(type='str', required=False, default='-1'),  # noqa: E501
                                          bucketmaxobjects=dict(type='int', required=False, default=-1))))  # noqa: E501

    # the AnsibleModule object
    module = AnsibleModule(argument_spec=fields,
                           supports_check_mode=False)

    if not HAS_ANOTHER_LIBRARY:
        module.fail_json(
            msg=missing_required_lib('another_library'),
            exception=ANOTHER_LIBRARY_IMPORT_ERROR)

    # get vars
    rgw_host = module.params.get('rgw_host')
    port = module.params.get('port')
    is_secure = module.params.get('is_secure')
    admin_access_key = module.params.get('admin_access_key')
    admin_secret_key = module.params.get('admin_secret_key')
    users = module.params['users']
    buckets = module.params.get('buckets')

    # seed the result dict in the object
    result = dict(
        changed=False,
        error_messages=[],
        added_users='',
        failed_users='',
        added_buckets='',
        failed_buckets='',
    )

    # radosgw connection
    rgw = radosgw.connection.RadosGWAdminConnection(host=rgw_host,
                                                    port=port,
                                                    access_key=admin_access_key,  # noqa: E501
                                                    secret_key=admin_secret_key,  # noqa: E501
                                                    aws_signature='AWS4',
                                                    is_secure=is_secure)

    # test connection
    connected = True
    try:
        rgw.get_usage()
    except radosgw.exception.RadosGWAdminError as e:
        connected = False
        result['error_messages'] = e.get_code()
    except socket_error as e:
        connected = False
        result['error_messages'] = str(e)

    if connected and users:
        create_users(rgw, users, result)

    if connected and buckets:
        create_buckets(rgw, buckets, result)

    if result['added_users'] != '' or result['added_buckets'] != '':
        result['changed'] = True

    # conditional state caused a failure
    if result['added_users'] == '' and result['added_buckets'] == '':
        module.fail_json(msg='No users or buckets were added successfully',
                         **result)

    # EXIT
    module.exit_json(**result)


if __name__ == '__main__':
    main()
