# Copyright 2013-2023 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack.package import *


class RteRrtmgp(AutotoolsPackage):
    """FIXME: Put a proper description of your package here."""

    homepage = "https://github.com/earth-system-radiation/rte-rrtmgp"
    url = "https://github.com/earth-system-radiation/rte-rrtmgp/wiki"
    # "home/biddisco/src/icon-exclaim/externals/rte-rrtmgp"
    git = "https://github.com/earth-system-radiation/rte-rrtmgp.git"
    maintainers = ["biddisco"]

    license("BSD-3-Clause")

    version("autoconf", branch="autoconf")

    # depends_on("foo")
#    variant("atmo", default=False, "enable atmo")
#    variant("edmf", default=False, "enable edmf")
#    variant("les",  default=False, "enable les")
#    variant("upatmo", default=False, "enable upatmo")
#    variant("ocean", default=False, "enable ocean")

    def install(self, spec, prefix):
        configure("--prefix=" + prefix)
        make()
        make("install")