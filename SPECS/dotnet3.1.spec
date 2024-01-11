%bcond_with bootstrap

# Avoid provides/requires from private libraries
%global privlibs             libhostfxr
%global privlibs %{privlibs}|libclrjit
%global privlibs %{privlibs}|libcoreclr
%global privlibs %{privlibs}|libcoreclrtraceptprovider
%global privlibs %{privlibs}|libdbgshim
%global privlibs %{privlibs}|libhostpolicy
%global privlibs %{privlibs}|libmscordaccore
%global privlibs %{privlibs}|libmscordbi
%global privlibs %{privlibs}|libsos
%global privlibs %{privlibs}|libsosplugin
%global __provides_exclude ^(%{privlibs})\\.so
%global __requires_exclude ^(%{privlibs})\\.so

# Filter flags not supported by clang/dotnet:
#  -fstack-clash-protection is not supported by clang
#  -specs= is not supported by clang
%global dotnet_cflags %(echo %optflags | sed -e 's/-fstack-clash-protection//' | sed -re 's/-specs=[^ ]*//g')
%if 0%{?fedora} < 30 && ! 0%{?rhel}
# on Fedora 29, clang, -fcf-protection and binutils interact in strage ways leading to
# "<corrupt x86 feature size: 0x8>" errors.
%global dotnet_cflags %(echo %dotnet_cflags | sed -e 's/ -fcf-protection//')
%endif
%global dotnet_ldflags %(echo %{__global_ldflags} | sed -re 's/-specs=[^ ]*//g')

%global host_version 3.1.32
%global runtime_version 3.1.32
%global aspnetcore_runtime_version %{runtime_version}
%global sdk_version 3.1.426
%global templates_version %(echo %{runtime_version} | awk 'BEGIN { FS="."; OFS="." } {print $1, $2, $3+1 }')

%global host_rpm_version %{host_version}
%global runtime_rpm_version %{runtime_version}
%global aspnetcore_runtime_rpm_version %{aspnetcore_runtime_version}
%global sdk_rpm_version %{sdk_version}

%if 0%{?fedora} || 0%{?rhel} < 8
%global use_bundled_libunwind 0
%else
%global use_bundled_libunwind 1
%endif

%ifarch x86_64
%global runtime_arch x64
%endif
%ifarch aarch64
%global runtime_arch arm64
%endif

%if 0%{?fedora}
%global runtime_id fedora.%{fedora}-%{runtime_arch}
%else
%if 0%{?centos}
%global runtime_id centos.%{centos}-%{runtime_arch}
%else
%global runtime_id rhel.%{rhel}-%{runtime_arch}
%endif
%endif

Name:           dotnet3.1
Version:        %{sdk_rpm_version}
Release:        1%{?dist}
Summary:        .NET Core CLI tools and runtime
License:        MIT and ASL 2.0 and BSD
URL:            https://github.com/dotnet/

# ./build-dotnet-tarball dotnet-v%%{sdk_version}-SDK
Source0:        dotnet-v%{sdk_version}-SDK.tar.gz
#Source0:        dotnet-v%%{sdk_version}-SDK-x64-bootstrap.tar.gz

Source100:      check-debug-symbols.py
Source101:      dotnet.sh.in

Patch1:         source-build-ilasm-ildasm-path-fix.patch

Patch100:       corefx-optflags-support.patch
Patch103:       corefx-39633-cgroupv2-mountpoints.patch

Patch200:       coreclr-27048-sysctl-deprecation.patch
# Already applied at tarball build time
#Patch201:       coreclr-libunwind-fno-common.patch

Patch300:       core-setup-do-not-strip.patch
Patch301:       core-setup-no-werror.patch

Patch500:       cli-telemetry-optout.patch

ExclusiveArch:  x86_64

BuildRequires:  clang
BuildRequires:  cmake
BuildRequires:  coreutils
%if %{without bootstrap}
BuildRequires:  dotnet-build-reference-packages
BuildRequires:  dotnet-sdk-3.1
BuildRequires:  dotnet-sdk-3.1-source-built-artifacts
%endif
BuildRequires:  git
%if 0%{?fedora} || 0%{?rhel} > 7
BuildRequires:  glibc-langpack-en
%endif
BuildRequires:  hostname
BuildRequires:  krb5-devel
BuildRequires:  libcurl-devel
BuildRequires:  libicu-devel
%if ! %{use_bundled_libunwind}
BuildRequires:  libunwind-devel
%endif
BuildRequires:  lldb-devel
BuildRequires:  llvm
BuildRequires:  lttng-ust-devel
BuildRequires:  openssl-devel
BuildRequires:  python3
BuildRequires:  tar
BuildRequires:  zlib-devel

%description
.NET Core is a fast, lightweight and modular platform for creating
cross platform applications that work on Linux, macOS and Windows.

It particularly focuses on creating console applications, web
applications and micro-services.

.NET Core contains a runtime conforming to .NET Standards a set of
framework libraries, an SDK containing compilers and a 'dotnet'
application to drive everything.


%package -n dotnet

Version:        %{sdk_rpm_version}
Summary:        .NET Core CLI tools and runtime

Requires:       dotnet-sdk-3.1%{?_isa} >= %{sdk_rpm_version}-%{release}

%description -n dotnet
.NET Core is a fast, lightweight and modular platform for creating
cross platform applications that work on Linux, macOS and Windows.

It particularly focuses on creating console applications, web
applications and micro-services.

.NET Core contains a runtime conforming to .NET Standards a set of
framework libraries, an SDK containing compilers and a 'dotnet'
application to drive everything.


%package -n dotnet-host

Version:        %{host_rpm_version}
Summary:        .NET command line launcher

%description -n dotnet-host
The .NET Core host is a command line program that runs a standalone
.NET core application or launches the SDK.

.NET Core is a fast, lightweight and modular platform for creating
cross platform applications that work on Linux, Mac and Windows.

It particularly focuses on creating console applications, web
applications and micro-services.


%package -n dotnet-hostfxr-3.1

Version:        %{host_rpm_version}
Summary:        .NET Core command line host resolver

# Theoretically any version of the host should work. But lets aim for the one
# provided by this package, or from a newer version of .NET Core
Requires:       dotnet-host%{?_isa} >= %{host_rpm_version}-%{release}

%description -n dotnet-hostfxr-3.1
The .NET Core host resolver contains the logic to resolve and select
the right version of the .NET Core SDK or runtime to use.

.NET Core is a fast, lightweight and modular platform for creating
cross platform applications that work on Linux, Mac and Windows.

It particularly focuses on creating console applications, web
applications and micro-services.


%package -n dotnet-runtime-3.1

Version:        %{runtime_rpm_version}
Summary:        NET Core 3.1 runtime

Requires:       dotnet-hostfxr-3.1%{?_isa} >= %{host_rpm_version}-%{release}

# libicu is dlopen()ed
Requires:       libicu

# See src/corefx.*/src/Native/AnyOS/brotli-version.txt
Provides: bundled(libbrotli) = 1.0.9
%if %{use_bundled_libunwind}
Provides: bundled(libunwind) = 1.3
%endif

%description -n dotnet-runtime-3.1
The .NET Core runtime contains everything needed to run .NET Core applications.
It includes a high performance Virtual Machine as well as the framework
libraries used by .NET Core applications.

.NET Core is a fast, lightweight and modular platform for creating
cross platform applications that work on Linux, Mac and Windows.

It particularly focuses on creating console applications, web
applications and micro-services.


%package -n aspnetcore-runtime-3.1

Version:        %{aspnetcore_runtime_rpm_version}
Summary:        ASP.NET Core 3.1 runtime

Requires:       dotnet-runtime-3.1%{?_isa} >= %{runtime_rpm_version}-%{release}

%description -n aspnetcore-runtime-3.1
The ASP.NET Core runtime contains everything needed to run .NET Core
web applications. It includes a high performance Virtual Machine as
well as the framework libraries used by .NET Core applications.

ASP.NET Core is a fast, lightweight and modular platform for creating
cross platform web applications that work on Linux, Mac and Windows.

It particularly focuses on creating console applications, web
applications and micro-services.


%package -n dotnet-templates-3.1

Version:        %{sdk_rpm_version}
Summary:        .NET Core 3.1 templates

# Theoretically any version of the host should work. But lets aim for the one
# provided by this package, or from a newer version of .NET Core
Requires:       dotnet-host%{?_isa} >= %{host_rpm_version}-%{release}

%description -n dotnet-templates-3.1
This package contains templates used by the .NET Core SDK.

ASP.NET Core is a fast, lightweight and modular platform for creating
cross platform web applications that work on Linux, Mac and Windows.

It particularly focuses on creating console applications, web
applications and micro-services.


%package -n dotnet-sdk-3.1

Version:        %{sdk_rpm_version}
Summary:        .NET Core 3.1 Software Development Kit

Requires:       dotnet-runtime-3.1%{?_isa} >= %{runtime_rpm_version}-%{release}
Requires:       aspnetcore-runtime-3.1%{?_isa} >= %{aspnetcore_runtime_rpm_version}-%{release}

Requires:       dotnet-apphost-pack-3.1%{?_isa} >= %{runtime_rpm_version}-%{release}
Requires:       dotnet-targeting-pack-3.1%{?_isa} >= %{runtime_rpm_version}-%{release}
Requires:       aspnetcore-targeting-pack-3.1%{?_isa} >= %{aspnetcore_runtime_rpm_version}-%{release}
Requires:       netstandard-targeting-pack-2.1%{?_isa} >= %{sdk_rpm_version}-%{release}

Requires:       dotnet-templates-3.1%{?_isa} >= %{sdk_rpm_version}-%{release}

%description -n dotnet-sdk-3.1
The .NET Core SDK is a collection of command line applications to
create, build, publish and run .NET Core applications.

.NET Core is a fast, lightweight and modular platform for creating
cross platform applications that work on Linux, Mac and Windows.

It particularly focuses on creating console applications, web
applications and micro-services.


%define dotnet_targeting_pack() %{expand:
%package -n %{1}

Version:        %{2}
Summary:        Targeting Pack for %{3} %{4}

Requires:       dotnet-host

%description -n %{1}
This package provides a targetting pack for %{3} %{4}
that allows developers to compile against and target %{3} %{4}
applications using the .NET Core SDK.

%files -n %{1}
%dir %{_libdir}/dotnet/packs
%{_libdir}/dotnet/packs/%{5}
}

%dotnet_targeting_pack dotnet-apphost-pack-3.1 %{runtime_rpm_version} Microsoft.NETCore.App 3.1 Microsoft.NETCore.App.Host.%{runtime_id}
%dotnet_targeting_pack dotnet-targeting-pack-3.1 %{runtime_rpm_version} Microsoft.NETCore.App 3.1 Microsoft.NETCore.App.Ref
%dotnet_targeting_pack aspnetcore-targeting-pack-3.1 %{aspnetcore_runtime_rpm_version} Microsoft.AspNetCore.App 3.1 Microsoft.AspNetCore.App.Ref
#%%dotnet_targeting_pack netstandard-targeting-pack-2.1 %%{sdk_rpm_version} NETStandard.Library 2.1 NETStandard.Library.Ref

%package -n dotnet-sdk-3.1-source-built-artifacts

Version:        %{sdk_rpm_version}
Summary:        Internal package for building .NET Core 3.1 Software Development Kit

%description -n dotnet-sdk-3.1-source-built-artifacts
The .NET Core source-built archive is a collection of packages needed
to build the .NET Core SDK itself.

These are not meant for general use.


%prep
%if %{with bootstrap}

%ifarch x86_64
%setup T -b0 -q -n dotnet-v%{sdk_version}-SDK-%{runtime_arch}-bootstrap
%endif
%ifarch aarch64
%setup T -b1 -q -n dotnet-v%{sdk_version}-SDK-%{runtime_arch}-bootstrap
%endif

%else
%setup -q -n dotnet-v%{sdk_version}-SDK
%endif

%if %{without bootstrap}
# Remove all prebuilts
find -iname '*.dll' -type f -delete
find -iname '*.so' -type f -delete
find -iname '*.tar.gz' -type f -delete
find -iname '*.nupkg' -type f -delete
find -iname '*.zip' -type f -delete
rm -rf .dotnet/
rm -rf packages/source-built
%endif

%if %{without bootstrap}
mkdir -p packages/archive
ln -s %{_libdir}/dotnet/source-built-artifacts/*.tar.gz packages/archive/
ln -s %{_libdir}/dotnet/reference-packages/Private.SourceBuild.ReferencePackages*.tar.gz packages/archive
%endif

# Fix bad hardcoded path in build
sed -i 's|/usr/share/dotnet|%{_libdir}/dotnet|' src/dotnet-core-setup.*/src/corehost/common/pal.unix.cpp

# Disable warnings
sed -i 's|skiptests|skiptests ignorewarnings|' repos/coreclr.common.props

%patch1 -p1

pushd src/dotnet-corefx.*
%patch100 -p1
%patch103 -p1
popd

pushd src/dotnet-coreclr.*
%patch200 -p1
#%%patch201 -p1
popd

pushd src/dotnet-core-setup.*
%patch300 -p1
%patch301 -p1
popd

pushd src/dotnet-cli.*
%patch500 -p1
popd

# If CLR_CMAKE_USE_SYSTEM_LIBUNWIND=TRUE is misisng, add it back
grep CLR_CMAKE_USE_SYSTEM_LIBUNWIND repos/coreclr.common.props || \
    sed -i 's|\$(BuildArguments) </BuildArguments>|$(BuildArguments) cmakeargs -DCLR_CMAKE_USE_SYSTEM_LIBUNWIND=TRUE</BuildArguments>|' repos/coreclr.common.props

%if %{use_bundled_libunwind}
sed -i 's|-DCLR_CMAKE_USE_SYSTEM_LIBUNWIND=TRUE|-DCLR_CMAKE_USE_SYSTEM_LIBUNWIND=FALSE|' repos/coreclr.common.props
%endif

cat source-build-info.txt

find -iname 'nuget.config' -exec echo {}: \; -exec cat {} \; -exec echo \;


%build
cat /etc/os-release

%if %{without bootstrap}
# We need to create a copy because we will mutate this
cp -a %{_libdir}/dotnet previously-built-dotnet
%endif

export CFLAGS="%{dotnet_cflags}"
export CXXFLAGS="%{dotnet_cflags}"
export LDFLAGS="%{dotnet_ldflags}"

VERBOSE=1 ./build.sh \
%if %{without bootstrap}
    --with-sdk previously-built-dotnet \
%endif
    -- \
    /v:n \
    /p:SkipPortableRuntimeBuild=true \
    /p:LogVerbosity=n \
    /p:MinimalConsoleLogOutput=false \
    /p:ContinueOnPrebuiltBaselineError=true \


sed -e 's|[@]LIBDIR[@]|%{_libdir}|g' %{SOURCE101} > dotnet.sh


%install
install -dm 0755 %{buildroot}%{_libdir}/dotnet
find artifacts/%{runtime_arch}/Release
tar xf artifacts/%{runtime_arch}/Release/dotnet-sdk-%{sdk_version}-%{runtime_id}.tar.gz -C %{buildroot}%{_libdir}/dotnet/

# Install managed symbols
tar xf artifacts/%{runtime_arch}/Release/runtime/dotnet-runtime-symbols-%{runtime_version}-%{runtime_id}.tar.gz \
    -C %{buildroot}/%{_libdir}/dotnet/shared/Microsoft.NETCore.App/%{runtime_version}/

# Fix executable permissions on files
find %{buildroot}%{_libdir}/dotnet/ -type f -name '*.dll' -exec chmod -x {} \;
find %{buildroot}%{_libdir}/dotnet/ -type f -name '*.pdb' -exec chmod -x {} \;
find %{buildroot}%{_libdir}/dotnet/ -type f -name '*.props' -exec chmod -x {} \;
find %{buildroot}%{_libdir}/dotnet/ -type f -name '*.pubxml' -exec chmod -x {} \;
find %{buildroot}%{_libdir}/dotnet/ -type f -name '*.targets' -exec chmod -x {} \;
chmod 0755 %{buildroot}/%{_libdir}/dotnet/sdk/%{sdk_version}/AppHostTemplate/apphost
chmod 0644 %{buildroot}/%{_libdir}/dotnet/packs/Microsoft.AspNetCore.App.Ref/3.1.10/data/FrameworkList.xml
chmod 0644 %{buildroot}/%{_libdir}/dotnet/packs/Microsoft.AspNetCore.App.Ref/3.1.10/data/PackageOverrides.txt
chmod 0644 %{buildroot}/%{_libdir}/dotnet/packs/Microsoft.AspNetCore.App.Ref/3.1.10/data/PlatformManifest.txt
chmod 0644 %{buildroot}/%{_libdir}/dotnet/packs/Microsoft.AspNetCore.App.Ref/3.1.10/ref/netcoreapp3.1/*.xml
chmod 0644 %{buildroot}/%{_libdir}/dotnet/packs/Microsoft.NETCore.App.Host.%{runtime_id}/%{runtime_version}/runtimes/%{runtime_id}/native/nethost.h
chmod 0644 %{buildroot}/%{_libdir}/dotnet/packs/Microsoft.NETCore.App.Ref/3.1.0/data/FrameworkList.xml
chmod 0644 %{buildroot}/%{_libdir}/dotnet/packs/Microsoft.NETCore.App.Ref/3.1.0/data/PackageOverrides.txt
chmod 0644 %{buildroot}/%{_libdir}/dotnet/packs/Microsoft.NETCore.App.Ref/3.1.0/data/PlatformManifest.txt
chmod 0644 %{buildroot}/%{_libdir}/dotnet/packs/NETStandard.Library.Ref/2.1.0/data/FrameworkList.xml
chmod 0644 %{buildroot}/%{_libdir}/dotnet/packs/NETStandard.Library.Ref/2.1.0/data/PackageOverrides.txt
chmod 0755 %{buildroot}/%{_libdir}/dotnet/packs/Microsoft.NETCore.App.Host.%{runtime_id}/%{runtime_version}/runtimes/%{runtime_id}/native/apphost
chmod 0755 %{buildroot}/%{_libdir}/dotnet/packs/Microsoft.NETCore.App.Host.%{runtime_id}/%{runtime_version}/runtimes/%{runtime_id}/native/libnethost.so

# Provided by dotnet-host from another SRPM
#install -dm 0755 %%{buildroot}%%{_sysconfdir}/profile.d/
#install dotnet.sh %%{buildroot}%%{_sysconfdir}/profile.d/

# Provided by dotnet-host from another SRPM
#install -dm 0755 %%{buildroot}/%%{_datadir}/bash-completion/completions
# dynamic completion needs the file to be named the same as the base command
#install src/dotnet-cli.*/scripts/register-completions.bash %%{buildroot}/%%{_datadir}/bash-completion/completions/dotnet

# TODO: the zsh completion script needs to be ported to use #compdef
#install -dm 755 %%{buildroot}/%%{_datadir}/zsh/site-functions
#install src/dotnet-cli/scripts/register-completions.zsh %%{buildroot}/%%{_datadir}/zsh/site-functions/_dotnet

# Provided by dotnet-host from another SRPM
#install -dm 0755 %%{buildroot}%%{_bindir}
#ln -s ../../%%{_libdir}/dotnet/dotnet %%{buildroot}%%{_bindir}/

# Provided by dotnet-host from another SRPM
#install -dm 0755 %%{buildroot}%%{_mandir}/man1/
#find -iname 'dotnet*.1' -type f -exec cp {} %%{buildroot}%%{_mandir}/man1/ \;

# Provided by dotnet-host from another SRPM
#echo "%%{_libdir}/dotnet" >> install_location
#install -dm 0755 %%{buildroot}%%{_sysconfdir}/dotnet
#install install_location %%{buildroot}%%{_sysconfdir}/dotnet/

install -dm 0755 %{buildroot}%{_libdir}/dotnet/source-built-artifacts
install artifacts/%{runtime_arch}/Release/Private.SourceBuilt.Artifacts.*.tar.gz %{buildroot}/%{_libdir}/dotnet/source-built-artifacts/

# Check debug symbols in all elf objects. This is not in %%check
# because native binaries are stripped by rpm-build after %%install.
# So we need to do this check earlier.
echo "Testing build results for debug symbols..."
%{SOURCE100} -v %{buildroot}%{_libdir}/dotnet/

# Self-check
%{buildroot}%{_libdir}/dotnet/dotnet --info

# Provided by dotnet-host from another SRPM
rm %{buildroot}%{_libdir}/dotnet/LICENSE.txt
rm %{buildroot}%{_libdir}/dotnet/ThirdPartyNotices.txt
rm %{buildroot}%{_libdir}/dotnet/dotnet

# Provided by netstandard-targeting-pack-2.1 from another SRPM
rm -rf %{buildroot}%{_libdir}/dotnet/packs/NETStandard.Library.Ref/2.1.0

%files -n dotnet-hostfxr-3.1
%dir %{_libdir}/dotnet/host/fxr
%{_libdir}/dotnet/host/fxr/%{host_version}

%files -n dotnet-runtime-3.1
%dir %{_libdir}/dotnet/shared
%dir %{_libdir}/dotnet/shared/Microsoft.NETCore.App
%{_libdir}/dotnet/shared/Microsoft.NETCore.App/%{runtime_version}

%files -n aspnetcore-runtime-3.1
%dir %{_libdir}/dotnet/shared
%dir %{_libdir}/dotnet/shared/Microsoft.AspNetCore.App
%{_libdir}/dotnet/shared/Microsoft.AspNetCore.App/%{aspnetcore_runtime_version}

%files -n dotnet-templates-3.1
%dir %{_libdir}/dotnet/templates
%{_libdir}/dotnet/templates/%{templates_version}

%files -n dotnet-sdk-3.1
%dir %{_libdir}/dotnet/sdk
%{_libdir}/dotnet/sdk/%{sdk_version}
%dir %{_libdir}/dotnet/packs

%files -n dotnet-sdk-3.1-source-built-artifacts
%dir %{_libdir}/dotnet
%{_libdir}/dotnet/source-built-artifacts

%changelog
* Wed Nov 30 2022 Omair Majid <omajid@redhat.com> - 3.1.426-1
- Update to .NET SDK 3.1.426 and Runtime 3.1.32
- Resolves: RHBZ#2148219

* Wed Sep 14 2022 Omair Majid <omajid@redhat.com> - 3.1.423-2
- Update to .NET SDK 3.1.423 and Runtime 3.1.29
- Resolves: RHBZ#2123784

* Tue Aug 09 2022 Omair Majid <omajid@redhat.com> - 3.1.422-2
- Update to .NET SDK 3.1.422 and Runtime 3.1.28
- Resolves: RHBZ#2115350

* Thu Jul 21 2022 Omair Majid <omajid@redhat.com> - 3.1.421-2
- Update to .NET SDK 3.1.421 and Runtime 3.1.27
- Resolves: RHBZ#2103273

* Thu Jun 23 2022 Omair Majid <omajid@redhat.com> - 3.1.420-1
- Update to .NET SDK 3.1.420 and Runtime 3.1.26
- Resolves: RHBZ#2096318

* Mon May 16 2022 Omair Majid <omajid@redhat.com> - 3.1.419-1
- Update to .NET SDK 3.1.419 and Runtime 3.1.25
- Resolves: RHBZ#2081442

* Wed Apr 27 2022 Omair Majid <omajid@redhat.com> - 3.1.418-2
- Bump release
- Related: RHBZ#2072012

* Mon Apr 25 2022 Omair Majid <omajid@redhat.com> - 3.1.418-1
- Update to .NET SDK 3.1.418 and Runtime 3.1.24
- Resolves: RHBZ#2072012

* Tue Jan 25 2022 Omair Majid <omajid@redhat.com> - 3.1.416-4
- Update to .NET SDK 3.1.416 and Runtime 3.1.22
- Resolves: RHBZ#2011820
- Resolves: RHBZ#2003077
- Resolves: RHBZ#2031428

* Sat Aug 14 2021 Omair Majid <omajid@redhat.com> - 3.1.118-1
- Update to .NET SDK 3.1.118 and Runtime 3.1.18
- Resolves: RHBZ#1990174

* Wed Aug 11 2021 Omair Majid <omajid@redhat.com> - 3.1.117-1
- Update to .NET SDK 3.1.117 and Runtime 3.1.17
- Resolves: RHBZ#1978389

* Fri Jun 11 2021 Omair Majid <omajid@redhat.com> - 3.1.116-1
- Update to .NET SDK 3.1.116 and Runtime 3.1.16
- Resolves: RHBZ#1965499
- Resolves: RHBZ#1966998

* Wed Jun 02 2021 Omair Majid <omajid@redhat.com> - 3.1.115-1
- Update to .NET SDK 3.1.115 and Runtime 3.1.15
- Resolves: RHBZ#1954324

* Thu Apr 22 2021 Omair Majid <omajid@redhat.com> - 3.1.114-2
- Update to .NET SDK 3.1.114 and Runtime 3.1.14
- Add dotnet-sdk-3.1-source-built-artifacts subpackage
- Resolves: RHBZ#1946721

* Wed Feb 10 2021 Omair Majid <omajid@redhat.com> - 3.1.112-2
- Update to .NET Core SDK 3.1.112 and Runtime 3.1.12
- Resolves: RHBZ#1923370

* Wed Jan 13 2021 Omair Majid <omajid@redhat.com> - 3.1.111-2
- Update to .NET Core SDK 3.1.111 and Runtime 3.1.11
- Resolves: RHBZ#1907627

* Fri Nov 06 2020 Omair Majid <omajid@redhat.com> - 3.1.110-2
- Update to .NET Core SDK 3.1.110 and Runtime 3.1.10
- Resolves: RHBZ#1893778

* Tue Oct 13 2020 Omair Majid <omajid@redhat.com> - 3.1.109-3
- Update to .NET Core SDK 3.1.109 and Runtime 3.1.9
- Resolves: RHBZ#1886546

* Fri Sep 18 2020 Omair Majid <omajid@redhat.com> - 3.1.108-3
- Bump release to preserve upgrade path
- Resolves: RHBZ#1874503

* Fri Sep 04 2020 Omair Majid <omajid@redhat.com> - 3.1.108-2
- Stop producing netstandard-targeting-pack-2.1
- Resolves: RHBZ#1874503

* Fri Sep 04 2020 Omair Majid <omajid@redhat.com> - 3.1.108-1
- Update to .NET Core SDK 3.1.108 and Runtime 3.1.8
- Resolves: RHBZ#1874503
- Resolves: RHBZ#1873454

* Mon Aug 17 2020 Omair Majid <omajid@redhat.com> - 3.1.107-2
- Remove subpackages that conflict with dotnet5.0
- Resolves: RHBZ#1862590

* Thu Aug 13 2020 Omair Majid <omajid@redhat.com> - 3.1.107-1
- Update to .NET Core SDK 3.1.107 and Runtime 3.1.7
- Resolves: RHBZ#1862590
- Resolves: RHBZ#1861114

* Thu Jul 30 2020 Omair Majid <omajid@redhat.com> - 3.1.106-6
- Remove duplicate LDFLAGS (actually typoed ASMFLAGS) for build
- Resolves: RHBZ#1811776

* Wed Jul 29 2020 Omair Majid <omajid@redhat.com> - 3.1.106-5
- Export ASMFLAGS during build
- Resolves: RHBZ#1811776

* Tue Jul 28 2020 Omair Majid <omajid@redhat.com> - 3.1.106-4
- Enable -fcf-protection
- Resolves: RHBZ#1811776

* Mon Jul 27 2020 Omair Majid <omajid@redhat.com> - 3.1.106-3
- Improve hardening in core-setup and corefx
- Resolves: RHBZ#1811776

* Fri Jul 24 2020 Omair Majid <omajid@redhat.com> - 3.1.106-2
- Improve hardening in CoreCLR
- Resolves: RHBZ#1811776

* Thu Jul 16 2020 Omair Majid <omajid@redhat.com> - 3.1.106-1
- Update to .NET Core SDK 3.1.106 and Runtime 3.1.6
- Resolves: RHBZ#1853772
- Resolves: RHBZ#1856939

* Tue Jun 09 2020 Omair Majid <omajid@redhat.com> - 3.1.105-1
- Update to .NET Core Runtime 3.1.5 and SDK 3.1.105
- Resolves: RHBZ#1844491

* Mon Jun 01 2020 Omair Majid <omajid@redhat.com> - 3.1.104-3
- Update to .NET Core Runtime 3.1.4 and SDK 3.1.104
- Resolves: RHBZ#1832685

* Fri Mar 20 2020 Omair Majid <omajid@redhat.com> - 3.1.103-2
- Update to .NET Core Runtime 3.1.3 and SDK 3.1.103
- Resolves: RHBZ#1815632

* Wed Feb 19 2020 Omair Majid <omajid@redhat.com> - 3.1.102-2
- Update to .NET Core Runtime 3.1.2 and SDK 3.1.102
- Resolves: RHBZ#1804452

* Thu Jan 23 2020 Omair Majid <omajid@redhat.com> - 3.1.101-2
- Update to .NET Core Runtime 3.1.1 and SDK 3.1.101
- Resolves: RHBZ#1789154

* Wed Dec 04 2019 Omair Majid <omajid@redhat.com> - 3.1.100-2
- Remove arm64 variant of the source tarball
- Resolves: RHBZ#1711405

* Tue Dec 03 2019 Omair Majid <omajid@redhat.com> - 3.1.100-1
- Update to .NET Core Runtime 3.1.0 and SDK 3.1.100
- Resolves: RHBZ#1711405

* Wed Nov 27 2019 Omair Majid <omajid@redhat.com> - 3.1.100-0.7.preview3
- Extract self-contained executables under $HOME
- Resolves: RHBZ#1711405

* Wed Nov 27 2019 Omair Majid <omajid@redhat.com> - 3.1.100-0.6.preview3
- Drop local fixes for cgroupv2
- Resolves: RHBZ#1711405

* Mon Nov 18 2019 Omair Majid <omajid@redhat.com> - 3.1.100-0.5.preview3
- Fix permissions on apphost
- Resolves: RHBZ#1711405

* Mon Nov 18 2019 Omair Majid <omajid@redhat.com> - 3.1.100-0.4.preview3
- Update to .NET Core Runtime 3.1.0-preview3.19553.2 and SDK 3.1.100-preview3-014645
- Resolves: RHBZ#1711405

* Wed Nov 13 2019 Omair Majid <omajid@redhat.com> - 3.1.100-0.3
- Add gating tests
- Resolves: RHBZ#1711405

* Wed Nov 13 2019 Omair Majid <omajid@redhat.com> - 3.1.100-0.2
- Initial import from Fedora into RHEL
- Resolves: RHBZ#1711405

* Wed Nov 06 2019 Omair Majid <omajid@redhat.com> - 3.1.100-0.2
- Update to .NET Core 3.1 Preview 2

* Wed Oct 30 2019 Omair Majid <omajid@redhat.com> - 3.1.100-0.1
- Update to .NET Core 3.1 Preview 1

* Thu Oct 24 2019 Omair Majid <omajid@redhat.com> - 3.0.100-5
- Add cgroupv2 support to .NET Core

* Wed Oct 16 2019 Omair Majid <omajid@redhat.com> - 3.0.100-4
- Include fix from coreclr for building on Fedora 32

* Wed Oct 16 2019 Omair Majid <omajid@redhat.com> - 3.0.100-3
- Harden built binaries to pass annocheck

* Fri Oct 11 2019 Omair Majid <omajid@redhat.com> - 3.0.100-2
- Export DOTNET_ROOT in profile to make apphost lookup work

* Fri Sep 27 2019 Omair Majid <omajid@redhat.com> - 3.0.100-1
- Update to .NET Core Runtime 3.0.0 and SDK 3.0.100

* Wed Sep 25 2019 Omair Majid <omajid@redhat.com> - 3.0.100-0.18.rc1
- Update to .NET Core Runtime 3.0.0-rc1-19456-20 and SDK 3.0.100-rc1-014190

* Tue Sep 17 2019 Omair Majid <omajid@redhat.com> - 3.0.100-0.16.preview9
- Fix files duplicated between dotnet-apphost-pack-3.0 and dotnet-targeting-pack-3.0
- Fix dependencies between .NET SDK and the targeting packs

* Mon Sep 16 2019 Omair Majid <omajid@redhat.com> - 3.0.100-0.15.preview9
- Update to .NET Core Runtime 3.0.0-preview 9 and SDK 3.0.100-preview9

* Mon Aug 19 2019 Omair Majid <omajid@redhat.com> - 3.0.100-0.11.preview8
- Update to .NET Core Runtime 3.0.0-preview8-28405-07 and SDK
  3.0.100-preview8-013656

* Tue Jul 30 2019 Omair Majid <omajid@redhat.com> - 3.0.100-0.9.preview7
- Update to .NET Core Runtime 3.0.0-preview7-27912-14 and SDK
  3.0.100-preview7-012821

* Fri Jul 26 2019 Omair Majid <omajid@redhat.com> - 3.0.100-0.8.preview7
- Update to .NET Core Runtime 3.0.0-preview7-27902-19 and SDK
  3.0.100-preview7-012802

* Wed Jun 26 2019 Omair Majid <omajid@redhat.com> - 3.0.0-0.7.preview6
- Obsolete dotnet-sdk-3.0.1xx
- Add supackages for targeting packs
- Add -fcf-protection to CFLAGS

* Wed Jun 26 2019 Omair Majid <omajid@redhat.com> - 3.0.0-0.6.preview6
- Update to .NET Core Runtime 3.0.0-preview6-27804-01 and SDK 3.0.100-preview6-012264
- Set dotnet installation location in /etc/dotnet/install_location
- Update targetting packs
- Install managed symbols
- Completely conditionalize libunwind bundling

* Tue May 07 2019 Omair Majid <omajid@redhat.com> - 3.0.0-0.3.preview4
- Update to .NET Core 3.0 preview 4

* Tue Dec 18 2018 Omair Majid <omajid@redhat.com> - 3.0.0-0.1.preview1
- Update to .NET Core 3.0 preview 1

* Fri Dec 07 2018 Omair Majid <omajid@redhat.com> - 2.2.100
- Update to .NET Core 2.2.0

* Wed Nov 07 2018 Omair Majid <omajid@redhat.com> - 2.2.100-0.2.preview3
- Update to .NET Core 2.2.0-preview3

* Fri Nov 02 2018 Omair Majid <omajid@redhat.com> - 2.1.403-3
- Add host-fxr-2.1 subpackage

* Mon Oct 15 2018 Omair Majid <omajid@redhat.com> - 2.1.403-2
- Disable telemetry by default
- Users have to manually export DOTNET_CLI_TELEMETRY_OPTOUT=0 to enable

* Tue Oct 02 2018 Omair Majid <omajid@redhat.com> - 2.1.403-1
- Update to .NET Core Runtime 2.1.5 and SDK 2.1.403

* Wed Sep 26 2018 Omair Majid <omajid@redhat.com> - 2.1.402-2
- Add ~/.dotnet/tools to $PATH to make it easier to use dotnet tools

* Thu Sep 13 2018 Omair Majid <omajid@redhat.com> - 2.1.402-1
- Update to .NET Core Runtime 2.1.4 and SDK 2.1.402

* Wed Sep 05 2018 Omair Majid <omajid@redhat.com> - 2.1.401-2
- Use distro-standard flags when building .NET Core

* Tue Aug 21 2018 Omair Majid <omajid@redhat.com> - 2.1.401-1
- Update to .NET Core Runtime 2.1.3 and SDK 2.1.401

* Mon Aug 20 2018 Omair Majid <omajid@redhat.com> - 2.1.302-1
- Update to .NET Core Runtime 2.1.2 and SDK 2.1.302

* Fri Jul 20 2018 Omair Majid <omajid@redhat.com> - 2.1.301-1
- Update to .NET Core 2.1

* Thu May 03 2018 Omair Majid <omajid@redhat.com> - 2.0.7-1
- Update to .NET Core 2.0.7

* Wed Mar 28 2018 Omair Majid <omajid@redhat.com> - 2.0.6-2
- Enable bash completion for dotnet
- Remove redundant buildrequires and requires

* Wed Mar 14 2018 Omair Majid <omajid@redhat.com> - 2.0.6-1
- Update to .NET Core 2.0.6

* Fri Feb 23 2018 Omair Majid <omajid@redhat.com> - 2.0.5-1
- Update to .NET Core 2.0.5

* Wed Jan 24 2018 Omair Majid <omajid@redhat.com> - 2.0.3-5
- Don't apply corefx clang warnings fix on clang < 5

* Fri Jan 19 2018 Omair Majid <omajid@redhat.com> - 2.0.3-4
- Add a test script to sanity check debug and symbol info.
- Build with clang 5.0
- Make main package real instead of using a virtual provides (see RHBZ 1519325)

* Wed Nov 29 2017 Omair Majid <omajid@redhat.com> - 2.0.3-3
- Add a Provides for 'dotnet'
- Fix conditional macro

* Tue Nov 28 2017 Omair Majid <omajid@redhat.com> - 2.0.3-2
- Fix build on Fedora 27

* Fri Nov 17 2017 Omair Majid <omajid@redhat.com> - 2.0.3-1
- Update to .NET Core 2.0.3

* Thu Oct 19 2017 Omair Majid <omajid@redhat.com> - 2.0.0-4
- Add a hack to let omnisharp work

* Wed Aug 30 2017 Omair Majid <omajid@redhat.com> - 2.0.0-3
- Add a patch for building coreclr and core-setup correctly on Fedora >= 27

* Fri Aug 25 2017 Omair Majid <omajid@redhat.com> - 2.0.0-2
- Move libicu/libcurl/libunwind requires to runtime package
- Make sdk depend on the exact version of the runtime package

* Thu Aug 24 2017 Omair Majid <omajid@redhat.com> - 2.0.0-1
- Update to 2.0.0 final release

* Wed Jul 26 2017 Omair Majid <omajid@redhat.com> - 2.0.0-0.3.preview2
- Add man pages

* Tue Jul 25 2017 Omair Majid <omajid@redhat.com> - 2.0.0-0.2.preview2
- Add Requires on libicu
- Split into multiple packages
- Do not repeat first-run message

* Fri Jul 21 2017 Omair Majid <omajid@redhat.com> - 2.0.0-0.1.preview2
- Update to .NET Core 2.0 Preview 2

* Thu Mar 16 2017 Nemanja Milošević <nmilosevnm@gmail.com> - 1.1.0-7
- rebuilt with latest libldb
* Wed Feb 22 2017 Nemanja Milosevic <nmilosev@fedoraproject.org> - 1.1.0-6
- compat-openssl 1.0 for F26 for now
* Sun Feb 19 2017 Nemanja Milosevic <nmilosev@fedoraproject.org> - 1.1.0-5
- Fix wrong commit id's
* Sat Feb 18 2017 Nemanja Milosevic <nmilosev@fedoraproject.org> - 1.1.0-4
- Use commit id's instead of branch names
* Sat Feb 18 2017 Nemanja Milosevic <nmilosev@fedoraproject.org> - 1.1.0-3
- Improper patch5 fix
* Sat Feb 18 2017 Nemanja Milosevic <nmilosev@fedoraproject.org> - 1.1.0-2
- SPEC cleanup
- git removal (using all tarballs for reproducible builds)
- more reasonable versioning
* Thu Feb 09 2017 Nemanja Milosevic <nmilosev@fedoraproject.org> - 1.1.0-1
- Fixed debuginfo going to separate package (Patch1)
- Added F25/F26 RIL and fixed the version info (Patch2)
- Added F25/F26 RIL in Microsoft.NETCore.App suported runtime graph (Patch3)
- SPEC file cleanup
* Wed Jan 11 2017 Nemanja Milosevic <nmilosev@fedoraproject.org> - 1.1.0-0
- Initial RPM for Fedora 25/26.

