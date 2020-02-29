#!/usr/bin/env bash


curDir="$(pwd)"
repo_dir="$(cd "$(dirname $0)"; pwd)"

if [ ! -f "${repo_dir}/SOURCES/bin/minio" -o ! -f "${repo_dir}/SOURCES/bin/mc" ] ; then
    echo "Get the latest release of minio/mc ..."

    [ -f "${repo_dir}/SOURCES/bin/minio" ] && rm -rf "${repo_dir}/SOURCES/bin/minio"
    URL_MINIO="https://dl.minio.io/server/minio/release/linux-amd64/archive"
    VER_MINIO="$(curl -s ${URL_MINIO}/ | grep 'minio.RELEASE.' | egrep -v '\.sha.*sum|\.asc' | sort | tail -1 | sed 's/<[^<>]*>//g' | sed 's/ //g')"
    if [ -z "${VER_MINIO}" ] ; then
        echo "get the latest release version of minio failed!" >&2
        exit 1
    fi
    echo "downding [${URL_MINIO}/${VER_MINIO}] ..."
    curl -L -o "${repo_dir}/SOURCES/bin/minio" ${URL_MINIO}/${VER_MINIO}
    if [ "$(sha1sum "${repo_dir}/SOURCES/bin/minio" | awk '{print $1}')" != "$(curl -s ${URL_MINIO}/${VER_MINIO}.shasum | awk '{print $1}')" ] ; then
        echo "downloaded minio is not correct!" >&2
        exit 1
    fi
    chmod a+x "${repo_dir}/SOURCES/bin/minio"

    [ -f "${repo_dir}/SOURCES/bin/mc" ] && rm -rf "${repo_dir}/SOURCES/bin/mc"
    URL_MC="https://dl.minio.io/client/mc/release/linux-amd64/archive"
    VER_MC="$(curl -s ${URL_MC}/ | grep 'mc.RELEASE.' | egrep -v '\.sha.*sum|\.asc' | sort | tail -1 | sed 's/<[^<>]*>//g' | sed 's/ //g')"
    if [ -z "${VER_MC}" ] ; then
        echo "get the latest release version of mc failed!" >&2
        exit 1
    fi
    echo "downding [${URL_MC}/${VER_MC}] ..."
    curl -L -o "${repo_dir}/SOURCES/bin/mc" ${URL_MC}/${VER_MC}
    if [ "$(sha1sum "${repo_dir}/SOURCES/bin/mc" | awk '{print $1}')" != "$(curl -s ${URL_MC}/${VER_MC}.shasum | awk '{print $1}')" ] ; then
        echo "downloaded mc is not correct!" >&2
        exit 1
    fi
    chmod a+x "${repo_dir}/SOURCES/bin/mc"

    [ -f "${repo_dir}/SOURCES/bin/warp" ] && rm -rf "${repo_dir}/SOURCES/bin/warp"
    VER_WARP="$(curl -s "https://api.github.com/repos/minio/warp/releases/latest" | grep '"tag_name":' | sed -E 's/.*"v([^"]+)".*/\1/')"
    if [ -z "${VER_WARP}" ] ; then
        echo "get the latest release version of warp failed!" >&2
        exit 1
    fi
    URL_WARP="https://github.com/minio/warp/releases/download/v${VER_WARP}/warp_${VER_WARP}_Linux_amd64.tar.gz"
    echo "downding [${URL_WARP}] ..."
    if ! curl -L -o "${repo_dir}/SOURCES/bin/warp.tgz" ${URL_WARP} ; then
        echo "downloaded warp is not correct!" >&2
        exit 1
    fi
    tar -xzvf warp.tgz warp
    [ -f "${repo_dir}/SOURCES/bin/warp.tgz" ] && rm -rf "${repo_dir}/SOURCES/bin/warp.tgz"
    chmod a+x "${repo_dir}/SOURCES/bin/warp"
fi


echo "Building RPM ..."

RHEL_VERSION=7
PLATFORM="el${RHEL_VERSION}"
minio_verson="$("${repo_dir}/SOURCES/bin/minio" --version | awk '{print $3}' | sed -e 's/[^0-9]//g')"

[ -d "${HOME}/rpmbuild" ] && rm -rf "${HOME}/rpmbuild"
mkdir "${HOME}/rpmbuild"
cp -a ${repo_dir}/SPECS ${HOME}/rpmbuild/
cp -a ${repo_dir}/SOURCES ${HOME}/rpmbuild/
cp -a ${repo_dir}/README.md ${HOME}/rpmbuild/
find ${HOME}/rpmbuild/SOURCES/ -name '.*' -exec rm -rf '{}' \; 2>/dev/null
find ${HOME}/rpmbuild/SOURCES/ -name '*.pyc' -delete
find ${HOME}/rpmbuild/SOURCES/ -name '*.pyo' -delete

cd ${HOME}
rpmbuild -bb \
    --define "_minio_verson ${minio_verson}" \
    --define "_rhel_version ${RHEL_VERSION}" \
    -ba rpmbuild/SPECS/minio.spec
if [ $? -ne 0 ] ; then
    echo "building failed!" >&2
    cd ${curDir}
    exit 1
fi

echo "Copying generated files to [${curDir}/dist/] ..."

mkdir -p "${curDir}/dist"
cp -af "${HOME}/rpmbuild"/RPMS/*/*.rpm "${curDir}/dist/"
[ -d "${HOME}/rpmbuild" ] && rm -rf "${HOME}/rpmbuild"

cd ${curDir}
echo "Done."
