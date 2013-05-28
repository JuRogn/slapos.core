class Snapshot:
  def __init__(self, username, cpu = 0, cpu_io = 0, ram = 0, ram_io = 0, hd = 0, hd_io = 0, net = 0, net_io = 0):
    self.username = username
    self.cpu      = cpu
    self.cpu_io   = cpu_io
    self.ram      = ram
    self.ram_io   = ram_io
    self.hd       = hd
    self.hd_io    = hd_io
    self.net      = net
    self.net_io   = net_io

  def __repr__(self):
    return "%s :: (cpu : (%s, %s), ram : (%s, %s), hd : (%s, %s), net : (%s, %s))" % (
        self.username,
        self.cpu, self.cpu_io,
        self.ram, self.ram_io,
        self.hd, self.hd_io,
        self.net, self.net_io
    )

  def __add__(self, other):
    assert self.username == other.username
    return Snapshot(
        self.username,
        self.cpu + other.cpu,
        self.cpu_io + other.cpu_io,
        self.ram + other.ram,
        self.ram_io + other.ram_io,
        self.hd + other.hd,
        self.hd_io + other.hd_io,
        self.net + other.net,
        self.net_io + other.net_io
    )

  def matters(self):
    return self.cpu != 0 or self.cpu_io != 0 or self.ram != 0 or self.ram_io != 0 or \
        self.hd != 0 or self.hd_io != 0 or self.net != 0 or self.net_io != 0


