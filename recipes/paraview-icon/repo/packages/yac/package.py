# Copyright 2013-2023 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack.package import *


class Yac(AutotoolsPackage):
    """FIXME: Put a proper description of your package here."""

    homepage = "https://dkrz-sw.gitlab-pages.dkrz.de/yac"
    url = "https://gitlab.dkrz.de/dkrz-sw/YAC.git"
    git = "https://gitlab.dkrz.de/dkrz-sw/YAC.git"
    maintainers = ["biddisco"]

    license("BSD-3-Clause")

    version("release-2.6.1_p3", branch="release-2.6.1_p3")

    variant("shared", default=True, description="Enable shared libraries")
    variant("fortran", default=True, description="Enable Fortran interface")

    depends_on("mpi")
    depends_on("mpi +fortran", when="+fortran")
    depends_on("yaxt@0.9.3.1")
    depends_on("yaxt@0.9.3.1 +fortran", when="+fortran")
    depends_on("libxml2")

    def configure_args(self):
        print('self.spec["mpi"].mpifc is', self.spec["mpi"].mpifc)
        args = [
            "--enable-static",
            "CC={0}".format(self.spec["mpi"].mpicc),
#            "CXX={0}".format(self.spec["mpi"].mpicxx),
            "FC={0}".format(
                self.spec["mpi"].mpifc if "+fortran" in self.spec else "no"
            ),
            "--with-yaxt-root={0}".format(self.spec["yaxt"].prefix),
            "--with-xml2-root={0}".format(self.spec["libxml2"].prefix),
        ]

        args += self.enable_or_disable("shared")

        return args

    def install(self, spec, prefix):
        make()
        make("install")
