# Minio toolkit for Vertica

[Minio](https://github.com/minio/minio) and related tools for Vertica.

## Build

All you need to do is just running `make`.

## Supported Platforms

* CentOS/RHEL 7+

## Directory structure

* **/opt/vertica/bin/minio** : minio server.

* **/opt/vertica/bin/mc** : [minio client](https://github.com/minio/mc) to manage or access S3 storage.

* **/opt/vertica/bin/warp** : [benchmark tool for S3 storage](https://github.com/minio/warp).

* **/usr/lib/systemd/system/minio.service** : minio serivce for systemd.

* **/opt/vertica/config/minio.conf.default** : minio config file template.

* **/opt/vertica/bin/clustercli.sh** : shell commands to assisting cluster management.

  * provides **cls_run**, **cls_cp** to run command and copy files in the whole cluster.

  * cluster members come from `/opt/vertica/config/admintools.conf`, `/opt/vertica/config/minio.conf`.

  * links into /etc/profile.d/, so all users can use it directly in shell.

* TODO: monitoring tools.

## How to use them

Pay attention to the NOTICE after install this package. You can read it again by issue `rpm --scripts -q minio` command.
