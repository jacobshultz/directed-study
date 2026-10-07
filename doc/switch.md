# Switch

This document details the configuration for the network switch.

Network configuration is made of two parts: *Within the nodes* and *outside the nodes*. This document discusses the *outside the nodes* part.

### Prerequisites:
- Control node is configured as defined in *cluster.md*.

## Power on
If powered off, simply plug the power cord into the switch. The fans will audibly start automatically, and the front status light will be orange.

Continue once the status light is green.

## Plug in ethernet
- Internet to physical port 23
- Control node to physical port 24
- Protected nodes starting at 1 and working up.

## Detection

Use [NMAP](https://nmap.org/) to perform a quickscan:

### 1. Detect your network IP address

Example:
```
$ ip addr
> ... inet 192.168.12.130/24 ...
```

In the above example our network address is 192.168.12.0.

### 2. Perform a quickscan with nmap and access in the browser
`nmap -sn 192.168.12.0/24`

Type the returned IP addressed into your browser one-by-one until the netgear web interface pops up. **Note:** your browser will likely try to upgrade the connection to https, so you will want to manually enter the url as `http://192.168.12.XXX/`

### 3. VLAN Config

Log into the web interface. Consult Dr. Ohl for the password.

The configuration we care about is found under **Switching -> VLAN**.

*Note: Be sure to select the **Apply** button to save all your configuration changes.*

**VLAN Configuration**

You should see 3 VLANS under the *basic VLAN Configuration*:
- 1: Default (default)
- 2: Protected
- 4089: Auto-Video (default)

The protected VLAN must have an ID of 2.

**VLAN Trunking Configuration**

| Interface | Switch Port Mode | Native VLAN Tagging | Access VLAN ID | Native VLAN ID | Note |
| --- | --- | --- | --- | --- | --- |
| g1-g22 | General | Disable | 2 | 2 | Protected Nodes |
| g23 | General | Disable | 1 | 1 | WAN connection |
| g24 | Trunk | Disable | 2 | 1 | Controller Node |


**VLAN Membership**

- U (Untagged): Port is native to this VLAN
- T (Tagged): Port is non-native to this VLAN
- (none): Port cannot access this vlan, not a member.

VLAN 1
| # | Value |
| --- | --- |
| 1 - 22 | (none) |
| 23 - 24 | U |

VLAN 2
| # | Value |
| --- | --- |
| 1 - 22 | U |
| 23 | (none) |
| 24 | T |

Don't mess with LAG.

**VLAN Status**

Useful for sanity checking your vlan config.

**Port PVID Configuration**

| # | PVID | VLAN Member |
| --- | --- | --- |
| g1-g22 | 2 | 2 |
| g23 | 1 | 1 |
| g24 | 1 | 1,2,4089 |

g24 will also have ingress filtering and current ingress filtering enabled. g24 has values specified under Tagged Vlans. These values should be set automatically from the Vlan Membership section.

## Sanity check

1. If you've plugged in the nodes before configuration you may need to remove them and re-insert.

1. Check `systemctl status dnsmasq` on the control node. Being disconnected from the network may cause the DHCP server to timeout. Restart if needed

1. Connect control node to port 24.

1. Verify that the control node has access to the internet: try to access a web page.

1. Run an nmap scan on your laptop (on the LAN, outside the VLANs) and verify the control node's hostname appears.

1. Connect the protected node(s) to the switch starting at port 1.

1. Verify that each node gets internet access.

1. Run an nmap scan on the control node - target VLAN 2. Verify that each connected protected node is connected.