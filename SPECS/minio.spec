Name:           minio
Version:        1.0.2
Release:        %{_minio_verson}.el%{_rhel_version}
Vendor:         Minio, Inc.
Summary:        Cloud Storage Server.
License:        Apache v2.0
Group:          Applications/File
Source0:        bin
Source1:        config
Source2:        minio.service
Source3:        ddstat
URL:            https://www.minio.io/
BuildRoot:      %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

%if 0%{?rhel} >= 7
BuildRequires:  systemd-units
Requires:       systemd
%endif
Requires(pre): shadow-utils, vertica >= 9.2.1-0

%description
Minio is an object storage server released under Apache License v2.0.
It is compatible with Amazon S3 cloud storage service. It is best
suited for storing unstructured data such as photos, videos, log
files, backups and container / VM images. Size of an object can
range from a few KBs to a maximum of 5TB.

## Turn off auto-compilation of Python files outside Python specific paths,
## so there's no risk that unexpected "__python" macro gets picked to do the
## RPM-native byte-compiling there (only "{_datadir}/pacemaker/tests" affected)
## -- distro-dependent tricks or automake's fallback to be applied there
%if %{defined _python_bytecompile_extra}
%global _python_bytecompile_extra 0
%else
### the statement effectively means no RPM-native byte-compiling will occur at
### all, so distro-dependent tricks for Python-specific packages to be applied
%global __os_install_post %(echo '%{__os_install_post}' | sed -e 's!/usr/lib[^[:space:]]*/brp-python-bytecompile[[:space:]].*$!!g')
%endif


%clean
rm -rf %{buildroot}


%prep
%setup -q -T -c


%install
mkdir -p %{buildroot}/opt/vertica
cp -a %{SOURCE0} %{buildroot}/opt/vertica/
cp -a %{SOURCE1} %{buildroot}/opt/vertica/

%if 0%{?rhel} >= 7
mkdir -p %{buildroot}/%{_unitdir}
cp -a %{SOURCE2} %{buildroot}/%{_unitdir}/
%endif

cp -a %{SOURCE3} %{buildroot}/opt/vertica/


%post
[ ! -f /opt/vertica/config/minio.conf ] && cp -a  /opt/vertica/config/minio.conf.default  /opt/vertica/config/minio.conf
[ ! -f /etc/profile.d/clustercli.sh -o  ! -h /etc/profile.d/clustercli.sh ] && ln -sf -t /etc/profile.d/ /opt/vertica/bin/clustercli.sh

#%if 0%{?rhel} >= 7
#%systemd_post minio.service
#%endif

cat <<-'EOF'

NOTICE: 
1. the first thing is run [sudo /opt/vertica/sbin/install_vertica --hosts server1,server2,...] to check system and define cluster.
2. before you start minio service, modify [/opt/vertica/config/minio.conf] as your situation.
3. sync config file [/opt/vertica/config/minio.conf] to all servers as :
    cls_cp /opt/vertica/config/minio.conf /opt/vertica/config/
4. start minio service on all servers as :
    # start service
    cls_run --background sudo systemctl start minio.service
    # show status of service
    cls_run 'hostname; sudo systemctl status minio.service'
    # troubleshoot acording to logs if require
    cls_run 'hostname; sudo journalctl --no-pager -u minio -n 12'
    # enable service start/restart dynamically
    cls_run sudo systemctl enable minio.service
EOF


%preun
[ -h /etc/profile.d/clustercli.sh ] && rm -rf /etc/profile.d/clustercli.sh 

%if 0%{?rhel} >= 7
%systemd_preun minio.service
%endif


%files
%defattr(644, dbadmin, verticadba, 755)
%attr(755, dbadmin, verticadba) /opt/vertica/bin/minio
%attr(755, dbadmin, verticadba) /opt/vertica/bin/mc
%attr(755, dbadmin, verticadba) /opt/vertica/bin/warp
%attr(755, dbadmin, verticadba) /opt/vertica/bin/clustercli.sh
# reject access from others as there are MINIO_ACCESS_KEY and MINIO_SECRET_KEY
%attr(600, dbadmin, verticadba) /opt/vertica/config/minio.conf.default

%if 0%{?rhel} >= 7
%attr(644, root, root) %{_unitdir}/minio.service
%endif

%attr(755, dbadmin, verticadba) /opt/vertica/bin/ddstat
%attr(755, dbadmin, verticadba) /opt/vertica/ddstat

%doc ../../README.md
