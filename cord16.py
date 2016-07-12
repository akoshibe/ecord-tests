#!/usr/bin/env python
"""
ONS 2016 demo ECORD POD topology.

This emulation models a claw topology of three sites connected together by a
packet transport network.
"""
from subprocess import Popen

from mininet.net import Mininet
from mininet.node import UserSwitch, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info

from domains import Domain
from vlansrc import VLANHost

# If true, use VLAN-aware Ethernet edge traffic sources/sinks (hosts). The hosts
# will use VLAN/IP pairs as specified by VLANS_SITE* variables below.
VLAN_ENABLE = False
# VLANS_SITE[A-C] - VLANs handled at the Ethernet edge for each site, with
# associated endpoint IP address
VLANS_SITEA = { 100 : '10.0.0.1' , 200 : '10.0.0.2' }
VLANS_SITEB = { 100 : '10.0.0.3' }
VLANS_SITEC = { 200 : '10.0.0.4' }

# If true, site fabrics will be connected to a local control plane. Otherwise,
# they are statically configured by static.sh.
CPLANE_ENABLE = True

# If True, replace Ethernet Edges/transport with VLAN-aware hosts that expect
# the same VLANS as the edges and transports.
DEBUG_XCS = False 
# VLANs/IPs used for debug-mode VLAN hosts: vh1,2,3, and 4.
DEBUG_VH1 = { 100 : '10.0.0.100' , 200 : '10.0.0.101' }
DEBUG_VH2 = { 101 : '10.0.0.102' , 201 : '10.0.0.103' }
DEBUG_VH3 = { 101 : '10.0.0.104' }
DEBUG_VH4 = { 100 : '10.0.0.105' }

class CO( Domain ):
    """
    A single central office fabric. May or may not be statically configured
    based on value of CPLANE_ENABLE.
    """
    def __init__( self, did ):
        Domain.__init__(self, did)

    def build( self ):
        id = self.getId()
        self.addSwitch( 'xc%s' % id, dpid='0000ffffff0%s' % id, cls=UserSwitch )

class StaticNodes( Domain ):
    """
    The set of statically configured nodes. These are the OVSes that emulate the
    vSG/rewrites VLANs. These nodes do not connect to any controllers.
    """
    def build( self ):
        # site A - OVS is a vSG (currently unconfigured, even statically).
        # site B/C - OVS doing VLAN stitching
        self.addSwitch( 'ovs1', dpid='0000000000000001' ) 
        self.addSwitch( 'ovs2', dpid='0000000000000002' )
        self.addSwitch( 'ovs3', dpid='0000000000000003' )

        # if debug-mode, make some EE-replacing VLAN Hosts and set aside.
        if DEBUG_XCS:
            self.addHost( 'vh1', cls=VLANHost, vmap=DEBUG_VH1 )
            self.addHost( 'vh2', cls=VLANHost, vmap=DEBUG_VH2 )
            self.addHost( 'vh3', cls=VLANHost, vmap=DEBUG_VH3 )
            self.addHost( 'vh4', cls=VLANHost, vmap=DEBUG_VH4 )

class MetroCore( Domain ):
    """
    The transport (metro core) nodes. Although it's just one node at this time,
    we make an explicit domain for clarity and flexibility.
    """
    def __init__( self, did ):
        Domain.__init__(self, did)

    def build( self ):
        self.addSwitch( 'txp1', dpid='00000c072ee1', cls=UserSwitch )

class EtherEdge( Domain ):
    """
    The Ethernet Edge and traffic source, with former part fo teh Metro domain.
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
    Allocate controller sets to domains. 
    If CPLANE_ENABLE=True, each fabric is also connected to a controller (set).
    In general, if only one IP set is provided, everything is connected to that
    one IP set. If four IP sets or more are supplied, the fabrics and metro
    domains (the transport and EE nodes) are each given a IP set, given
    CPLAN_ENABLE is set. Otherwise, just the first IP set is connected with the
    metro domains.
    """
    ccls = RemoteController
    # all domains controlled by metro controller(s)
    metro = dm[ 4:8 ]
    i = 0
    if CPLANE_ENABLE:
        for d in dm[ 1:4 ]:
            ctls = cts[ i ].split( ',' )
            print ( ctls )
            for c in range( len( ctls ) ):
                d.addController( 'c%s0%s' % ( d.getId(), c ), controller=ccls, ip=ctls[ c ] )
            if len( cts ) >= 4:
                i += 1
    else:
        for d in dm[ 1:4 ]:
            d.addController( 'c00', controller=ccls, ip='127.0.0.1', port=6666 )

    # either the last IP set or first will be used here
    for m in metro:
        ctls = cts[ i ].split( ',' )
        for c in range( len( ctls ) ):
            m.addController( 'c%s%s' % ( m.getId(), c ), controller=ccls, ip=ctls[ c ] )

    # invariant static domain is 0th in domain list
    dm[ 0 ].addController( 'c00', controller=ccls, ip='127.0.0.1', port=6666 )

def wireTopo( dm, net ):
    """
    build out the multidomain topology as follows:

             +----CO(xc1)---ee1                 [site A]
             |       |
             |   stat(ovs1)
             |
    core(txp1)----CO(xc2)--stat(ovs2)---ee2     [site B]
             |
             +----CO(xc3)--stat(ovs3)---ee3     [site C]
    """
    s = dm[ 0 ]
    # Only wire together test nodes if in debug mode
    if DEBUG_XCS:
        net.addLink( s.getHosts( 'vh1' ), dm[ 1 ].getSwitches( 'xc1' ), port2=1 )
        net.addLink( dm[ 1 ].getSwitches( 'xc1' ), s.getHosts( 'vh2' ), port1=2 )
        net.addLink( s.getHosts( 'vh3' ), dm[ 2 ].getSwitches( 'xc2' ), port2=2 )
        net.addLink( s.getSwitches( 'ovs2' ), s.getHosts( 'vh4' ), port2=1 )
    else:
        txp = dm[ 7 ].getSwitches( 'txp1' )
        net.addLink( txp, dm[ 1 ].getSwitches( 'xc1' ), port1=1, port2=2 )
        net.addLink( txp, dm[ 2 ].getSwitches( 'xc2' ), port1=2, port2=2 )
        net.addLink( txp, dm[ 3 ].getSwitches( 'xc3' ), port1=3, port2=2 )
        net.addLink( dm[ 1 ].getSwitches( 'xc1' ), dm[ 4 ].getSwitches( 'ee1' ), port1=1, port2=2 )
        net.addLink( s.getSwitches( 'ovs2' ), dm[ 5 ].getSwitches( 'ee2' ), port1=1, port2=2 )
        net.addLink( s.getSwitches( 'ovs3' ), dm[ 6 ].getSwitches( 'ee3' ), port1=1, port2=2 )

    # Assemble COs - attach OVSes to CpQDs
    net.addLink( dm[ 1 ].getSwitches( 'xc1' ), s.getSwitches( 'ovs1' ), port1=3, port2=1 )
    net.addLink( dm[ 2 ].getSwitches( 'xc2' ), s.getSwitches( 'ovs2' ), port1=1, port2=2 )
    net.addLink( dm[ 3 ].getSwitches( 'xc3' ), s.getSwitches( 'ovs3' ), port1=1, port2=2 )

def cfgStatic( metro ):
    """
    statically configure the static domain. See static.sh for details.
    """
    import time

    # UserSwitch.dpctl() seems buggy, so invoking a sh script here.
    info( 'Configuring static nodes...' )
    time.sleep( 2 )
    ctl = metro.getControllers()[0].IP() if metro != None else ''
    Popen( [ 'sh', './static.sh', 'static' if not CPLANE_ENABLE else '' ] )
    Popen( [ 'sh', './netcfgs.sh', ctl ] )

def setup( argv ):
    ctlsets = argv[ 1: ]
    domains = []
    metro = None

    # things that can be statically config'd are grouped as domain 0
    # 1,2, and 3 are sites A, B, and C, respectively.
    domains.insert( 0, StaticNodes() )
    domains.insert( 1, CO( 1 ) )
    domains.insert( 2, CO( 2 ) )
    domains.insert( 3, CO( 3 ) )

    # create all domains, unless ading debug hosts
    domains.insert( 4, EtherEdge(1, vmap=VLANS_SITEA ) )
    domains.insert( 5, EtherEdge(2, vmap=VLANS_SITEB ) )
    domains.insert( 6, EtherEdge(3, vmap=VLANS_SITEC ) )
    domains.insert( 7, MetroCore(4) )
    metro = domains[ 7 ]

    # connect domains to controllers according to configuration
    assignCtls( domains, ctlsets )

    # build network out
    map( lambda d : d.build(), domains )
    net = Mininet()
    map( lambda d : d.injectInto( net ), domains )
    net.build()

    # wire domains together since domains are still unconnected at this point
    wireTopo( domains, net )
    # start network, do static configs, and launch CLI
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
