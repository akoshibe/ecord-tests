E-CORD pod emulation script.

`cord16.py` is the script that starts a Mininet topology, and statically
configures the cross-connects.

To invoke:

    sudo cord16.py [IPset]

or 

    sudo cord16.py [CO1 IPset1] [CO2 IPset2] [CO3 IPset3] [Metro IPset4]

IPset is a comma-separated list of IPs in a controller cluster. Supplying one
set associates all sites to that one set; supplying four associates each site to
a different set.

----

Cord16 config flags

cord16.py has a crude debug mode for the static parts of the network, which
connects them between VLAN-aware endpoints. To enable, set 

DEBUG_XCS = True

in the file. The VLANs used by each site are configured by the VLANS_SITE[A-C]
variables in the same file.

VLAN* flags switch on/off VLAN-aware traffic sources/sinks for the Ethernet 
edge, or configure them in some way.

To connect the statically-configured fabrics to actual controllers, set

CPLANE_ENABLE = True

which will associate each CO to an IPset. This also prevents the fabrics from
being statically configured. The OVSes will remain statically configured in this
case.

All flags are defined in cord16.py, along with more comments.

----

Static configurations are in `static.sh`. static.sh also contains a crude 
convenience function for interrogating nodes, 'ask'. It assumes that anything
named 'xc*' is a cpdq, otherwise ovs.

To use 'ask', import static.sh to a root shell.

- To dump a list of xc1's ports: `ask xc1 ports`
- To dump flows: `ask xc1 flows`

Other files:
- `vlansrc.py` : a VLAN-aware host
- `domains.py` : network subset associated with a particular set of controllers
- `netcfgs.sh` : cord16-specific network configurations
