"""
A source of VLAN traffic. based on mininet/examples/vlanhost.py
"""

from mininet.node import Host
from mininet.util import quietRun
from mininet.log import error

class VLANHost( Host ):
    "Host connected to VLAN interface"

    def __init__( self, name, vmap={}, *args, **kwargs ):
        super(VLANHost, self).__init__(name, *args, **kwargs)
        self.vlanmap = vmap
        self.cfgd = False

    def addVLAN( self, vlan, ip ):
        self.vlanmap[ vlan ] = ip
        if self.cfgd:
            self.config()

    def config( self, **params ):
        """Configure VLANHost according to (optional) parameters:
           vlan: VLAN ID for default interface"""

        intf = self.defaultIntf()
        if not self.cfgd:
            r = super( VLANHost, self ).config( **params )
            self.cmd( 'ifconfig %s inet 0' % intf )
            self.cfgd = True

        # create VLAN interface(s)
        for vlan, ip in self.vlanmap.iteritems():
            self.cmd( 'vconfig add %s %d' % ( intf, vlan ) )
            # assign the host's IP to the VLAN interface
            self.cmd( 'ifconfig %s.%d inet %s' % ( intf, vlan, ip ) )

        # first time: remove IP from default, "physical" interface
        self.vlanmap.clear()
        return r
