# Ceph Automation Collection

This repository contains the `ceph.automation` Ansible Collection.

## Tested with Ansible

Tested with ansible-core >=2.15 releases and the current development version of ansible-core.

## External requirements

Some modules and plugins require external libraries. Please check the requirements for each plugin or module you use in the documentation to find out which requirements are needed.

## Included content

Please check the included content on the [Ansible Galaxy page for this collection](https://galaxy.ansible.com/ui/repo/published/ceph/automation).

## Using this collection

```
    ansible-galaxy collection install ceph.automation
```

You can also include it in a `requirements.yml` file and install it via `ansible-galaxy collection install -r requirements.yml` using the format:

```yaml
collections:
  - name: ceph.automation
```

To upgrade the collection to the latest available version, run the following command:

```bash
ansible-galaxy collection install ceph.automation --upgrade
```

You can also install a specific version of the collection, for example, if you need to downgrade when something is broken in the latest version (please report an issue in this repository). Use the following syntax where `X.Y.Z` can be any [available version](https://galaxy.ansible.com/ui/repo/published/ceph/automation):

```bash
ansible-galaxy collection install ceph.automation:==X.Y.Z
```

See [Ansible Using collections](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html) for more details.

## Ceph CLI execution (cephadm vs host `ceph`)

Several modules run Ceph commands either through **cephadm** (`cephadm shell ceph …`) or directly with the **`ceph`** binary on the target (keyring auth). This matters for clusters **not** managed by cephadm (for example some Proxmox VE setups).

### Options

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `use_cephadm` | `true` | `true`: cephadm shell; `false`: host `ceph` |
| `cluster` | `ceph` | Cluster name for host `ceph` (`--cluster`) |
| `ceph_client` | `client.admin` | Client name for host `ceph` (`-n`) |
| `keyring` | *(derived)* | Keyring path; default `/etc/ceph/<cluster>.<ceph_client>.keyring` |

These options are documented on each affected module and shared via the **`ceph.automation.ceph_cli`** doc fragment.

### Apply to every supported module in a play

Use the **`ceph_cli`** action group so you set `use_cephadm` once (see `meta/runtime.yml` for the module list):

```yaml
- name: Manage Ceph without cephadm shell
  hosts: ceph_nodes
  become: true

  module_defaults:
    group/ceph.automation.ceph_cli:
      use_cephadm: false
      # Optional if paths differ from defaults:
      # cluster: ceph
      # ceph_client: client.admin
      # keyring: /etc/ceph/ceph.client.admin.keyring

  tasks:
    - name: Read a config value
      ceph.automation.ceph_config:
        action: get
        who: global
        option: osd_pool_default_size
```

### Override on a single task

```yaml
- hosts: mixed
  become: true
  module_defaults:
    group/ceph.automation.ceph_cli:
      use_cephadm: true

  tasks:
    - name: This task uses host ceph instead
      ceph.automation.ceph_config:
        use_cephadm: false
        action: get
        who: global
        option: osd_pool_default_size
```

### `cephadm_registry_login`

`cephadm_registry_login` only works with cephadm. It fails if `use_cephadm: false`.

## Release notes

See the [changelog](https://github.com/ceph/ceph.automation/blob/main/CHANGELOG.rst).

## Roadmap

<!-- Optional. Include the roadmap for this collection, and the proposed release/versioning strategy so users can anticipate the upgrade/update cycle. -->

## More information

<!-- List out where the user can find additional information, such as working group meeting times, slack/IRC channels, or documentation for the product this collection automates. At a minimum, link to: -->

- [Ansible Collection overview](https://github.com/ansible-collections/overview)
- [Ansible User guide](https://docs.ansible.com/ansible/devel/user_guide/index.html)
- [Ansible Developer guide](https://docs.ansible.com/ansible/devel/dev_guide/index.html)
- [Ansible Collections Checklist](https://github.com/ansible-collections/overview/blob/main/collection_requirements.rst)
- [Ansible Community code of conduct](https://docs.ansible.com/ansible/devel/community/code_of_conduct.html)
- [The Bullhorn (the Ansible Contributor newsletter)](https://us19.campaign-archive.com/home/?u=56d874e027110e35dea0e03c1&id=d6635f5420)
- [News for Maintainers](https://github.com/ansible-collections/news-for-maintainers)

## Licensing

Apache License, Version 2.0.

See [LICENSE](http://www.apache.org/licenses/LICENSE-2.0) to see the full text.
