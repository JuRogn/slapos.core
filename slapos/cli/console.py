# -*- coding: utf-8 -*-

import logging

from slapos.cli.config import ClientConfigCommand
from slapos.client import init, do_console, ClientConfig


class ConsoleCommand(ClientConfigCommand):
    """
    slapconsole allows you interact with slap API. You can play with the global
    "slap" object and with the global "request" method.

    examples :
    >>> # Request instance
    >>> request(kvm, "myuniquekvm")
    >>> # Request software installation on owned computer
    >>> supply(kvm, "mycomputer")
    >>> # Fetch instance informations on already launched instance
    >>> request(kvm, "myuniquekvm").getConnectionParameter("url")
    """
    # XXX TODO: docstring is printed without newlines

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        ap = super(ConsoleCommand, self).get_parser(prog_name)

        ap.add_argument('-u', '--master_url',
                        help='Url of SlapOS Master to use')

        ap.add_argument('-k', '--key_file',
                        help='SSL Authorisation key file')

        ap.add_argument('-c', '--cert_file',
                        help='SSL Authorisation certificate file')

        return ap

    def take_action(self, args):
        configuration_parser = self.fetch_config(args)
        config = ClientConfig(args, configuration_parser)
        local = init(config)
        do_console(local)
