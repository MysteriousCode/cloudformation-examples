from troposphere import GetAZs, Join, Ref, Select, Tags, Template
from troposphere.ec2 import InternetGateway, NetworkAcl, NetworkAclEntry, Route, RouteTable, Subnet, \
    SubnetNetworkAclAssociation, SubnetRouteTableAssociation, VPC, VPCGatewayAttachment

VPC_NETWORK = "172.22.0.0/16"
VPC_PRIVATE_1 = "172.22.1.0/24"
VPC_PRIVATE_2 = "172.22.2.0/24"
VPC_PUBLIC_A = "172.22.128.0/24"
VPC_PUBLIC_1 = "172.22.129.0/24"
VPC_PUBLIC_2 = "172.22.130.0/24"

t = Template()

t.add_description("Stack creating a basic VPC")

vpc = t.add_resource(VPC(
    "VPC",
    CidrBlock=VPC_NETWORK,
    InstanceTenancy="default",
    EnableDnsSupport=True,
    EnableDnsHostnames=False,
    Tags=Tags(
        Name=Ref("AWS::StackName")
    )
))

# internet gateway
internetGateway = t.add_resource(InternetGateway(
    "InternetGateway",
    Tags=Tags(
        Name=Join("", [Ref("AWS::StackName"), "-gateway"]),
    ),
))

gatewayAttachment = t.add_resource(VPCGatewayAttachment(
    "InternetGatewayAttachment",
    InternetGatewayId=Ref(internetGateway),
    VpcId=Ref(vpc)
))

# public routing table
publicRouteTable = t.add_resource(RouteTable(
    "PublicRouteTable",
    VpcId=Ref(vpc),
    Tags=Tags(
        Name=Join("-", [Ref("AWS::StackName"), "public-rt"]),
    ),
))

privateRouteTable1 = t.add_resource(RouteTable(
    "PrivateRouteTable1",
    VpcId=Ref(vpc),
    Tags=Tags(
        Name=Join("-", [Ref("AWS::StackName"), "private-rt1"]),
    ),
))

privateRouteTable2 = t.add_resource(RouteTable(
    "PrivateRouteTable2",
    VpcId=Ref(vpc),
    Tags=Tags(
        Name=Join("-", [Ref("AWS::StackName"), "private-rt2"]),
    ),
))

internetRoute = t.add_resource(Route(
    "RouteToInternet",
    DestinationCidrBlock="0.0.0.0/0",
    GatewayId=Ref(internetGateway),
    RouteTableId=Ref(publicRouteTable),
    DependsOn=gatewayAttachment.title
))

# private subnetworks
subnetPrivate1 = t.add_resource(Subnet(
    "StackPrivateSubnet1",
    AvailabilityZone=Select(0, GetAZs()),
    CidrBlock=VPC_PRIVATE_1,
    MapPublicIpOnLaunch=False,
    Tags=Tags(
        Name=Join("", [Ref("AWS::StackName"), " private subnet 1"]),
    ),
    VpcId=Ref(vpc)
))

t.add_resource(SubnetRouteTableAssociation(
    "PrivateSubnet1RouteTable",
    RouteTableId=Ref(privateRouteTable1),
    SubnetId=Ref(subnetPrivate1)
))

subnetPrivate2 = t.add_resource(Subnet(
    "StackPrivateSubnet2",
    AvailabilityZone=Select(1, GetAZs()),
    CidrBlock=VPC_PRIVATE_2,
    MapPublicIpOnLaunch=False,
    Tags=Tags(
        Name=Join("", [Ref("AWS::StackName"), " private subnet 2"]),
    ),
    VpcId=Ref(vpc)
))

t.add_resource(SubnetRouteTableAssociation(
    "PrivateSubnet2RouteTable",
    RouteTableId=Ref(privateRouteTable2),
    SubnetId=Ref(subnetPrivate2)
))

# public subnetworks
subnetPublic1 = t.add_resource(Subnet(
    "StackPublicSubnet1",
    AvailabilityZone=Select(0, GetAZs()),
    CidrBlock=VPC_PUBLIC_1,
    MapPublicIpOnLaunch=True,
    Tags=Tags(
        Name=Join("", [Ref("AWS::StackName"), " public subnet 1"]),
    ),
    VpcId=Ref(vpc),
))

t.add_resource(SubnetRouteTableAssociation(
    "PublicSubnet1RouteTable",
    RouteTableId=Ref(publicRouteTable),
    SubnetId=Ref(subnetPublic1)
))

subnetPublic2 = t.add_resource(Subnet(
    "StackPublicSubnet2",
    AvailabilityZone=Select(1, GetAZs()),
    CidrBlock=VPC_PUBLIC_2,
    MapPublicIpOnLaunch=True,
    Tags=Tags(
        Name=Join("", [Ref("AWS::StackName"), " public subnet 2"]),
    ),
    VpcId=Ref(vpc),
))

t.add_resource(SubnetRouteTableAssociation(
    "PublicSubnet2RouteTable",
    RouteTableId=Ref(publicRouteTable),
    SubnetId=Ref(subnetPublic2)
))

# network ACL for private subnets
privateNetworkAcl = t.add_resource(NetworkAcl(
    "PrivateNetworkAcl",
    VpcId=Ref(vpc),
    Tags=Tags(
        Name=Join("", [Ref("AWS::StackName"), "-private-nacl"]),
    ),
))

t.add_resource(SubnetNetworkAclAssociation(
    "PrivateNetwork1AclAss",
    SubnetId=Ref(subnetPrivate1),
    NetworkAclId=Ref(privateNetworkAcl)
))

t.add_resource(SubnetNetworkAclAssociation(
    "PrivateNetwork2AclAss",
    SubnetId=Ref(subnetPrivate2),
    NetworkAclId=Ref(privateNetworkAcl)
))

t.add_resource(NetworkAclEntry(
    "PrivateNetworkAclEntryIngress",
    CidrBlock=VPC_NETWORK,
    Egress=False,
    NetworkAclId=Ref(privateNetworkAcl),
    Protocol=-1,
    RuleAction="allow",
    RuleNumber=200
))

t.add_resource(NetworkAclEntry(
    "PrivateNetworkAclEntryEgress",
    CidrBlock=VPC_NETWORK,
    Egress=True,
    NetworkAclId=Ref(privateNetworkAcl),
    Protocol=-1,
    RuleAction="allow",
    RuleNumber=200
))

print(t.to_json())
