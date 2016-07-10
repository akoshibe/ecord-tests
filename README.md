E-CORD pod emulation script.

`cord16.py` is the script that starts a Mininet topology, and statically
configures the cross-connects.

To invoke:

   sudo cord16.py [IPset] #or
   sudo cord16.py [IPset1] [IPset2] [IPset3] [IPset4]

IPset is a comma-separated list of IPs in a controller cluster. Supplying one
set associates all sites to that one set; supplying four associates each site to
a different set.

----

cord16.py has a crude debug mode for the static parts of the network, which
connects them between VLAN-aware endpoints. To enable, set 

DEBUG_XCS = True

in the file. The VLANs used by each site are configured by the VLANS_SITE[A-C]
variables in the same file.

----

Static configurations are in `static.sh`. static.sh also contains a crude 
convenience function for interrogating nodes, 'ask'. It assumes that anything
named 'xc*' is a cpdq, otherwise ovs.

To use 'ask', import static.sh to a root shell.

To dump a list of xc1's ports: ask xc1 ports
To dump flows: ask xc1 flows

Other files:
- `vlansrc.py` : a VLAN-aware host
- `domains.py` : network subset associated with a particular set of controllers
- `netcfgs.sh` : cord16-specific network configurations
