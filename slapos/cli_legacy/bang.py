# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2011, 2012 Vifib SARL and Contributors.
# All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly advised to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import argparse
import ConfigParser

from slapos.bang import do_bang


def main(*args):
    ap = argparse.ArgumentParser()
    ap.add_argument('-m', '--message', default='', help='Message for bang.')
    ap.add_argument('configuration_file', type=argparse.FileType(),
                    help='SlapOS configuration file.')
    if args:
        args = ap.parse_args(list(args))
    else:
        args = ap.parse_args()
    configp = ConfigParser.SafeConfigParser()
    configp.readfp(args.configuration_file)
    do_bang(configp, args.message)
