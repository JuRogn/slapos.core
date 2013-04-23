# -*- coding: utf-8 -*-

import logging

from slapos.cli.config import ClientConfigCommand
from slapos.client import init, do_supply, ClientConfig


class SupplyCommand(ClientConfigCommand):

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        ap = super(SupplyCommand, self).get_parser(prog_name)

        ap.add_argument('software_url',
                        help='Your software url')

        ap.add_argument('node',
                        help="Target node")

        return ap

    def take_action(self, args):
        configuration_parser = self.fetch_config(args)
        config = ClientConfig(args, configuration_parser)
        local = init(config)
        do_supply(args.software_url, args.node, local)
