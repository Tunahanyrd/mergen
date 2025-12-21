#!/bin/bash
# Build .rpm package for Fedora/RHEL/CentOS

VERSION="0.7.0"
RELEASE="1"

# Create RPM build directories
mkdir -p ~/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

# Create spec file
cat > ~/rpmbuild/SPECS/mergen.spec << EOF
Name:           mergen
Version:        ${VERSION}
Release:        ${RELEASE}%{?dist}
Summary:        Multi-threaded download manager with browser integration

License:        GPL-3.0
URL:            https://github.com/Tunahanyrd/mergen
Source0:        %{name}-%{version}.tar.gz

BuildArch:      x86_64
Requires:       python3 >= 3.8

%description
Mergen is a modern download manager featuring multi-threaded downloads,
browser integration, resume support, and queue management.

%prep
%setup -q

%build
# Binary already built

%install
mkdir -p %{buildroot}/usr/bin
mkdir -p %{buildroot}/usr/share/applications
mkdir -p %{buildroot}/usr/share/icons/hicolor/128x128/apps
mkdir -p %{buildroot}/usr/share/mergen

install -m 755 dist/mergen %{buildroot}/usr/bin/
install -m 644 data/mergen.desktop %{buildroot}/usr/share/applications/
install -m 644 data/mergen.png %{buildroot}/usr/share/icons/hicolor/128x128/apps/
cp -r browser-extension %{buildroot}/usr/share/mergen/
cp -r native-host %{buildroot}/usr/share/mergen/

%files
/usr/bin/mergen
/usr/share/applications/mergen.desktop
/usr/share/icons/hicolor/128x128/apps/mergen.png
/usr/share/mergen/*

%post
update-desktop-database /usr/share/applications
gtk-update-icon-cache /usr/share/icons/hicolor

%changelog
* $(date "+%a %b %d %Y") Tunahanyrd <your-email@example.com> - ${VERSION}-${RELEASE}
- Initial release
EOF

# Copy source to SOURCES
tar -czf ~/rpmbuild/SOURCES/mergen-${VERSION}.tar.gz -C ../.. .

# Build RPM
rpmbuild -ba ~/rpmbuild/SPECS/mergen.spec

# Copy to current directory
cp ~/rpmbuild/RPMS/x86_64/mergen-${VERSION}-${RELEASE}.*.rpm ./

echo "✅ RPM package created: mergen-${VERSION}-${RELEASE}.*.rpm"
