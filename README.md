# Minio toolkit for Vertica

[Minio](https://github.com/minio/minio) and related tools for Vertica.

## Build

All you need to do is just running `make`.

## Supported Platforms

* CentOS/RHEL 7+

## Directory structure

* **/opt/vertica/bin/minio** : Minio server.

* **/opt/vertica/bin/mc** : [Minio client](https://github.com/minio/mc) to manage or access S3 storage.

* **/opt/vertica/bin/warp** : [benchmark tool for S3 storage](https://github.com/minio/warp).

* **/usr/lib/systemd/system/minio.service** : Minio serivce for systemd.

* **/opt/vertica/config/minio.conf.default** : Minio config file template.

* **/opt/vertica/bin/clustercli.sh** : shell commands to assisting cluster management.

  * provides **cls_run**, **cls_cp** to run command and copy files in the whole cluster.

  * cluster members automatically come from `/opt/vertica/config/admintools.conf`, `/opt/vertica/config/minio.conf`.

  * links into /etc/profile.d/, so all users can use it directly in shell.

* **/opt/vertica/bin/ddstat** : distributed version of [dstat](https://github.com/dagwieers/dstat) for monitoring cluster.

  * automatically get cluster members from /opt/vertica/bin/clustercli.sh.

  * show timestamp and node name, support `--output csvFile` to export all measures for later analysis.

  * TODO: plugin `--minio` for concurrency, errors and other measures of each Minio service.

## How to use them

Pay attention to the NOTICE after install this package. You can read it again by issue `rpm --scripts -q minio` command.

### Example 1: setup Minio S3 storage

1. install vertica package on one server.

   ```BASH
   [adminUser ~]# sudo rpm -Uvh /tmp/vertica-9.3.1-2.x86_64.RHEL6.rpm
   ```

2. leverage install_vertica to create cluster and adjust system parameter.

   ```BASH
   [adminUser ~]# sudo /opt/vertica/sbin/install_vertica --hosts 192.168.33.105,192.168.33.106,192.168.33.107 --rpm vertica-9.3.1-2.x86_64.RHEL6.rpm
   Vertica Analytic Database 9.3.1-2 Installation Tool

   >> Validating options...
   >> Starting installation tasks.
   >> Getting system information for cluster (this may take a while)...
   >> Validating software versions (rpm or deb)...
   >> Beginning new cluster creation...
   >> Creating or validating DB Admin user/group...
   >> Validating node and cluster prerequisites...
   >> Establishing DB Admin SSH connectivity...
   >> Setting up each node and modifying cluster...
   >> Sending new cluster configuration to all nodes...
   >> Completing installation...

   Running upgrade logic
   Installation complete.
   ```

3. download the latest Minio rpm package from this repository and install it on one server.

   ```BASH
   [adminUser ~]# sudo rpm -Uvh /tmp/minio-1.0.0-20200220225123.el7.x86_64.rpm
   Preparing...                          ################################# [100%]
   Updating / installing...
      1:minio-1.0.0-20200220225123.el7   ################################# [100%]
   ...
   ```

4. copy Minio package and install it to other servers.

   ```BASH
   [adminUser ~]# cls_cp vertica/minio-1.0.0-20200220225123.el7.x86_64.rpm /tmp/
   minio-1.0.0-20200220225123.el7.x86_64.rpm   100%   21MB 125.8MB/s   00:00
   minio-1.0.0-20200220225123.el7.x86_64.rpm   100%   21MB 115.4MB/s   00:00

   # re-login shell, or run "source /etc/profile.d/clustercli.sh"

   [adminUser ~]# cls_run -p sudo rpm -Uvh /tmp/minio-1.0.0-20200220225123.el7.x86_64.rpm
   [192.168.33.105] Preparing...                          ########################################
   [192.168.33.105]  package minio-1.0.0-20200220225123.el7.x86_64 is already installed
   [192.168.33.106] ...
   [192.168.33.107] Preparing...                          ################################# [100%]
   [192.168.33.107] Updating / installing...
   [192.168.33.107]    1:minio-1.0.0-20200220225123.el7   ################################# [100%]
   [192.168.33.107]
   [192.168.33.107] NOTICE:
   [192.168.33.107] 1. the first thing is run [sudo /opt/vertica/sbin/install_vertica --hosts server1,server2,...] to check system and define cluster.
   [192.168.33.107] 2. before you start minio service, modify [/opt/vertica/config/minio.conf] as your situation.
   [192.168.33.107] 3. sync config file [/opt/vertica/config/minio.conf] to all servers as :
   [192.168.33.107]     cls_cp /opt/vertica/config/minio.conf /opt/vertica/config/
   [192.168.33.107] 4. start minio service on all servers as :
   [192.168.33.107]     # start service
   [192.168.33.107]     cls_run --background sudo systemctl start minio.service
   [192.168.33.107]     # show status of service
   [192.168.33.107]     cls_run 'hostname; sudo systemctl status minio.service'
   [192.168.33.107]     # troubleshoot acording to logs if require
   [192.168.33.107]     cls_run 'hostname; sudo journalctl --no-pager -u minio -n 12'
   [192.168.33.107]     # enable service start/restart dynamically
   [192.168.33.107]     cls_run sudo systemctl enable minio.service
   ```

5. set paramenters of Minio

   Prepare disks and file systems for Minio.

   **Note**: dedicated disks for Minio are recommended. But we do not have in this demo. Suppose you have 12 disks each server mounted as /data1~12, just replace following `/home/minio{1...4}` as `/data{1...12}`.

   ```BASH
   [adminUser ~]# cls_run -p sudo mkdir -p /home/minio{1..4}
   [adminUser ~]# cls_run -p sudo chown -R dbadmin:verticadba /home/minio{1..4}
   ```

   Change paramenters of Minio service.

   ```BASH
   [adminUser ~]# cls_run -p sudo -u dbadmin "sed -i -e 's/^\s*MINIO_VOLUMES\s*=.*$/MINIO_VOLUMES=\"http:\/\/192.168.33.{105...107}:9000\/home\/minio{1...4}\"/g' /opt/vertica/config/minio.conf"
   [adminUser ~]# cls_run -p sudo -u dbadmin egrep '^\s*MINIO_VOLUMES\s*=' /opt/vertica/config/minio.conf
   [192.168.33.105] MINIO_VOLUMES="http://192.168.33.{105...107}:9000/home/minio{1...4}"
   [192.168.33.106] MINIO_VOLUMES="http://192.168.33.{105...107}:9000/home/minio{1...4}"
   [192.168.33.107] MINIO_VOLUMES="http://192.168.33.{105...107}:9000/home/minio{1...4}"

   [adminUser ~]# cls_run -p sudo -u dbadmin "sed -i -e 's/^\s*MINIO_ACCESS_KEY\s*=.*$/MINIO_ACCESS_KEY=\"dbadmin\"/g' /opt/vertica/config/minio.conf"
   [adminUser ~]# cls_run -p sudo -u dbadmin egrep '^\s*MINIO_ACCESS_KEY\s*=' /opt/vertica/config/minio.conf
   [192.168.33.105] MINIO_ACCESS_KEY="dbadmin"
   [192.168.33.106] MINIO_ACCESS_KEY="dbadmin"
   [192.168.33.107] MINIO_ACCESS_KEY="dbadmin"

   [adminUser ~]# cls_run -p sudo -u dbadmin "sed -i -e 's/^\s*MINIO_SECRET_KEY\s*=.*$/MINIO_SECRET_KEY=\"verticas3\"/g' /opt/vertica/config/minio.conf"
   [adminUser ~]# cls_run -p sudo -u dbadmin egrep '^\s*MINIO_SECRET_KEY\s*=' /opt/vertica/config/minio.conf
   [192.168.33.105] MINIO_SECRET_KEY="verticas3"
   [192.168.33.106] MINIO_SECRET_KEY="verticas3"
   [192.168.33.107] MINIO_SECRET_KEY="verticas3"
   ```

6. satrt Minio service

   ```BASH
   [adminUser ~]# cls_run --background sudo systemctl start minio.service
   ```

   Show status of Minio service.

   ```BASH
   [adminUser ~]# cls_run -p sudo systemctl status minio.service
   [192.168.33.105] ● minio.service - Minio
   [192.168.33.105]    Loaded: loaded (/usr/lib/systemd/system/minio.service; disabled; vendor preset: disabled)
   [192.168.33.105]    Active: active (running) since Wed 2020-02-26 08:08:20 EST; 24s ago
   [192.168.33.105]      Docs: https://docs.minio.io
   [192.168.33.105]   Process: 37554 ExecStartPre=/bin/sh -c [ -n "${MINIO_VOLUMES}" ] || echo "Variable MINIO_VOLUMES not set in /opt/vertica/config/minio.conf" (code=exited, status=0/SUCCESS)
   [192.168.33.105]  Main PID: 37556 (minio)
   [192.168.33.105]    CGroup: /system.slice/minio.service
   [192.168.33.105]            └─37556 /opt/vertica/bin/minio server --address :9000 --anonymous http://192.168.33.{105...107}:9000/home/minio{1...4}
   [192.168.33.105]
   [192.168.33.105] Feb 26 08:08:23 SE-POC-MapR-1 minio[37556]: Status:         12 Online, 0 Offline.
   [192.168.33.105] Feb 26 08:08:23 SE-POC-MapR-1 minio[37556]: Endpoint:  http://172.16.33.105:9000  http://192.168.33.105:9000  http://127.0.0.1:9000
   [192.168.33.105] Feb 26 08:08:23 SE-POC-MapR-1 minio[37556]: Browser Access:
   [192.168.33.105] Feb 26 08:08:23 SE-POC-MapR-1 minio[37556]: http://172.16.33.105:9000  http://192.168.33.105:9000  http://127.0.0.1:9000
   [192.168.33.105] Feb 26 08:08:23 SE-POC-MapR-1 minio[37556]: Object API (Amazon S3 compatible):
   [192.168.33.105] Feb 26 08:08:23 SE-POC-MapR-1 minio[37556]: Go:         https://docs.min.io/docs/golang-client-quickstart-guide
   [192.168.33.105] Feb 26 08:08:23 SE-POC-MapR-1 minio[37556]: Java:       https://docs.min.io/docs/java-client-quickstart-guide
   [192.168.33.105] Feb 26 08:08:23 SE-POC-MapR-1 minio[37556]: Python:     https://docs.min.io/docs/python-client-quickstart-guide
   [192.168.33.105] Feb 26 08:08:23 SE-POC-MapR-1 minio[37556]: JavaScript: https://docs.min.io/docs/javascript-client-quickstart-guide
   [192.168.33.105] Feb 26 08:08:23 SE-POC-MapR-1 minio[37556]: .NET:       https://docs.min.io/docs/dotnet-client-quickstart-guide
   [192.168.33.106] ● minio.service - Minio
   [192.168.33.106]    Loaded: loaded (/usr/lib/systemd/system/minio.service; disabled; vendor preset: disabled)
   [192.168.33.106]    Active: active (running) since Wed 2020-02-26 08:08:20 EST; 24s ago
   [192.168.33.106]      Docs: https://docs.minio.io
   [192.168.33.106]   Process: 73372 ExecStartPre=/bin/sh -c [ -n "${MINIO_VOLUMES}" ] || echo "Variable MINIO_VOLUMES not set in /opt/vertica/config/minio.conf" (code=exited, status=0/SUCCESS)
   [192.168.33.106]  Main PID: 73376 (minio)
   [192.168.33.106]    CGroup: /system.slice/minio.service
   [192.168.33.106]            └─73376 /opt/vertica/bin/minio server --address :9000 --anonymous http://192.168.33.{105...107}:9000/home/minio{1...4}
   [192.168.33.106]
   [192.168.33.106] Feb 26 08:08:24 SE-POC-MapR-2 minio[73376]: Status:         12 Online, 0 Offline.
   [192.168.33.106] Feb 26 08:08:24 SE-POC-MapR-2 minio[73376]: Endpoint:  http://172.16.33.106:9000  http://192.168.33.106:9000  http://127.0.0.1:9000
   [192.168.33.106] Feb 26 08:08:24 SE-POC-MapR-2 minio[73376]: Browser Access:
   [192.168.33.106] Feb 26 08:08:24 SE-POC-MapR-2 minio[73376]: http://172.16.33.106:9000  http://192.168.33.106:9000  http://127.0.0.1:9000
   [192.168.33.106] Feb 26 08:08:24 SE-POC-MapR-2 minio[73376]: Object API (Amazon S3 compatible):
   [192.168.33.106] Feb 26 08:08:24 SE-POC-MapR-2 minio[73376]: Go:         https://docs.min.io/docs/golang-client-quickstart-guide
   [192.168.33.106] Feb 26 08:08:24 SE-POC-MapR-2 minio[73376]: Java:       https://docs.min.io/docs/java-client-quickstart-guide
   [192.168.33.106] Feb 26 08:08:24 SE-POC-MapR-2 minio[73376]: Python:     https://docs.min.io/docs/python-client-quickstart-guide
   [192.168.33.106] Feb 26 08:08:24 SE-POC-MapR-2 minio[73376]: JavaScript: https://docs.min.io/docs/javascript-client-quickstart-guide
   [192.168.33.106] Feb 26 08:08:24 SE-POC-MapR-2 minio[73376]: .NET:       https://docs.min.io/docs/dotnet-client-quickstart-guide
   [192.168.33.107] ● minio.service - Minio
   [192.168.33.107]    Loaded: loaded (/usr/lib/systemd/system/minio.service; disabled; vendor preset: disabled)
   [192.168.33.107]    Active: active (running) since Wed 2020-02-26 08:08:20 EST; 24s ago
   [192.168.33.107]      Docs: https://docs.minio.io
   [192.168.33.107]   Process: 215304 ExecStartPre=/bin/sh -c [ -n "${MINIO_VOLUMES}" ] || echo "Variable MINIO_VOLUMES not set in /opt/vertica/config/minio.conf" (code=exited, status=0/SUCCESS)
   [192.168.33.107]  Main PID: 215306 (minio)
   [192.168.33.107]    CGroup: /system.slice/minio.service
   [192.168.33.107]            └─215306 /opt/vertica/bin/minio server --address :9000 --anonymous http://192.168.33.{105...107}:9000/home/minio{1...4}
   [192.168.33.107]
   [192.168.33.107] Feb 26 08:08:23 SE-POC-MapR-3 minio[215306]: Status:         12 Online, 0 Offline.
   [192.168.33.107] Feb 26 08:08:23 SE-POC-MapR-3 minio[215306]: Endpoint:  http://172.16.33.107:9000  http://192.168.33.107:9000  http://127.0.0.1:9000
   [192.168.33.107] Feb 26 08:08:23 SE-POC-MapR-3 minio[215306]: Browser Access:
   [192.168.33.107] Feb 26 08:08:23 SE-POC-MapR-3 minio[215306]: http://172.16.33.107:9000  http://192.168.33.107:9000  http://127.0.0.1:9000
   [192.168.33.107] Feb 26 08:08:23 SE-POC-MapR-3 minio[215306]: Object API (Amazon S3 compatible):
   [192.168.33.107] Feb 26 08:08:23 SE-POC-MapR-3 minio[215306]: Go:         https://docs.min.io/docs/golang-client-quickstart-guide
   [192.168.33.107] Feb 26 08:08:23 SE-POC-MapR-3 minio[215306]: Java:       https://docs.min.io/docs/java-client-quickstart-guide
   [192.168.33.107] Feb 26 08:08:23 SE-POC-MapR-3 minio[215306]: Python:     https://docs.min.io/docs/python-client-quickstart-guide
   [192.168.33.107] Feb 26 08:08:23 SE-POC-MapR-3 minio[215306]: JavaScript: https://docs.min.io/docs/javascript-client-quickstart-guide
   [192.168.33.107] Feb 26 08:08:23 SE-POC-MapR-3 minio[215306]: .NET:       https://docs.min.io/docs/dotnet-client-quickstart-guide
   ```

   Troubleshoot acording to logs if required.

   ```BASH
   [adminUser ~]# cls_run -p sudo journalctl --no-pager -u minio
   ```

   Monitor cluster status of Minio.

   ```BASH
   su - dbadmin
   [dbadmin ~]# cls_run -p mc config host add mys3 http://localhost:9000 dbadmin verticas3
   [192.168.33.105] Added `mys3` successfully.
   [192.168.33.106] Added `mys3` successfully.
   [192.168.33.107] Added `mys3` successfully.

   [dbadmin ~]# cls_run -p mc config host add mys3 http://localhost:9000 dbadmin verticas3
   [dbadmin ~]# mc admin info mys3
   ●  192.168.33.106:9000
      Uptime: 3 minutes
      Version: 2020-02-20T22:51:23Z
      Network: 3/3 OK
      Drives: 4/4 OK
   ●  192.168.33.107:9000
      Uptime: 3 minutes
      Version: 2020-02-20T22:51:23Z
      Network: 3/3 OK
      Drives: 4/4 OK
   ●  192.168.33.105:9000
      Uptime: 3 minutes
      Version: 2020-02-20T22:51:23Z
      Network: 3/3 OK
      Drives: 4/4 OK
   ```

### Example 2: benchmark S3 storage

1. vioperf on filesystem, and vioperf on networking

   ```BASH
   [dbadmin ~]# cls_run -b -p /opt/vertica/bin/vioperf /home 2>/dev/null
   [192.168.33.107] The minimum required I/O is 20 MB/s read and write per physical processor core on each node, in full duplex i.e. reading and writing at this rate simultaneously, concurrently on all nodes of the cluster. The recommended I/O is 40 MB/s per physical core on each node. For example, the I/O rate for a server node with 2 hyper-threaded six-core CPUs is 240 MB/s required minimum, 480 MB/s recommended.
   [192.168.33.107]
   [192.168.33.107] Using direct io (buffer size=1048576, alignment=512) for directory "/home"
   [192.168.33.107]
   [192.168.33.107] test      | directory          | counter name        | counter value       | counter value (10 sec avg)      | counter value/core  | counter value/core (10 sec avg) | thread count  | %CPU  | %IO Wait  | elapsed time (s)| remaining time (s)
   [192.168.33.107] ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
   [192.168.33.107] Write     | /home              | MB/s                | 1611                | 1612                            | 201.375             | 201.5                           | 8             | 67    | 32        | 75              | 0
   [192.168.33.107] ReWrite   | /home              | (MB-read+MB-write)/s| 336+336             | 336+336                         | 42+42               | 42+42                           | 8             | 14    | 78        | 10              | 65
   [192.168.33.107] Read      | /home              | MB/s                | 631                 | 649                             | 78.875              | 81.125                          | 8             | 26    | 69        | 20              | 55
   [192.168.33.107] SkipRead  | /home              | seeks/s             | 1768                | 1696                            | 221                 | 212                             | 8             | 0     | 62        | 40              | 35
   [192.168.33.106] Write     | /home              | MB/s                | 1253                | 1272                            | 156.625             | 159                             | 8             | 53    | 45        | 20              | 55
   [192.168.33.106] ReWrite   | /home              | (MB-read+MB-write)/s| 319+319             | 319+319                         | 39.875+39.875       | 39.875+39.875                   | 8             | 13    | 82        | 10              | 65
   [192.168.33.106] Read      | /home              | MB/s                | 624                 | 624                             | 78                  | 78                              | 8             | 26    | 68        | 10              | 65
   [192.168.33.106] SkipRead  | /home              | seeks/s             | 1652                | 1781                            | 206.5               | 222.625                         | 8             | 0     | 77        | 40              | 35
   [192.168.33.105] Write     | /home              | MB/s                | 1783                | 1861                            | 222.875             | 232.625                         | 8             | 78    | 21        | 30              | 45
   [192.168.33.105] ReWrite   | /home              | (MB-read+MB-write)/s| 323+323             | 323+323                         | 40.375+40.375       | 40.375+40.375                   | 8             | 14    | 78        | 10              | 65
   [192.168.33.105] Read      | /home              | MB/s                | 720                 | 763                             | 90                  | 95.375                          | 8             | 34    | 62        | 40              | 35
   [192.168.33.105] SkipRead  | /home              | seeks/s             | 1177                | 1243                            | 147.125             | 155.375                         | 8             | 0     | 81        | 30              | 45

   [dbadmin ~]$ vnetperf
   The maximum recommended rtt latency is 2 milliseconds. The ideal rtt latency is 200 microseconds or less. It is recommended that clock skew be kept to under 1 second.
   test              | date                    | node             | index | rtt latency (us)  | clock skew (us)
   -------------------------------------------------------------------------------------------------------------------------
   latency           | 2020-02-26_23:35:42,304 | 192.168.33.105   | 0     | 41                | 0
   latency           | 2020-02-26_23:35:42,304 | 192.168.33.106   | 1     | 95                | 1351
   latency           | 2020-02-26_23:35:42,304 | 192.168.33.107   | 2     | 104               | 1290

   The minimum recommended throughput is 100 MB/s. Ideal throughput is 800 MB/s or more. Note: UDP numbers may be lower, multiple network switches may reduce performance results.
   date                    | test              | rate limit (MB/s) | node             | MB/s (sent) | MB/s (rec)  | bytes (sent)        | bytes (rec)         | duration (s)
   ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
   2020-02-26_23:35:42,306 | udp-throughput    | 32                | average          | 30.5153     | 30.5153     | 32002261            | 32002261            | 1.00015
   2020-02-26_23:35:43,307 | udp-throughput    | 64                | average          | 61.0286     | 61.0286     | 64002560            | 64002560            | 1.00015
   2020-02-26_23:35:44,308 | udp-throughput    | 128               | average          | 122.057     | 122.057     | 128001685           | 128001685           | 1.00012
   2020-02-26_23:35:45,309 | udp-throughput    | 256               | average          | 244.11      | 244.11      | 256001408           | 256001408           | 1.00013
   2020-02-26_23:35:46,310 | udp-throughput    | 512               | average          | 438.032     | 437.455     | 459398933           | 458790997           | 1.00019
   2020-02-26_23:35:47,311 | udp-throughput    | 640               | average          | 482.064     | 441.4       | 505629546           | 462986197           | 1.00031
   2020-02-26_23:35:48,312 | udp-throughput    | 768               | average          | 406.041     | 347.125     | 425957056           | 364151210           | 1.00051
   2020-02-26_23:35:49,314 | udp-throughput    | 1024              | 192.168.33.105   | 759.878     | 336.581     | 796980544           | 353015040           | 1.00024
   2020-02-26_23:35:49,314 | udp-throughput    | 1024              | 192.168.33.106   | 332.769     | 551.1       | 349229056           | 578360576           | 1.00085
   2020-02-26_23:35:49,314 | udp-throughput    | 1024              | 192.168.33.107   | 378.137     | 420.239     | 396960128           | 441158400           | 1.00115
   2020-02-26_23:35:49,314 | udp-throughput    | 1024              | average          | 490.261     | 435.973     | 514389909           | 457511338           | 1.00074
   2020-02-26_23:35:50,316 | udp-throughput    | 2048              | average          | 498.404     | 457.557     | 522858325           | 480273856           | 1.00083

   The minimum recommended throughput is 100 MB/s. Ideal throughput is 800 MB/s or more. Note: UDP numbers may be lower, multiple network switches may reduce performance results.
   date                    | test              | rate limit (MB/s) | node             | MB/s (sent) | MB/s (rec)  | bytes (sent)        | bytes (rec)         | duration (s)
   ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
   2020-02-26_23:35:51,318 | tcp-throughput    | 32                | average          | 30.5795     | 30.5795     | 32112640            | 32112640            | 1.00149
   2020-02-26_23:35:53,322 | tcp-throughput    | 64                | average          | 61.0966     | 61.0966     | 64094208            | 64094208            | 1.00047
   2020-02-26_23:35:55,324 | tcp-throughput    | 128               | average          | 122.131     | 122.131     | 128122880           | 128122880           | 1.00047
   2020-02-26_23:35:57,326 | tcp-throughput    | 256               | average          | 244.196     | 244.196     | 256114688           | 256114688           | 1.00022
   2020-02-26_23:35:59,327 | tcp-throughput    | 512               | average          | 488.336     | 488.336     | 512098304           | 512098304           | 1.00008
   2020-02-26_23:36:01,329 | tcp-throughput    | 640               | average          | 610.407     | 610.407     | 640090112           | 640090112           | 1.00005
   2020-02-26_23:36:03,331 | tcp-throughput    | 768               | average          | 732.477     | 732.477     | 768081920           | 768081920           | 1.00003
   2020-02-26_23:36:05,332 | tcp-throughput    | 1024              | 192.168.33.105   | 971.721     | 976.094     | 1019478016          | 1024065536          | 1.00054
   2020-02-26_23:36:05,332 | tcp-throughput    | 1024              | 192.168.33.106   | 976.618     | 967.243     | 1024065536          | 1014235136          | 1.00001
   2020-02-26_23:36:05,332 | tcp-throughput    | 1024              | 192.168.33.107   | 976.599     | 976.599     | 1024065536          | 1024065536          | 1.00003
   2020-02-26_23:36:05,332 | tcp-throughput    | 1024              | average          | 974.979     | 973.312     | 1022536362          | 1020788736          | 1.00019
   2020-02-26_23:36:07,335 | tcp-throughput    | 2048              | average          | 1069.25     | 1067.93     | 1123046741          | 1121648640          | 1.00165
   ```

2. warp on s3

   Testing PUT and GET with concurrence.

   ```BASH
   [dbadmin ~]# cls_run 'nohup /opt/vertica/bin/warp client > ~/warp_client.log 2>&1 &'
   [dbadmin ~]# cls_run -p /usr/sbin/pidof  warp
   [192.168.33.105] 43668
   [192.168.33.106] 77078
   [192.168.33.107] 247321

   [dbadmin ~]# warp get --duration=1m --warp-client=192.168.33.{105...107} --host=192.168.33.{105...107}:9000 -concurrent=$(lscpu | egrep '^CPU\(s\):' | awk '{print $2}') --access-key=dbadmin --secret-key=verticas3
   Operation: PUT. Concurrency: 21. Hosts: 3.
   * Average: 626.75 MiB/s, 62.68 obj/s (1m58.11s, starting 18:15:09 EST)
   warp: Connecting to ws://192.168.33.105:7761/ws
   warp: Client 192.168.33.105:7761 connected...
   warp: Connecting to ws://192.168.33.106:7761/ws
   warp: Client 192.168.33.106:7761 connected...
   warp: Connecting to ws://192.168.33.107:7761/ws
   warp: Client 192.168.33.107:7761 connected...
   warp: All clients connected...
   warp: Requesting stage prepare start...
   warp: Client 192.168.33.105:7761: Requested stage prepare start..
   warp: Client 192.168.33.107:7761: Requested stage prepare start..
   warp: Client 192.168.33.106:7761: Requested stage prepare start..
   warp: Client 192.168.33.105:7761: Finished stage prepare...
   warp: Client 192.168.33.107:7761: Finished stage prepare...
   warp: Client 192.168.33.106:7761: Finished stage prepare...
   warp: All clients prepared...
   warp: Requesting stage benchmark start...
   warp: Client 192.168.33.105:7761: Requested stage benchmark start..
   warp: Client 192.168.33.106:7761: Requested stage benchmark start..
   warp: Client 192.168.33.107:7761: Requested stage benchmark start..
   warp: Client 192.168.33.106:7761: Finished stage benchmark...
   warp: Client 192.168.33.107:7761: Finished stage benchmark...
   warp: Client 192.168.33.105:7761: Finished stage benchmark...
   warp: Done. Downloading operations...
   warp: Client 192.168.33.105:7761: Operations downloaded.
   warp: Client 192.168.33.106:7761: Operations downloaded.
   warp: Client 192.168.33.107:7761: Operations downloaded.
   warp: Benchmark data written to "warp-remote-2020-02-26[182919]-eoyK.csv.zst"
   warp: Requesting stage cleanup start...
   warp: Client 192.168.33.105:7761: Requested stage cleanup start..
   warp: Client 192.168.33.106:7761: Requested stage cleanup start..
   warp: Client 192.168.33.107:7761: Requested stage cleanup start..
   warp: Client 192.168.33.105:7761: Finished stage cleanup...
   warp: Client 192.168.33.107:7761: Finished stage cleanup...
   warp: Client 192.168.33.106:7761: Finished stage cleanup...
   -------------------
   Operation: PUT. Concurrency: 24. Hosts: 3.
   * Average: 655.51 MiB/s, 65.55 obj/s (1m52.742s, starting 18:26:21 EST)

   Throughput by host:
    * http://192.168.33.105:9000: Avg: 226.36 MiB/s, 22.64 obj/s (1m54.472s, starting 18:26:19 EST)
    * http://192.168.33.106:9000: Avg: 219.53 MiB/s, 21.95 obj/s (1m54.476s, starting 18:26:19 EST)
    * http://192.168.33.107:9000: Avg: 208.56 MiB/s, 20.86 obj/s (1m54.337s, starting 18:26:19 EST)

   Aggregated Throughput, split into 112 x 1s time segments:
    * Fastest: 731.3MiB/s, 73.13 obj/s (1s, starting 18:26:24 EST)
    * 50% Median: 664.2MiB/s, 66.42 obj/s (1s, starting 18:28:02 EST)
    * Slowest: 527.1MiB/s, 52.71 obj/s (1s, starting 18:27:11 EST)
   -------------------
   Operation: GET. Concurrency: 24. Hosts: 3.
   * Average: 1900.35 MiB/s, 190.04 obj/s (59.407s, starting 18:28:18 EST)

   Throughput by host:
    * http://192.168.33.105:9000: Avg: 639.18 MiB/s, 63.92 obj/s (1m0s, starting 18:28:18 EST)
    * http://192.168.33.106:9000: Avg: 631.15 MiB/s, 63.12 obj/s (59.989s, starting 18:28:18 EST)
    * http://192.168.33.107:9000: Avg: 628.22 MiB/s, 62.82 obj/s (59.967s, starting 18:28:18 EST)

   Aggregated Throughput, split into 59 x 1s time segments:
    * Fastest: 2060.7MiB/s, 206.07 obj/s (1s, starting 18:29:03 EST)
    * 50% Median: 1944.1MiB/s, 194.41 obj/s (1s, starting 18:29:16 EST)
    * Slowest: 1487.5MiB/s, 148.75 obj/s (1s, starting 18:28:18 EST)


   Every 5.0s: /opt/vertica/bin/mondb.sh                          Wed Feb 26 18:26:36 2020

   192.168.33.105: usr sys idl wai hiq siq| read  writ| recv  send|  in   out | int   csw
   192.168.33.105:  60  13  15   5   0   6|   0   460M| 458M  456M|   0     0 |  46k   24k
   192.168.33.106:  64  15  10   5   0   6|   0   465M| 461M  433M|   0     0 |  42k   17k
   192.168.33.107:  57  15  17   5   0   7|   0   469M| 448M  421M|   0     0 |  49k   20k
   192.168.33.105: usr sys idl wai hiq siq| read  writ| recv  send|  in   out | int   csw
   192.168.33.105:  30  16  24  21   0   9| 295M    0 | 843M  807M|   0     0 |  97k   92k
   192.168.33.106:  31  16  26  17   0   9| 299M    0 | 829M  829M|   0     0 |  88k   80k
   192.168.33.107:  36  17  19  18   0   9| 290M    0 | 792M  846M|   0     0 |  82k   70k
   ```

   Testing with mixed mode for near 'real workload'.

   ```BASH

   [dbadmin ~]# warp mixed --duration=1m --warp-client=192.168.33.{105...107} --host=192.168.33.{105...107}:9000 --obj.size 10M -concurrent=$(lscpu | egrep '^CPU\(s\):' | awk '{print $2}') --access-key=dbadmin --secret-key=verticas3
   warp: Connecting to ws://192.168.33.105:7761/ws
   warp: Client 192.168.33.105:7761 connected...
   warp: Connecting to ws://192.168.33.106:7761/ws
   warp: Client 192.168.33.106:7761 connected...
   warp: Connecting to ws://192.168.33.107:7761/ws
   warp: Client 192.168.33.107:7761 connected...
   warp: All clients connected...
   warp: Requesting stage prepare start...
   warp: Client 192.168.33.105:7761: Requested stage prepare start..
   warp: Client 192.168.33.106:7761: Requested stage prepare start..
   warp: Client 192.168.33.107:7761: Requested stage prepare start..
   warp: Client 192.168.33.105:7761: Finished stage prepare...
   warp: Client 192.168.33.106:7761: Finished stage prepare...
   warp: Client 192.168.33.107:7761: Finished stage prepare...
   warp: All clients prepared...
   warp: Requesting stage benchmark start...
   warp: Client 192.168.33.107:7761: Requested stage benchmark start..
   warp: Client 192.168.33.105:7761: Requested stage benchmark start..
   warp: Client 192.168.33.106:7761: Requested stage benchmark start..
   warp: Client 192.168.33.105:7761: Finished stage benchmark...
   warp: Client 192.168.33.106:7761: Finished stage benchmark...
   warp: Client 192.168.33.107:7761: Finished stage benchmark...
   warp: Done. Downloading operations...
   warp: Client 192.168.33.105:7761: Operations downloaded.
   warp: Client 192.168.33.107:7761: Operations downloaded.
   warp: Client 192.168.33.106:7761: Operations downloaded.
   warp: Benchmark data written to "warp-remote-2020-02-26[193830]-0gFV.csv.zst"
   warp: Requesting stage cleanup start...
   warp: Client 192.168.33.105:7761: Requested stage cleanup start..
   warp: Client 192.168.33.107:7761: Requested stage cleanup start..
   warp: Client 192.168.33.106:7761: Requested stage cleanup start..
   warp: Client 192.168.33.107:7761: Finished stage cleanup...
   warp: Client 192.168.33.106:7761: Finished stage cleanup...
   warp: Client 192.168.33.105:7761: Finished stage cleanup...
   Mixed operations.

   Operation: DELETE
    * Operations: 1107 (10.0% of operations)

   Throughput by host:
    * http://192.168.33.105:9000: Avg: 6.22 obj/s (59.514s, starting 19:37:29 EST)
    * http://192.168.33.106:9000: Avg: 5.89 obj/s (59.413s, starting 19:37:29 EST)
    * http://192.168.33.107:9000: Avg: 6.44 obj/s (59.826s, starting 19:37:29 EST)

   Operation: STAT
    * Operations: 3347 (30.3% of operations)

   Throughput by host:
    * http://192.168.33.106:9000: Avg: 18.19 obj/s (59.743s, starting 19:37:29 EST)
    * http://192.168.33.107:9000: Avg: 19.53 obj/s (59.951s, starting 19:37:29 EST)
    * http://192.168.33.105:9000: Avg: 18.19 obj/s (59.97s, starting 19:37:29 EST)

   Operation: GET
    * Operations: 5019 (45.5% of operations)

   Throughput by host:
    * http://192.168.33.105:9000: Avg: 267.46 MiB/s, 28.05 obj/s (59.957s, starting 19:37:29 EST)
    * http://192.168.33.106:9000: Avg: 265.32 MiB/s, 27.82 obj/s (59.986s, starting 19:37:29 EST)
    * http://192.168.33.107:9000: Avg: 266.45 MiB/s, 27.94 obj/s (59.921s, starting 19:37:29 EST)

   Operation: PUT
    * Operations: 1672 (15.2% of operations)

   Throughput by host:
    * http://192.168.33.105:9000: Avg: 94.93 MiB/s, 9.95 obj/s (59.69s, starting 19:37:29 EST)
    * http://192.168.33.106:9000: Avg: 92.06 MiB/s, 9.65 obj/s (59.249s, starting 19:37:29 EST)
    * http://192.168.33.107:9000: Avg: 80.95 MiB/s, 8.49 obj/s (59.611s, starting 19:37:29 EST)

   Cluster Total:  1062.11 MiB/s, 185.57 obj/s (59.474s, starting 19:37:29 EST)
    * http://192.168.33.105:9000:  362.47 MiB/s, 62.40 obj/s (59.97s, starting 19:37:29 EST)
    * http://192.168.33.106:9000:  356.36 MiB/s, 61.36 obj/s (59.997s, starting 19:37:29 EST)
    * http://192.168.33.107:9000:  347.01 MiB/s, 62.33 obj/s (59.992s, starting 19:37:29 EST)

   Every 5.0s: /opt/vertica/bin/mondb.sh                         Wed Feb 26 19:35:16 2020

   192.168.33.105: usr sys idl wai hiq siq| read  writ| recv  send|  in   out | int   csw
   192.168.33.105:  62  13  17   3   0   5|   0   459M| 454M  452M|   0     0 |  43k   20k
   192.168.33.106:  64  17  10   2   0   6|   0   461M| 440M  445M|   0     0 |  40k   16k
   192.168.33.107:  61  15  16   2   0   6|   0   463M| 443M  437M|   0     0 |  47k   21k
   192.168.33.105: usr sys idl wai hiq siq| read  writ| recv  send|  in   out | int   csw
   192.168.33.105:  43  14  12  25   0   6| 274M  145M| 575M  555M|   0     0 |  72k   61k
   192.168.33.106:  42  19   6  25   0   8| 278M  146M| 570M  568M|   0     0 |  66k   53k
   192.168.33.107:  45  15  10  22   0   8| 274M  145M| 553M  545M|   0     0 |  71k   57k
   192.168.33.105: usr sys idl wai hiq siq| read  writ| recv  send|  in   out | int   csw
   192.168.33.105:  44  14  23  14   0   5| 145M  200M| 485M  560M|   0     0 |  60k   48k
   192.168.33.106:  44  18  12  18   0   8| 147M  205M| 549M  517M|   0     0 |  61k   44k
   192.168.33.107:  41  15  15  24   0   6| 143M  202M| 506M  493M|   0     0 |  65k   54k
   ```

3. testing for throughput-concurrence curve

   ```BASH
   [dbadmin ~]# for ((n=1; n<=2*$(lscpu | egrep '^CPU\(s\):' | awk '{print $2}'); n++)) ; do warp mixed --duration=1m --warp-client=192.168.33.{105...107} --host=192.168.33.{105...107}:9000 --obj.size 10M -concurrent=${n} --access-key=dbadmin --secret-key=verticas3 ; done | grep  "Cluster Total"
   Cluster Total:  302.48 MiB/s, 52.83 obj/s (59.81s, starting 19:55:55 EST)
   Cluster Total:  568.61 MiB/s, 99.47 obj/s (59.777s, starting 20:01:48 EST)
   Cluster Total:  687.54 MiB/s, 119.33 obj/s (59.703s, starting 20:07:10 EST)
   Cluster Total:  821.47 MiB/s, 143.35 obj/s (59.64s, starting 20:12:01 EST)
   Cluster Total:  900.37 MiB/s, 157.32 obj/s (59.565s, starting 20:16:44 EST)
   Cluster Total:  966.16 MiB/s, 169.55 obj/s (59.249s, starting 20:21:16 EST)
   Cluster Total:  1037.95 MiB/s, 181.44 obj/s (59.373s, starting 20:25:48 EST)
   Cluster Total:  1047.78 MiB/s, 183.17 obj/s (59.203s, starting 20:30:12 EST)
   Cluster Total:  1113.91 MiB/s, 195.09 obj/s (59.412s, starting 20:34:32 EST)
   Cluster Total:  1138.81 MiB/s, 199.39 obj/s (59.387s, starting 20:38:52 EST)
   Cluster Total:  1161.93 MiB/s, 203.06 obj/s (59.227s, starting 20:42:59 EST)
   Cluster Total:  1209.29 MiB/s, 211.20 obj/s (59.252s, starting 20:47:10 EST)
   Cluster Total:  1165.61 MiB/s, 203.76 obj/s (59.122s, starting 20:51:28 EST)
   Cluster Total:  1181.16 MiB/s, 206.76 obj/s (58.914s, starting 20:55:43 EST)
   Cluster Total:  1180.56 MiB/s, 206.33 obj/s (59.103s, starting 20:59:49 EST)
   Cluster Total:  1171.16 MiB/s, 205.02 obj/s (58.7s, starting 21:04:15 EST)

   [dbadmin ~]# cls_run killall -9 warp

   ```

### Example 3: create Vertica Eon mode database

1. create bucket for Vertica's communal storage.

   ```BASH
   [dbadmin ~]# mc mb mys3/vmarteon
   Bucket created successfully `mys3/vmarteon`.

   [dbadmin ~]# mc du mys3/vmarteon
   0B    vmarteon
   ```

2. create Eon mode database.

   **Note**: dedicated servers for Vertica are recommended. But we do not have in this demo. Replace following `localhost` as real host names or IPs of your Minio servers.

   ```BASH
   [dbadmin ~]# echo "awsauth = dbadmin:verticas3" > auth_params.conf
   [dbadmin ~]# echo "awsendpoint = localhost:9000" >> auth_params.conf
   [dbadmin ~]# echo "awsenablehttps = 0" >> auth_params.conf

   [dbadmin ~]# cls_run -p mkdir -p /home/dbadmin/vmarteon_depot
   [dbadmin ~]# cls_run -p du -hs /home/dbadmin/vmarteon_depot
   [192.168.33.105] 4.0K    /home/dbadmin/vmarteon_depot
   [192.168.33.106] 4.0K    /home/dbadmin/vmarteon_depot
   [192.168.33.107] 4.0K    /home/dbadmin/vmarteon_depot

   [dbadmin ~]# admintools -t create_db -x auth_params.conf \
                --communal-storage-location=s3://vmarteon \
                --depot-path=/home/dbadmin/vmarteon_depot  --shard-count=3 \
                --hosts 192.168.33.105,192.168.33.106,192.168.33.107 -d vmarteon -p 'myvertica'
   Default depot size in use
   Distributing changes to cluster.
   ...
   Start hosts = ['192.168.33.105', '192.168.33.106', '192.168.33.107']
   Starting nodes:
      v_vmarteon_node0001 (192.168.33.105)
      v_vmarteon_node0002 (192.168.33.106)
      v_vmarteon_node0003 (192.168.33.107)
   ...
   Node Status: v_vmarteon_node0001: (UP) v_vmarteon_node0002: (UP) v_vmarteon_node0003: (UP)
   Creating depot locations for 3 nodes
   Communal storage detected: rebalancing shards

   [dbadmin ~]# vsql -w myvertica -c "select node_name, location_path, location_usage, sharing_type, max_size from storage_locations order by 1, 2"
         node_name      |                          location_path                          | location_usage | sharing_type |   max_size
   ---------------------+-----------------------------------------------------------------+----------------+--------------+---------------
    v_vmarteon_node0001 | /home/dbadmin/vmarteon/v_vmarteon_node0001_data                 | DATA,TEMP      | NONE         |             0
    v_vmarteon_node0001 | /home/dbadmin/vmarteon_depot/vmarteon/v_vmarteon_node0001_depot | DEPOT          | NONE         | 1246305887232
    v_vmarteon_node0002 | /home/dbadmin/vmarteon/v_vmarteon_node0002_data                 | DATA,TEMP      | NONE         |             0
    v_vmarteon_node0002 | /home/dbadmin/vmarteon_depot/vmarteon/v_vmarteon_node0002_depot | DEPOT          | NONE         | 1246305887232
    v_vmarteon_node0003 | /home/dbadmin/vmarteon/v_vmarteon_node0003_data                 | DATA,TEMP      | NONE         |             0
    v_vmarteon_node0003 | /home/dbadmin/vmarteon_depot/vmarteon/v_vmarteon_node0003_depot | DEPOT          | NONE         | 1246305887232
                        | s3://vmarteon/                                                  | DATA           | COMMUNAL     |             0
   (7 rows)

   [dbadmin ~]# vsql -w myvertica -c "create table test(id int)"
   CREATE TABLE

   [dbadmin ~]# seq 1 1000000 | vsql -w myvertica -c "copy test from stdin"
   [dbadmin ~]# vsql -w myvertica -c "select count(*) from test"
     count
   ---------
    1000000
   (1 row)

   [dbadmin ~]# vsql -w myvertica -c "select node_name, count(*) as cnt, sum(file_size_bytes) as size from depot_uploads group by 1 order by 1"
         node_name      | cnt |  size
   ---------------------+-----+--------
    v_vmarteon_node0001 |  17 | 341940
    v_vmarteon_node0002 |   1 | 340077
    v_vmarteon_node0003 |   1 | 340311
   (3 rows)

   [dbadmin ~]# vsql -w myvertica -c "select node_name, count(*) as cnt, sum(file_size_bytes) as size from depot_files group by 1 order by 1"
         node_name      | cnt |  size
   ---------------------+-----+--------
    v_vmarteon_node0001 |   7 | 341181
    v_vmarteon_node0002 |   1 | 340077
    v_vmarteon_node0003 |   1 | 340311
   (3 rows)

   [dbadmin ~]# cls_run -p "du -hs /home/dbadmin/vmarteon/* /home/dbadmin/vmarteon_depot/*"
   [192.168.33.105] 16K    /home/dbadmin/vmarteon/dbLog
   [192.168.33.105] 4.0K    /home/dbadmin/vmarteon/port.dat
   [192.168.33.105] 4.0K    /home/dbadmin/vmarteon/procedures
   [192.168.33.105] 1.2G    /home/dbadmin/vmarteon/v_vmarteon_node0001_catalog
   [192.168.33.105] 8.0K    /home/dbadmin/vmarteon/v_vmarteon_node0001_data
   [192.168.33.105] 460K    /home/dbadmin/vmarteon_depot/vmarteon
   [192.168.33.106] 8.0K    /home/dbadmin/vmarteon/dbLog
   [192.168.33.106] 4.0K    /home/dbadmin/vmarteon/port.dat
   [192.168.33.106] 4.0K    /home/dbadmin/vmarteon/procedures
   [192.168.33.106] 1.2G    /home/dbadmin/vmarteon/v_vmarteon_node0002_catalog
   [192.168.33.106] 4.0K    /home/dbadmin/vmarteon/v_vmarteon_node0002_data
   [192.168.33.106] 348K    /home/dbadmin/vmarteon_depot/vmarteon
   [192.168.33.107] 8.0K    /home/dbadmin/vmarteon/dbLog
   [192.168.33.107] 4.0K    /home/dbadmin/vmarteon/port.dat
   [192.168.33.107] 4.0K    /home/dbadmin/vmarteon/procedures
   [192.168.33.107] 1.2G    /home/dbadmin/vmarteon/v_vmarteon_node0003_catalog
   [192.168.33.107] 4.0K    /home/dbadmin/vmarteon/v_vmarteon_node0003_data
   [192.168.33.107] 348K    /home/dbadmin/vmarteon_depot/vmarteon

   [dbadmin ~]# mc du --depth=2  mys3/vmarteon/
   115B    vmarteon/157
   131B    vmarteon/1c2
   118B    vmarteon/3cc
   38B    vmarteon/50d
   146B    vmarteon/6c2
   38B    vmarteon/7a1
   41B    vmarteon/7f2
   33B    vmarteon/8af
   145B    vmarteon/94e
   34B    vmarteon/997
   91B    vmarteon/9c5
   133B    vmarteon/a2d
   332KiB    vmarteon/a65
   61B    vmarteon/c27
   40B    vmarteon/d2e
   145B    vmarteon/d73
   332KiB    vmarteon/d9e
   61B    vmarteon/eba
   333KiB    vmarteon/edb
   581MiB    vmarteon/metadata
   582MiB    vmarteon
   ```
