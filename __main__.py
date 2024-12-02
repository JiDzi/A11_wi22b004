import pulumi
from pulumi_azure_native import compute, network, resources
import base64

# Step 1: Create a Resource Group
resource_group = resources.ResourceGroup("resourceGroup")

# Step 2: Create a Public IP Address
public_ip = network.PublicIPAddress(
    "nginxPublicIP",
    resource_group_name=resource_group.name,
    public_ip_allocation_method="Dynamic",
)

# Step 3: Create a Virtual Network and Subnet
vnet = network.VirtualNetwork(
    "vnet",
    resource_group_name=resource_group.name,
    address_space={"addressPrefixes": ["10.0.0.0/16"]},
)

subnet = network.Subnet(
    "subnet",
    resource_group_name=resource_group.name,
    virtual_network_name=vnet.name,
    address_prefix="10.0.1.0/24",
)

# Step 4: Create a Network Security Group with HTTP rule
nsg = network.NetworkSecurityGroup(
    "nsg",
    resource_group_name=resource_group.name,
    security_rules=[
        network.SecurityRuleArgs(
            name="allow-http",
            priority=100,
            direction="Inbound",
            access="Allow",
            protocol="Tcp",
            source_port_range="*",
            destination_port_range="80",
            source_address_prefix="*",
            destination_address_prefix="*",
        ),
    ],
)

# Step 5: Create a Network Interface
nic = network.NetworkInterface(
    "nic",
    resource_group_name=resource_group.name,
    ip_configurations=[
        network.NetworkInterfaceIPConfigurationArgs(
            name="ipconfig1",
            subnet=network.SubnetArgs(id=subnet.id),
            public_ip_address=network.PublicIPAddressArgs(id=public_ip.id),
        ),
    ],
    network_security_group=network.NetworkSecurityGroupArgs(id=nsg.id),
)

# Base64 encode the startup script for the VM
startup_script = """#!/bin/bash
sudo apt-get update
sudo apt-get install -y nginx
sudo systemctl start nginx
sudo systemctl enable nginx
"""
encoded_script = base64.b64encode(startup_script.encode("utf-8")).decode("utf-8")

# Step 6: Create a Virtual Machine
vm = compute.VirtualMachine(
    "nginxVM",
    resource_group_name=resource_group.name,
    network_profile=compute.NetworkProfileArgs(
        network_interfaces=[
            compute.NetworkInterfaceReferenceArgs(id=nic.id)
        ]
    ),
    os_profile=compute.OSProfileArgs(
        computer_name="nginxvm",
        admin_username="azureuser",
        admin_password="P@ssw0rd1234!",  # Replace with a secure password
        custom_data=encoded_script,  # Base64-encoded script
    ),
    storage_profile=compute.StorageProfileArgs(
        os_disk=compute.OSDiskArgs(
            create_option="FromImage",
            managed_disk=compute.ManagedDiskParametersArgs(
                storage_account_type="Standard_LRS",
            ),
        ),
        image_reference=compute.ImageReferenceArgs(
            publisher="Canonical",
            offer="UbuntuServer",
            sku="18.04-LTS",
            version="latest",
        ),
    ),
    hardware_profile=compute.HardwareProfileArgs(
        vm_size="Standard_B1s",  # Use a small VM size to save costs
    ),
)

# Export the Public IP Address of the VM
pulumi.export("vm_public_ip", public_ip.ip_address)
