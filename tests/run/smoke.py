#!/usr/bin/env python3
import sys
import os

from testflows.core import *

append_path(sys.path, "../..")

from tests.helpers.argparser import argparser


@TestModule
@Name("smoke")
@ArgumentParser(argparser)
def regression(self, feature):
    """Execute smoke tests."""

    self.context.altinity_repo = "https://helm.altinity.com"
    self.context.version = "25.3.6.10034.altinitystable"
    self.context.local_chart_path = os.path.join(os.getcwd(), "charts", "clickhouse")
    Feature(run=load(f"tests.scenarios.smoke", "feature"))


if main():
    regression()
