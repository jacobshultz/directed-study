**A few breif notes from 9/29/26**

Execute image capture on both nodes:
`ansible-playbook -i playbooks/inventory.yml playbooks/capture.yml -k`

The capture playbook records an image from both PIs.

It runs SSH from the cmdline of the controller node to access the protected nodes.

Protected nodes are accessed dynamically by reading the leases file.

TODO: DNS to identify nodes after DHCP reassignment