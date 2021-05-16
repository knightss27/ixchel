#
#				stiff.spec.in
#
# Process this file with autoconf to generate an RPM .spec packaging script.
#
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
#	This file part of:	STIFF
#
#	Copyright:		(C) 2003-2013 Emmanuel Bertin -- IAP/CNRS/UPMC
#
#	License:		GNU General Public License
#
#	STIFF is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
# 	(at your option) any later version.
#	STIFF is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#	You should have received a copy of the GNU General Public License
#	along with STIFF. If not, see <http://www.gnu.org/licenses/>.
#
#	Last modified:		27/06/2013
#
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%define name stiff
%define version 2.4.0
%define release 1
%undefine _missing_build_ids_terminate_build

Summary: convert FITS images to TIFF format
Name: %{name}
Version: %{version}
Release: %{release}
Source0: ftp://ftp.iap.fr/pub/from_users/bertin/%{name}/%{name}-%{version}.tar.gz
URL: http://astromatic.net/software/%{name}
License: GPL v3+
Group: Sciences/Astronomy
BuildRoot: %{_tmppath}/%{name}-buildroot
BuildRequires: pkgconfig
BuildRequires: libtiff-devel
BuildRequires: zlib-devel

%description
STIFF is a program that convert scientific FITS images to the
more popular TIFF, in 8 (grayscale) or 24 (true colour) bits per pixel.

%prep
%setup -q

%build
if test "$USE_BEST"; then
%configure --enable-icc --enable-auto-flags --enable-best-link
elif test "$USE_ICC"; then
%configure --enable-icc
else
%configure
fi
make %{?_smp_mflags}

%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%doc AUTHORS BUGS ChangeLog COPYRIGHT HISTORY INSTALL LICENSE README THANKS doc/stiff.pdf
%{_bindir}/stiff
%{_mandir}/man1/stiff.1*
%{_mandir}/manx/stiff.x*
%{_datadir}/stiff

%changelog
* Fri May 14 2021 Emmanuel Bertin <bertin@iap.fr>
- Automatic RPM rebuild
* Mon Feb 17 2003 Emmanuel Bertin <bertin@iap.fr>
- Fourth RPM build
* Sat Feb 01 2003 Emmanuel Bertin <bertin@iap.fr>
- Third RPM build
* Mon Jan 27 2003 Emmanuel Bertin <bertin@iap.fr>
- Second RPM build
* Sun Jan 19 2003 Emmanuel Bertin <bertin@iap.fr>
- First RPM build

# end of file

