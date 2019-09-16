#+
# Distutils script to install mtpy. Invoke from the command line
# in this directory as follows:
#
#     python3 setup.py install
#
# Written by Lawrence D'Oliveiro <ldo@geek-central.gen.nz>.
#-

import distutils.core

distutils.core.setup \
  (
    name = "mtpy",
    version = "0.7",
    description = "language bindings for libmtp",
    author = "Lawrence D'Oliveiro",
    author_email = "ldo@geek-central.gen.nz",
    url = "https://github.com/ldo/mtpy",
    py_modules = ["mtpy"],
  )
