# Copyright 2013-2023 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack.package import *


class Mtime(AutotoolsPackage):
    """FIXME: Put a proper description of your package here."""

    homepage = "https://gitlab.dkrz.de/icon-libraries/libmtime"
    url = "https://gitlab.dkrz.de/icon-libraries/libmtime"
    git = "https://gitlab.dkrz.de/icon-libraries/libmtime.git"
    maintainers = ["biddisco"]

    license("BSD-3-Clause")

    version("master", branch="libmtime-2.0.0-rc")
    #version("master", branch="master")

    variant("examples", default=False, description="Enable building examples")

    patch('skip-examples.patch')

    # depends_on("foo")

    def configure_args(self):
        return ["--enable-examples"] if self.spec.satisfies("+examples") else ["--enable-examples=no"]

    def install(self, spec, prefix):
        configure("--prefix=" + prefix)
        make()
        make("install")
