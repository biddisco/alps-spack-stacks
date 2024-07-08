# Copyright 2013-2024 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

# ----------------------------------------------------------------------------
# If you submit this package back to Spack as a pull request,
# please first remove this boilerplate and all FIXME comments.
#
# This is a template package file for Spack.  We've put "FIXME"
# next to all the things you'll want to change. Once you've handled
# them, you can save this file and test your package like this:
#
#     spack install ecrad
#
# You can edit this file again by typing:
#
#     spack edit ecrad
#
# See the Spack documentation for more information on packaging.
# ----------------------------------------------------------------------------

from spack.package import *

class Ecrad(AutotoolsPackage):
    """FIXME: Put a proper description of your package here."""

    # FIXME: Add a proper url for your package's homepage here.
    homepage = "https://github.com/C2SM/libecrad.git"
    url = "https://github.com/C2SM/libecrad.git"
    git = "https://github.com/C2SM/libecrad.git"

    # FIXME: Add a list of GitHub accounts to
    # notify when the package is updated.
    # maintainers("github_user1", "github_user2")

    # FIXME: Add the SPDX identifier of the project's license below.
    # See https://spdx.org/licenses/ for a list. Upon manually verifying
    # the license, set checked_by to your Github username.
    license("UNKNOWN", checked_by="github_user1")

    version("master", branch="master")

    variant("single-precision", default=False, description="Enable single precision")
    variant("pgi-inlib", default=False, description="enable PGI cross-file function inlining via an inline library")

    depends_on("autoconf", type="build", when="build_system=autotools")
    depends_on("automake", type="build", when="build_system=autotools")
    depends_on("libtool", type="build", when="build_system=autotools")
    depends_on("netcdf-fortran")

    def configure_args(self):
        args = []
        args.extend(self.enable_or_disable("single-precision"))
        args.extend(self.enable_or_disable("pgi-inlib"))
        return args


    def install(self, spec, prefix):
        configure("--prefix=" + prefix)
        make()
        make("install")

