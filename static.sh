# Static configs for emulated cross-connects and VLAN stitching. These nodes
# *don't* associate with any controllers. To make them do so, refer to
# cord16.py.
#
#   - xc1 stitches VLANs
#   - xc2/3 are plain cross-connects (pass-throughs here)
#   - ovs2/3 stitches VLANs
#
# dpctl(8) is highly innacurate, so we use this as CpQD dpctl reference: 
#
#    https://github.com/CPqD/ofsoftswitch13/wiki/Dpctl-Flow-Mod-Cases
#

CPQD="dpctl unix:/tmp/"
OVS="ovs-ofctl" 
OVSP="/var/run/openvswitch/"

# ask (switch, info): get flow or port info. Uses demo's switch-specific names
# to determine which syntax to use (xc* = cpqd, else, ovs). 
ask () {
    # see what switch is usw=userspace switch (cpqd)
    local usw='xc[0-9]\{1,\}'
    local ovs=$(printf "$1" | sed 's:'"$usw"'::')
    case $2 in
        ports)
            if [ "$ovs" ]; then
                ${OVS} dump-ports-desc ${OVSP}${1}.mgmt \
                    | sed -ne 's:\(.*'"${1}"'.*\):\1: p'
            else
                ${CPQD}${1} port-desc \
                    | sed -ne 's:.*no="\([0-9]*\).*name="\(.*eth[0-9]\).*:\2 \1: p'
            fi
            ;;
        flows)
            if [ "$ovs" ]; then
                ${OVS} dump-flows ${OVSP}${1}.mgmt
            else
                ${CPQD}${1} stats-flow | sed 's:stat_repl.*stats=\[::g'
            fi
            ;;
        *)
            printf '%s\n' "ask [switch] [ports|flows]"
            ;;
    esac
}

# --- Static flow configurations ---
#
# pass_*(switch, in, out): in one port, out the other untouched. Low-priority
# to not match tagged traffic.
pass_cpqd () {
    ${CPQD}${1} flow-mod table=0,cmd=add,prio=1000 in_port=${2} apply:output=${3}
}

pass_ovs () {
    ${OVS} add-flow ${OVSP}${1}.mgmt priority=1000,in_port=${2},actions=output:${3}
}

# stitch_*(switch, in, old, out, new): replace old vlan from port 'in' with new
# vlan on port 'out'
stitch_cpqd () {
    ${CPQD}${1} flow-mod table=0,cmd=add in_port=${2},vlan_vid=${3} \
        apply:set_field=vlan_vid:${5},output=${4}
}

stitch_ovs () {
    ${OVS} add-flow ${OVSP}${1}.mgmt \
        in_port=${2},dl_vlan=${3},actions=mod_vlan_vid:${5},output:${4}
}

# --- Fabric configurations at sites ---
#
# site A fabric. emulate the vlan rewriting that happens at the OVS attached to it,
# but pass non-tagged traffic as-is.
fabric1 () {
    stitch_cpqd xc1 1 100 2 101
    stitch_cpqd xc1 1 200 2 201
    stitch_cpqd xc1 2 101 1 100
    stitch_cpqd xc1 2 201 1 200
    pass_cpqd xc1 1 2
    pass_cpqd xc1 2 1
}

# sites B and C fabrics are regular pass-through, and ovs stitches the VLANs (while
# passing tagged traffic normally).
fabric2 () {
    pass_cpqd xc2 1 2
    pass_cpqd xc2 2 1
    stitch_ovs ovs2 1 100 2 101 
    stitch_ovs ovs2 2 101 1 100
    pass_ovs ovs2 1 2
    pass_ovs ovs2 2 1
}

fabric3 () {
    pass_cpqd xc3 1 2
    pass_cpqd xc3 2 1
    stitch_ovs ovs3 1 200 2 201
    stitch_ovs ovs3 2 201 1 200
    pass_ovs ovs3 1 2
    pass_ovs ovs3 2 1
}

# "main()" - pushes static configs anf network config to controller.
fabric1 1>/dev/null 2>&1
fabric2 1>/dev/null 2>&1
fabric3 1>/dev/null 2>&1
