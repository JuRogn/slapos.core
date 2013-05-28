from snapshot import Snapshot

class User(dict):
  def __init__(self, name):
    self.name = str(name)

  def dumpSummary(self):
    summary = reduce(lambda x, y: x+y, self.values(), Snapshot(self.name))
    if summary.matters():
      print summary

  def dump(self):
    print self
