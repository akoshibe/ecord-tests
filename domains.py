from mininet.net import Mininet

class Domain(object):
    """
    A network subgraph associated with a certain (set of) controller(s).

    At the core, a Domain is a container for switch, host, link, and controller
    information to be dumped into the Mininet mid-level API.
    """

    def __init__ (self, did=0):
        # each Domain has a numeric ID for sanity/convenience
        self.__dId = did

        # information about network elements - for calling the "mid-level" APIs
        self.__ctrls = {}
        self.__switches = {}
        self.__hosts = {}
        self.__links = {}
        # maps of devices, hosts, and controller names to actual objects
        self.__switchmap = {}
        self.__hostmap = {}
        self.__ctrlmap = {}

    def addController(self, name, **kwargs):
        self.__ctrls[name] = kwargs if kwargs else {}
        return name

    def addSwitch(self, name, **kwargs):
        self.__switches[name] = kwargs if kwargs else {}
        return name
    
    def addHost(self, name, **kwargs):
        self.__hosts[name] = kwargs if kwargs else {}
        return name

    def addLink(self, src, dst, **kwargs):
        self.__links[(src, dst)] = kwargs if kwargs else {}
        return (src, dst)

    def getId( self):
        return self.__dId

    def getControllers(self, name=None):
        return self.__ctrlmap.values() if not name else self.__ctrlmap.get(name)

    def getSwitches(self, name=None):
        return self.__switchmap.values() if not name else self.__switchmap.get(name)

    def getHosts(self, name=None):
        return self.__hostmap.values() if not name else self.__hostmap.get(name)

    def injectInto(self, net):        
        """
        Adds available topology info to a supplied Mininet object.
        """
        # add switches, hosts, then links to mininet object
        for sw, args in self.__switches.iteritems():
            self.__switchmap[sw] = net.addSwitch(sw, **args)
        for h, args in self.__hosts.iteritems():
            self.__hostmap[h] = net.addHost(h, **args)
        for l, args in self.__links.iteritems():
            src = self.__switchmap.get(l[0])
            dst = self.__switchmap.get(l[1])
            net.addLink(src if src else self.__hostmap.get(l[0]),
                         dst if dst else self.__hostmap.get(l[1]), **args)
        # then controllers
        for c, args in self.__ctrls.iteritems():
            self.__ctrlmap[c] = net.addController(c, **args)

    def _startCtl(self, ctl):
        if ctl:
            ctl.start()

    def start(self):
        """
        Starts the switches with the correct controller.
        """
        map(lambda c: self._startCtl(c), self.__ctrlmap.values())
        map(lambda s: s.start(self.__ctrlmap.values()), self.__switchmap.values())

    def build(self, *args):
        """ 
        Override for custom topology, similar to Mininet.Topo
        """
        pass

    @staticmethod
    def interConnect(endp1, endp2, net, **kwargs):
        """
        Connects two nodes in together with a link. Intended for interconnecting
        two domains within the same Mininet object.
        """
        net.addLink(endp1, endp2, **kwargs)

