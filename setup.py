#!/usr/bin/env python

import setuptools
setuptools.setup(
    setup_requires=["nose", "setuptools>=30.3",],    # workaround until setup.cfg
)                                                    # uses setup_requires for real
