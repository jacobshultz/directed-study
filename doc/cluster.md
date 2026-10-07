# Cluster
This document details the **network configuration** for each node.

Network configuration is made of two parts: *Within the nodes* and *outside the nodes*. This document discusses the *within the nodes* part.

This doesn't cover things like docker, ansible, etc.

## NODE OVERVIEW
- **Protected / P Node** - Node which is connected to a camera, captures the images. Not accessible from the LAN. Can access the internet.
- **Controller / C node** - Node which hands out IP addresses to P nodes, does NAT, is SSH’able, runs Ansible.


## VLANs
- **VLAN 1 / Open** - Internet and LAN access. Contains the C node.
- **VLAN 2 / Protected** - Inaccessible from the LAN. Contains the P node(s) and the C node. Internet access.


## PROTECTED NODE
Each protected node is connected to a camera and captures images. There isn't any network configuration needed for these nodes.


## CONTROLLER NODE
The controller node has the following responsibilities
- Act as a gateway for the P node
- Composite file storage

### Network Interfaces

The C node must access VLAN 1 and 2. It does this by having a second network interface in addition to the default `eth0`, which is the interface for vlan1

Use nmcli To create a second network interface (`eth0.2`). Execute on the C node:
`sudo nmcli con add type vlan con-name vlan2 ifname eth0.2 dev eth0 id 2 ipv4.method manual ipv4.addresses 192.168.2.5/24 connection.autoconnect yes`

This command creates the new network interface with IP address `192.168.2.5`. We need a static IP here because the controller will give out IPs in vlan 2 after the next section. Chicken or the egg problem.

Check that the new network interface has been created by running `nmcli con show`
You sould see the line: `vlan2   (uuid)  vlan  eth0.2`

### DHCP & DNSMasq
In order to access the P node(s) from the controller we need to assign the P nodes IP addresses. To achieve this run DNSMasq on the C node.

On the C node:
Install:
`sudo apt install dnsmasq`

Create a dnsmasq configuration for vlan2 `/etc/dnsmasq.d/vlan2.conf`:
```
interface=eth0.2
bind-interfaces
dhcp-range=192.168.2.10,192.168.2.250,infinite
```

In this configuration, the IP address of the controller (on vlan2) will serve as the gateway for VLAN2.

Validate configuration:
`dnsmasq --test`

Enable and start systemd service (first time setup):
1. `sudo systemctl enable --now dnsmasq`
1. `sudo systemctl status dnsmasq`

Or restart service (config changed):
1. `sudo systemctl restart dnsmasq`
1. `sudo systemctl status dnsmasq`

### NAT & nftables
Now that the P nodes have IP addresses and are sending their traffic to the C node gateway, we need to forward this traffic to the outside internet without exposing it to the LAN.

To accomplish this, we need to configure the firewall using nftables.

Enable forwarding, create a kernel configuration file `/etc/sysctl.d/99-forward.conf`:
```
net.ipv4.ip_forward=1
```

Reload kernel params: `sudo sysctl --system`

Then create the nftables configuration - modify `/etc/nftables.conf`

Add this:
```
table inet nat {
	chain postrouting {
		type nat hook postrouting priority srcnat;
		oifname “eth0” ip saddr 192.168.0/24 masquerade
	}
}
```

Enable nftables service: `sudo systemctl enable --now nftables`

Now the P nodes should be able to access the internet while still being invisible on the LAN.
