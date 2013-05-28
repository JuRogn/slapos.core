from psutil import *
from psutil._error import NoSuchProcess, AccessDenied

from time import time, sleep
import os
import ConfigParser

# Local import
from snapshot import Snapshot
from user import User

# ***************** Config *****************
GLOBAL_SLAPOS_CONFIGURATION = os.environ.get(
  'SLAPOS_CONFIGURATION',
  '/etc/opt/slapos/slapos.cfg'
)
# ******************************************

def build_user_list():
  """
  Builds a list of user based on slapos configuration file
  """
  config = ConfigParser.SafeConfigParser()
  config.read(GLOBAL_SLAPOS_CONFIGURATION)
  nb_user = int(config.get("slapformat", "partition_amount"))
  prefix  = config.get("slapformat", "user_base_name")
  return {name: User(name) for name in ["%s%s" % (prefix, nb) for nb in range(nb_user)] }


def gather(proc):
  """
  Gathers information on a single processus (psutil.Process)
  """
  assert type(proc) is Process
  try:
    return Snapshot(
        proc.username,
        cpu    = proc.get_cpu_percent(None),                            # CPU percentage, we will have to get actual absolute value
        cpu_io = proc.get_num_threads(),                                # Thread number, might not be really relevant
        ram    = proc.get_memory_info()[0],                             # Resident Set Size, virtual memory size is not accounted for
        ram_io = 0,                                                     # I cant figure out a way to measure this
        hd     = proc.get_io_counters()[2] + proc.get_io_counters()[3], # Byte count, Read and write. OSX NOT SUPPORTED
        hd_io  = proc.get_io_counters()[0] + proc.get_io_counters()[1], # Read + write IO cycles
        net    = 0,                                                     # COMING SOON!
        net_io = 0                                                      # COMING SOON!
    )
  except NoSuchProcess:
    return None

def snapshots():
  """
  Iterator used to apply gather() on every single relevant process.
  A process is considered relevant if its user matches our user list, i.e. its user
  is a slapos user
  """
  users = build_user_list()
  pList = [p for p in process_iter() if p.username in users]
  length = len(pList) / 5
  for i, process in enumerate(pList):
    if i % length == 0:
      sleep(.5)
    yield gather(process)

def main():
  """
  Main function
  The idea here is to poll system every so many seconds
  For each poll, we get a list of Snapshots, holding informations about processes
  We iterate over that list to store datas on a per user basis:
    Each user object is a dict, indexed on timestamp. We add every snapshot matching the user
    so that we get informations for each users
  """
  # Dict holding all slapos users (both active or inactive)
  # The User class is merely a Dict with a method to easily dump informations
  users = build_user_list()
  try:
    while True:
      tick = "%s" % time() # The key we use to store snapshots
      try:
        for snapshot in snapshots(): # iteration over snapshots that are being gathered by snapshots()
          if snapshot:
            user = users[snapshot.username]
            if tick in user:
              user[tick] += snapshot
            else:
              user[tick] = snapshot
      except (KeyboardInterrupt, SystemExit):
        break
      # Each iteration, we dump informations about users
      # Dumping is very generic : we can easily change the behavior
      # by changing the dumpSummary method from User class
      for user in users.values():
        user.dumpSummary()
  except AccessDenied: # We need some informations that require root permission
    print "You MUST execute this script with root permission."

if __name__  == '__main__':
  main()
