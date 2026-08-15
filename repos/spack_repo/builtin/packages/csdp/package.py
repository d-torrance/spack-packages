# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.makefile import MakefilePackage

from spack.package import *


class Csdp(MakefilePackage):
    """CSDP is a library of routines that implements a predictor corrector
    variant of the semidefinite programming algorithm of Helmberg, Rendl,
    Vanderbei, and Wolkowicz"""

    homepage = "https://projects.coin-or.org/Csdp"
    url = "https://www.coin-or.org/download/source/Csdp/Csdp-6.1.1.tgz"

    license("CPL-1.0", when="@:6.2.0", checked_by="d-torrance")
    # license has been updated in git for future releases to EPL-2.0

    version("6.2.0", sha256="7f202a15f33483ee205dcfbd0573fdbd74911604bb739a04f8baa35f8a055c5b")
    version("6.1.1", sha256="0558a46ac534e846bf866b76a9a44e8a854d84558efa50988ffc092f99a138b9")

    # 6.1.1 leaves the flags to the per-directory Makefiles; only 6.2.0 sets
    # them in the top level Makefile, where we override them below.
    variant("openmp", default=True, when="@6.2.0:", description="Build with OpenMP support")

    depends_on("c", type="build")

    depends_on("blas")
    depends_on("lapack")

    # apple-clang compiles OpenMP code given -Xpreprocessor -fopenmp, but Apple
    # ships no OpenMP runtime, so libomp has to come from somewhere.
    depends_on("llvm-openmp", when="+openmp %apple-clang")

    # user_exit.c calls printf without including stdio.h.  C89 allows that, so
    # the old standard set below is enough for gcc, but clang 16 and later
    # reject implicitly declaring a known library function whatever the
    # standard.  6.1.1's copy of the file does not call printf at all.
    patch("stdio.patch", when="@6.2.0:")

    def edit(self, spec, prefix):
        mkdirp(prefix.bin)
        makefile = FileFilter("Makefile")
        makefile.filter("/usr/local/bin", prefix.bin)
        makefile.filter(r"^export LIBS.*$", "")  # use flag_handler instead

        # csdp ships an INSTALL file and declares nothing phony, so where the
        # filesystem is case insensitive -- macOS -- make takes INSTALL as
        # satisfying the install target, reports it up to date, and silently
        # installs nothing at all.
        makefile.filter(r"^all:", ".PHONY: all unitTest install clean\nall:")

    @property
    def build_targets(self):
        # The CFLAGS 6.2.0 exports assume one toolchain on one machine.  -m64 is
        # not a valid option on aarch64, -march=native -mtune=native tune the
        # binaries for whichever machine happened to build them, -fopenmp is not
        # how apple-clang spells it, and -ansi is strict c89, where inline is
        # not a keyword and llvm-openmp's omp.h will not parse.  Being a plain
        # assignment it also clobbers anything passed in, so override it on the
        # command line, which takes precedence and reaches the sub-makes.
        #
        # Kept below is what the sources themselves test for.  An old standard
        # is among it: csdp defines its functions K&R style, which C23 drops, so
        # gcc 15 rejects the build without it.  The architecture flags are
        # deliberately not replaced -- that is the compiler wrapper's job, and
        # it knows the target that was actually asked for.
        if not self.spec.satisfies("@6.2.0:"):
            return []
        cflags = [
            "-O3",
            "-std=gnu89",
            "-DBIT64",
            "-DUSESIGTERM",
            "-DUSEGETTIME",
            "-I../include",
        ]
        if self.spec.satisfies("+openmp"):
            # omp.h is only included when USEOPENMP is defined, so the defines
            # and the compiler's OpenMP flag have to travel together
            cflags.extend([self.compiler.openmp_flag, "-DUSEOPENMP", "-DSETNUMTHREADS"])
        return [f"CFLAGS={' '.join(cflags)}"]

    def flag_handler(self, name: str, flags: List[str]):
        if name == "ldflags":
            flags.extend(
                [
                    f"-L{self.stage.source_path}/lib -lsdp",
                    self.spec["lapack"].libs.ld_flags,
                    self.spec["blas"].libs.ld_flags,
                    "-lm",
                ]
            )
            if self.spec.satisfies("+openmp %apple-clang"):
                # -Xpreprocessor -fopenmp only reaches the preprocessor, so it
                # does not pull in the OpenMP runtime the way -fopenmp would
                flags.append(self.spec["llvm-openmp"].libs.ld_flags)
        return (flags, None, None)
