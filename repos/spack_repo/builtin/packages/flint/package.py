# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import os

from spack_repo.builtin.build_systems.autotools import AutotoolsPackage

from spack.package import *


class Flint(AutotoolsPackage):
    """FLINT (Fast Library for Number Theory)."""

    homepage = "https://flintlib.org"
    url = "https://flintlib.org/download/flint-3.1.2.tar.gz"
    git = "https://github.com/flintlib/flint.git"
    list_url = "https://flintlib.org/downloads.html"
    list_depth = 0

    license("LGPL-2.1-or-later")

    version("main", branch="main")
    version("3.6.0", sha256="b95e2c7792f5eea4a1c8d2d42c4098434756832e57a094b295eb5dfdc9b4c36b")
    version("3.5.0", sha256="3982f385f00610a944e0152eb0a29893b2366fa640e8f5f3076c47564cf7e2a6")
    version("3.4.0", sha256="9497679804dead926e3affeb8d4c58739d1c7684d60c2c12827550d28e454a33")
    version("3.1.2", sha256="fdb3a431a37464834acff3bdc145f4fe8d0f951dd5327c4c6f93f4cbac5c2700")
    version("3.0.1", sha256="7b311a00503a863881eb8177dbeb84322f29399f3d7d72f3b1a4c9ba1d5794b4")
    version("2.5.2", sha256="cbf1fe0034533c53c5c41761017065f85207a1b770483e98b2392315f6575e87")
    version("2.4.5", sha256="e489354df00f0d84976ccdd0477028693977c87ccd14f3924a89f848bb0e01e3")

    # Overlap in functionality between gmp and mpir
    # All other dependencies must also be built with
    # one or the other
    # variant('mpir', default=False,
    #         description='Compile with the MPIR library')

    depends_on("c", type="build")  # generated
    depends_on("cxx", type="build")  # generated

    depends_on("gmp")  # mpir is a drop-in replacement for this
    depends_on("mpfr")  # Could also be built against mpir

    depends_on("m4", type="build")

    # A git checkout ships no configure, so one has to be generated.
    with when("@main"):
        depends_on("autoconf", type="build")
        depends_on("automake", type="build")
        depends_on("libtool", type="build")

    @when("@3.4.0:")
    def patch(self):
        # configure tells in-tree from out-of-tree builds by comparing two
        # spellings of one path textually, so a symlinked build path makes an
        # in-tree build look out-of-tree -- as on macOS, where the stage sits
        # under /var, a symlink to /private/var.  src/fmpz/fmpz.c then lands in
        # the source list twice, once from the wildcard and once from the
        # out-of-tree special case, and "ld -r" is handed the same object twice:
        # 12 duplicate symbols in build/fmpz_merged.lo.  Compare the two paths
        # with both sides resolved instead.
        #
        # The line is identical in every release that has it, so match on it
        # alone rather than carrying a patch per version.
        #
        # Edit exactly one file.  Releases ship a generated configure and are
        # built without autoreconf; editing configure.ac as well would leave it
        # newer, and flint's maintainer mode rule re-runs bootstrap.sh whenever
        # that happens, part way through the build.  A git checkout has only
        # configure.ac, and spack generates configure from it afterwards.
        target = "configure" if os.path.exists("configure") else "configure.ac"
        filter_file(
            'if test "$ac_abs_confdir" = "`pwd`";',
            'if test "`cd "$ac_abs_confdir" && pwd -P`" = "`pwd -P`";',
            target,
            string=True,
        )

    def configure_args(self):
        spec = self.spec
        return [f"--with-gmp={spec['gmp'].prefix}", f"--with-mpfr={spec['mpfr'].prefix}"]
