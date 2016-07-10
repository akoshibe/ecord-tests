# ONOS configurations. This is highly specific to the cord16 topology. 

LINKS='
{
    "links": {
        "of:000000000c072ee1/3-of:0000000000000ee3/2": {
            "basic": {
                "durable": "true",
                "type": "INDIRECT"
            }
        },
        "of:0000000000000ee3/2-of:000000000c072ee1/3": {
            "basic": {
                "durable": "true",
                "type": "INDIRECT"
            }
        },
        "of:000000000c072ee1/2-of:0000000000000ee2/2": {
            "basic": {
                "durable": "true",
                "type": "INDIRECT"
            }
        },
        "of:000000000c072ee1/1-of:0000000000000ee1/2": {
            "basic": {
                "durable": "true",
                "type": "INDIRECT"
            }
        },
        "of:0000000000000ee1/2-of:000000000c072ee1/1": {
            "basic": {
                "durable": "true",
                "type": "INDIRECT"
            }
        },
        "of:0000000000000ee2/2-of:000000000c072ee1/2": {
            "basic": {
                "durable": "true",
                "type": "INDIRECT"
            }
        }
    }
}
'

[ "${1}" ] && curl --user onos:rocks -X POST -H "Content-Type: application/json"                \
              http://${1}:8181/onos/v1/network/configuration/ \
              -d "${LINKS}"
