import click as cli
import requests

from .constants import DOCKET_LIST_FILTERS
from .utils import filters_to_url_params


def main():
    print(filters_to_url_params(DOCKET_LIST_FILTERS))


main()
