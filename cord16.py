#!/usr/bin/env python
"""
ONS 2016 demo ECORD POD topology.

This emulation models what the Metro controller should see - the transport
switch(es), and the Ethernet Edges at each site, and the indirect paths between
them, if any.

The fabrics are statically configured with cross-connect functionality, and the
OVSes (representing the services), likewise to rewrite VLANs.

Each site is a separate control domain. The statically configured nodes are
collectively in another domain with no controller - this is so that the nodes
can be statically configured using dpctl or similar (e.g. as OpenFlow nodes
pointing to nothing so we can point a dpctl at them).
"""
from subprocess import Popen

from mininet.net import Mininet
from mininet.node import UserSwitch, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info

from domains import Domain

# VLAN Configurations
#
# If true, use VLAN-aware Ethernet edge traffic sources/sinks (hosts). The hostsi
# will use VLAN/IP pairs as specified by VLANS_SITE* variables below.
VLAN_ENABLE = False
# VLANS_SITE[A-C] - VLANs handled at the Ethernet edge for each site, with
# associated endpoint IP address
VLANS_SITEA = { 100 : '10.0.0.1' , 200 : '10.0.0.2' }
VLANS_SITEB = { 100 : '10.0.0.3' }
VLANS_SITEC = { 200 : '10.0.0.4' }

# Debug options
#
# If True, replace Ethernet Edges/transport with VLAN-aware hosts that expect
# the same VLANS as the edges and transports.
DEBUG_XCS = False 

if VLAN_ENABLE or DEBUG_XCS:
    from vlansrc import VLANHost

class StaticNodes( Domain ):
    """
    The set of statically configured nodes (fabrics/cross-connects and
    vlan-rewriting OVS nodes). These nodes do not connect to any controllers.
    """
    def build( self ):
        # site A - A CpQD acting as cross-connect *and* VLAN stitching.
        xc1 = self.addSwitch( 'xc1', dpid='0000ffffff01', cls=UserSwitch )
        ovs1 = self.addSwitch( 'ovs1', dpid='0000000000000001' ) 
        # site B/C - CpQD + OVS, latter doing VLAN stitching
        xc2 = self.addSwitch( 'xc2', dpid='0000ffffff02', cls=UserSwitch ) 
        xc3 = self.addSwitch( 'xc3', dpid='0000ffffff03', cls=UserSwitch ) 
        ovs2 = self.addSwitch( 'ovs2', dpid='0000000000000002' )
        ovs3 = self.addSwitch( 'ovs3', dpid='0000000000000003' )

        self.addLink( xc1, ovs1, port1=3, port2=1 )
        self.addLink( xc2, ovs2, port1=1, port2=2 )
        self.addLink( xc3, ovs3, port1=1, port2=2 )

        # if debug-mode, sandwich Site A and B xc's/ovses with VLANHosts
        if DEBUG_XCS:
            ee1 = self.addHost( 'vh1', cls=VLANHost, vmap={ 100 : '10.0.0.100' , 200 : '10.0.0.101' } )
            txp1 = self.addHost( 'vh2', cls=VLANHost, vmap={ 101 : '10.0.0.102' , 201 : '10.0.0.103' } )
            txp2 = self.addHost( 'vh3', cls=VLANHost, vmap={ 101 : '10.0.0.104' } )
            ee2 = self.addHost( 'vh4', cls=VLANHost, vmap={ 100 : '10.0.0.105' } )
            self.addLink( ee1, xc1, port2=1 )
            self.addLink( xc1, txp1, port1=2 )
            self.addLink( txp2, xc2, port2=2 )
            self.addLink( ovs2, ee2, port1=1 )

class MetroCore( Domain ):
    """
    The transport (metro core) nodes. Although it's just one node at this time,
    we make an explicit domain for clarity and flexibility.
    """
    def __init__( self, did ):
        Domain.__init__(self, did)

    def build( self ):
        txp1 = self.addSwitch( 'txp1', dpid='00000c072ee1', cls=UserSwitch )

class EtherEdge( Domain ):
    """
    The Ethernet Edge node and VLAN traffic source.
    The EE is also controlled by the metro-level controller.
    """
    def __init__( self, did, vmap ):
        Domain.__init__(self, did)
        self.vmap = vmap

    def build( self ):
        id = self.getId()
        # nodes will be named after the domain ID.
        ee = self.addSwitch( 'ee%s' % id,
                              dpid='000000000ee%s' % id,
                              cls=UserSwitch )
        if VLAN_ENABLE:
            vh = self.addHost( 'vh%s0' % id, cls=VLANHost, vmap=self.vmap )
        else:
            vh = self.addHost( 'h%s0' % id, ip='10.0.0.%s' % id )
        self.addLink( ee, vh, port1=1 )

def assignCtls( dm, cts ):
    """
    Allocate controller sets to each domain. Assumes cts[0]->dm[0]... if there
    are enough sets of controller IPs. Else, assign the first set to all of the
    domains that need controllers. 
    """
    # 0: static(ally configured) domain
    dm[ 0 ].addController( 'c00', controller=RemoteController, ip='127.0.0.1', port=6666 )
    # give the rest controllers
    i = 0
    for d in dm[ 1: ]:
        ctls = cts[ i ].split( ',' )
        for c in range( len( ctls ) ):
            d.addController( 'c%s%s' % ( d.getId(), c ),
                             controller=RemoteController,
                             ip=ctls[ c ] )
        if len( cts ) == len( dm ) - 1:
            i += 1

def wireTopo( dm, net ):
    """
    build out the multidomain topology as follows:

             +----stat(xc1)---ee1          [site A]
             |
    core(txp1)----stat(xc2-ovs2)---ee2     [site B]
             |
             +----stat(xc3-ovs3)---ee3     [site C]
    """
    # Only wire together things if not in debug mode
    if DEBUG_XCS:
        return
 
    c = dm[ 4 ]
    s = dm[ 0 ]
    net.addLink( c.getSwitches( 'txp1' ), s.getSwitches( 'xc1' ), port1=1, port2=2 )
    net.addLink( c.getSwitches( 'txp1' ), s.getSwitches( 'xc2' ), port1=2, port2=2 )
    net.addLink( c.getSwitches( 'txp1' ), s.getSwitches( 'xc3' ), port1=3, port2=2 )
    net.addLink( s.getSwitches( 'xc1' ), dm[ 1 ].getSwitches( 'ee1' ), port1=1, port2=2 )
    net.addLink( s.getSwitches( 'ovs2' ), dm[ 2 ].getSwitches( 'ee2' ), port1=1, port2=2 )
    net.addLink( s.getSwitches( 'ovs3' ), dm[ 3 ].getSwitches( 'ee3' ), port1=1, port2=2 )

def cfgStatic( metro ):
    """
    statically configure the static domain. See static.sh for details.
    - xc1 both acts as a crossconnect and stitches VLANs
    - xc2/3 are plain cross-connects
    - ovs2/3 stitches VLANs
    """
    import time

    # UserSwitch.dpctl() seems buggy, so invoking a sh script here.
    info( 'Configuring static nodes...' )
    time.sleep( 2 )
    ctl = metro.getControllers( 'c40' ).IP() if metro != None else ''
    Popen( [ 'sh', './static.sh' ] )
    Popen( [ 'sh', './netcfgs.sh', ctl ] )

def setup( argv ):
    ctlsets = argv[ 1: ]
    
    # create sites
    domains = []
    metro = None
    domains.insert( 0, StaticNodes() )
    if not DEBUG_XCS:
        domains.insert( 1, EtherEdge(1, vmap=VLANS_SITEA ) )
        domains.insert( 2, EtherEdge(2, vmap=VLANS_SITEB ) )
        domains.insert( 3, EtherEdge(3, vmap=VLANS_SITEC ) )
        domains.insert( 4, MetroCore(4) )
        metro = domains[ 4 ]
    assignCtls( domains, ctlsets )

    # build network out - domains are still unconnected at this point
    map( lambda d : d.build(), domains )
    net = Mininet()
    map( lambda d : d.injectInto( net ), domains )
    net.build()

    # wire domains together
    wireTopo( domains, net )

    map( lambda d : d.start(), domains )
    cfgStatic( metro )
    CLI( net )
    net.stop()

if __name__ == '__main__':
    import sys
    print len( sys.argv ) != 2
    if len( sys.argv ) != 2 and len( sys.argv ) != 5:
        print("Requires one or four sets of comma-separated controller IPs" )
    else:
        setLogLevel('info')
        setup( sys.argv )
