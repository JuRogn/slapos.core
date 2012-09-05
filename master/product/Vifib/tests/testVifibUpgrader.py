# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Nexedi SA and Contributors. All Rights Reserved.
#                    Łukasz Nowak <luke@nexedi.com>
#                    Romain Courteaud <romain@nexedi.com>
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
# as published by the Free Software Foundation; either version 2
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
from VifibMixin import testVifibMixin
import transaction
import unittest
from Products.ERP5Type.tests.backportUnittest import expectedFailure

class TestVifibUpgrader(testVifibMixin):
  """ Checks that Vifib Upgrader is callable. """
  @expectedFailure
  def test_simple_call(self):
    self.login()
    portal = self.getPortalObject()
    portal.portal_alarms.upgrader_controller.activeSense()
    transaction.commit()
    self.tic()
    self.assertEqual(1,
        self.portal.portal_alarms.accept_submitted_credentials.isEnabled())
    self.assertEqual(1,
        self.portal.portal_alarms.confirm_ordered_sale_order.isEnabled())


def test_suite():
  suite = unittest.TestSuite()
  suite.addTest(unittest.makeSuite(TestVifibUpgrader))
  return suite
