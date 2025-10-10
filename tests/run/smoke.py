#!/usr/bin/env python3
import sys

from testflows.core import *

append_path(sys.path, "../..")

from tests.helpers.argparser import argparser


@TestModule
@Name("smoke")
@ArgumentParser(argparser)
def regression(self, feature):
    """Execute smoke tests."""

    self.context.altinity_repo = "https://altinity.github.io/helm-charts/"
    self.context.version  = "25.3.6.10034.altinitystable"

    Feature(run=load(f"tests.scenarios.smoke","feature"))


if main():
    regression()

