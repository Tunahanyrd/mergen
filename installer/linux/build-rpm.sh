#!/bin/bash
# Build .rpm package for Fedora/RHEL/CentOS

VERSION="0.9.0"
RELEASE="1"

mkdir -p rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

cat > rpmbuild/SPECS/mergen.spec << EOF
Name:           mergen
Version:        ${VERSION}
Release:        ${RELEASE}
Summary:        Multi-threaded download manager with stream support (HLS/DASH)
License:        GPL-3.0
URL:            https://github.com/Tunahanyrd/mergen

# BuildArch ve bağımlılıklar
BuildArch:      x86_64
AutoReqProv:    no
Requires:       python3 >= 3.8, (ffmpeg or ffmpeg-free)

%description
Mergen is a modern download manager with browser integration and streaming media capture.

%install
mkdir -p %{buildroot}/usr/bin
mkdir -p %{buildroot}/usr/share/applications
mkdir -p %{buildroot}/usr/share/icons/hicolor/128x128/apps
mkdir -p %{buildroot}/usr/share/mergen

# Install actual binary as .bin
install -m 755 %{_sourcedir}/mergen %{buildroot}/usr/bin/mergen.bin

# Install wrapper script as main executable
install -m 755 %{_sourcedir}/mergen-wrapper.sh %{buildroot}/usr/bin/mergen

# Install other files
install -m 644 %{_sourcedir}/mergen.desktop %{buildroot}/usr/share/applications/
install -m 644 %{_sourcedir}/mergen.png %{buildroot}/usr/share/icons/hicolor/128x128/apps/
cp -r %{_sourcedir}/browser-extension %{buildroot}/usr/share/mergen/
cp -r %{_sourcedir}/native-host %{buildroot}/usr/share/mergen/

%files
/usr/bin/mergen
/usr/bin/mergen.bin
/usr/share/applications/mergen.desktop
/usr/share/icons/hicolor/128x128/apps/mergen.png
/usr/share/mergen/*

%post
update-desktop-database /usr/share/applications
gtk-update-icon-cache /usr/share/icons/hicolor
EOF

cp mergen rpmbuild/SOURCES/
cp mergen-wrapper.sh rpmbuild/SOURCES/
cp ../../data/mergen.desktop rpmbuild/SOURCES/
cp ../../data/mergen.png rpmbuild/SOURCES/
cp -r ../../browser-extension rpmbuild/SOURCES/
cp -r ../../native-host rpmbuild/SOURCES/

rpmbuild --define "_topdir $(pwd)/rpmbuild" -bb rpmbuild/SPECS/mergen.spec

cp rpmbuild/RPMS/x86_64/*.rpm ./

echo "✅ RPM package created."