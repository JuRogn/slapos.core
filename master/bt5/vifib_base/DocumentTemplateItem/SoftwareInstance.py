# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Nexedi SARL and Contributors. All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
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
from AccessControl import ClassSecurityInfo
from Products.ERP5Type import Permissions
from Products.ERP5.Document.Item import Item
from lxml import etree
import collections

class DisconnectedSoftwareTree(Exception):
  pass

class SoftwareInstance(Item):
  """
  """

  meta_type = 'ERP5 Software Instance'
  portal_type = 'Software Instance'
  add_permission = Permissions.AddPortalContent

  # Declarative security
  security = ClassSecurityInfo()
  security.declareObjectProtected(Permissions.AccessContentsInformation)


  security.declareProtected(Permissions.AccessContentsInformation,
    'getSlaXmlAsDict')
  def getSlaXmlAsDict(self):
    """Returns SLA XML as python dictionary"""
    result_dict = {}
    xml = self.getSlaXml()
    if xml is not None and xml != '':
      tree = etree.fromstring(xml.encode('utf-8'))
      for element in tree.findall('parameter'):
        key = element.get('id')
        value = result_dict.get(key, None)
        if value is not None:
          value = value + ' ' + element.text
        else:
          value = element.text
        result_dict[key] = value
    return result_dict

  security.declareProtected(Permissions.AccessContentsInformation,
    'checkConnected')
  def checkDisconnected(self, graph, root):
    size = len(graph)
    visited = set()
    to_crawl = collections.deque(graph[root])
    while to_crawl:
      current = to_crawl.popleft()
      if current in visited:
        continue
      visited.add(current)
      node_children = set(graph[current])
      to_crawl.extend(node_children - visited)
    # add one to visited, as root won't be visited, only children
    # this is false positive in case of cyclic graphs, but they are
    # anyway wrong in Software Instance trees
    if size != len(visited) + 1:
      raise DisconnectedSoftwareTree
    return True
