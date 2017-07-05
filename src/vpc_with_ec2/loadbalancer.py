from troposphere import GetAtt, Join, Ref, Tags
from troposphere import ec2, elasticloadbalancing

from magicdict import MagicDict
from vpc import VPC


class LoadBalancer(MagicDict):
    def __init__(self, vpc):
        """
        :type vpc VPC
        """
        super(LoadBalancer, self).__init__()

        self.load_balancer_security_group = ec2.SecurityGroup(
            "LoadBalancerSecurityGroup",
            GroupDescription="Loadbalancer security group",
            SecurityGroupIngress=[
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=80,
                    ToPort=80,
                    CidrIp="0.0.0.0/0",
                ),
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=443,
                    ToPort=443,
                    CidrIp="0.0.0.0/0",
                ),
                ec2.SecurityGroupRule(
                    IpProtocol="icmp",
                    FromPort="-1",
                    ToPort="-1",
                    CidrIp='0.0.0.0/0',
                ),
            ],
            SecurityGroupEgress=[
                ec2.SecurityGroupRule(
                    CidrIp="172.1.0.0/16",
                    FromPort=0,
                    IpProtocol="-1",
                    ToPort=65535
                )
            ],
            VpcId=Ref(vpc.vpc)
        )

        self.load_balancer = elasticloadbalancing.LoadBalancer(
            "LoadBalancer",
            Subnets=[Ref(vpc.public_subnet_1), Ref(vpc.public_subnet_2)],
            ConnectionDrainingPolicy=elasticloadbalancing.ConnectionDrainingPolicy(
                Enabled=True,
                Timeout=300,
            ),
            CrossZone=True,
            Listeners=[
                elasticloadbalancing.Listener(
                    LoadBalancerPort="80",
                    InstancePort="80",
                    Protocol="HTTP",
                    InstanceProtocol="HTTP"
                ),
            ],
            HealthCheck=elasticloadbalancing.HealthCheck(
                Target="HTTP:80/",
                HealthyThreshold="2",
                UnhealthyThreshold="3",
                Interval="30",
                Timeout="10",
            ),
            SecurityGroups=[
                GetAtt(self.load_balancer_security_group, "GroupId"),
            ],
            DependsOn=vpc.internet_gateway_attachment.title
        )

        # EC2 instance security group
        self.instance_security_group = ec2.SecurityGroup(
            "InstanceSecurityGroup",
            GroupDescription="Instance security group",
            SecurityGroupIngress=[
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=80,
                    ToPort=80,
                    SourceSecurityGroupId=GetAtt(self.load_balancer_security_group, "GroupId"),
                ),
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=443,
                    ToPort=443,
                    SourceSecurityGroupId=GetAtt(self.load_balancer_security_group, "GroupId"),
                ),
                ec2.SecurityGroupRule(
                    IpProtocol="icmp",
                    FromPort="-1",
                    ToPort="-1",
                    SourceSecurityGroupId=GetAtt(self.load_balancer_security_group, "GroupId"),
                ),
            ],
            SecurityGroupEgress=[
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=80,
                    ToPort=80,
                    CidrIp='0.0.0.0/0',
                ),
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=443,
                    ToPort=443,
                    CidrIp='0.0.0.0/0',
                ),
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=587,
                    ToPort=587,
                    CidrIp='0.0.0.0/0',
                ),
                ec2.SecurityGroupRule(  # allow access to whole vpc
                    IpProtocol="-1",
                    FromPort="-1",
                    ToPort="-1",
                    CidrIp="172.1.0.0/16",
                ),
            ],
            VpcId=Ref(vpc.vpc),
            Tags=Tags(
                Name=Join("", [Ref("AWS::StackName"), " instance security group"]),
            ),
        )
