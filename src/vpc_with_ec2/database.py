from troposphere import Join, Ref, Tags
from troposphere import ec2, rds

from loadbalancer import LoadBalancer
from magicdict import MagicDict
from parameters import Parameters
from vpc import VPC


class Database(MagicDict):
    def __init__(self, parameters, vpc, loadbalancer):
        """
        :type parameters Parameters
        :type vpc VPC
        :type loadbalancer LoadBalancer
        """
        super(Database, self).__init__()

        self.db_security_group = ec2.SecurityGroup(
            "DBSecurityGroup",
            GroupDescription="Database security group",
            SecurityGroupIngress=[
                ec2.SecurityGroupRule(  # rds
                    IpProtocol="tcp",
                    FromPort=3306,
                    ToPort=3306,
                    SourceSecurityGroupId=Ref(loadbalancer.instance_security_group)
                )
            ],
            SecurityGroupEgress=[  # disallow outgoing connections
                {
                    "CidrIp": "127.0.0.1/32",
                    "IpProtocol": "-1"
                }
            ],
            VpcId=Ref(vpc.vpc),
            Tags=Tags(
                Name=Join("", [Ref("AWS::StackName"), " RDS security group"]),
            ),
        )

        # rds
        self.db_subnet_group = rds.DBSubnetGroup(
            "DBSubnetGroup",
            DBSubnetGroupDescription="DB Subnet group",
            SubnetIds=[
                Ref(vpc.private_subnet_1),
                Ref(vpc.private_subnet_2),
            ],
            Tags=Tags(
                Name=Join("", [Ref("AWS::StackName"), " database subnet group"]),
            )
        )

        self.database = rds.DBInstance(
            "Database",
            BackupRetentionPeriod=Ref(parameters.db_backup_retention),
            AllocatedStorage=Ref(parameters.db_storage_size),
            DBInstanceClass=Ref(parameters.db_instance_type),
            DBInstanceIdentifier=Ref("AWS::StackName"),
            Engine="MySQL",
            EngineVersion="5.6",
            MasterUsername="root",
            MasterUserPassword=Ref(parameters.db_password),
            StorageType="gp2",
            DeletionPolicy="Snapshot",
            DBSubnetGroupName=Ref(self.db_subnet_group),
            MultiAZ=True,
            VPCSecurityGroups=[Ref(self.db_security_group)],
            Tags=Tags(
                Name=Ref("AWS::StackName")
            ),
        )
