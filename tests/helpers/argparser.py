import os
from testflows.core import Secret

def argparser(parser):
    """Parse common arguments for the tests."""

    parser.add_argument(
        "--feature",
        metavar="name",
        type=str,
        help="Test Feature name",
        required=False,
    )

    pass