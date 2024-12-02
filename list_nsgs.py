import pulumi
from pulumi_azure_native import compute, network

# Replace with your VM and resource group names
resource_group_name = "resourceGroup"  # Resource group where the VM is located
vm_name = "nginxVM"  # Name of the VM
location = "westeurope"  # Replace with the location of your resources

# Fetch the VM
vm = compute.get_virtual_machine(resource_group_name=resource_group_name, vm_name=vm_name)

# Fetch the Network Interface associated with the VM
nic_id = vm.network_profile.network_interfaces[0].id

# Get the Network Interface details
nic = network.get_network_interface(
    resource_group_name=resource_group_name,
    network_interface_name=nic_id.split('/')[-1]
)

# Check for an associated NSG
if nic.network_security_group:
    nsg_id = nic.network_security_group.id
    nsg_name = nsg_id.split('/')[-1]

    # Get NSG details
    nsg = network.get_network_security_group(
        resource_group_name=resource_group_name,
        network_security_group_name=nsg_name,
    )

    # Export NSG details
    pulumi.export("nsg_name", nsg.name)
    pulumi.export("nsg_rules", [rule.name for rule in nsg.security_rules])
else:
    pulumi.export("nsg_status", "No NSG associated with the VM's Network Interface")
