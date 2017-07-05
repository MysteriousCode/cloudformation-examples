from troposphere import Parameter

from magicdict import MagicDict


class Parameters(MagicDict):
    def __init__(self):
        super(Parameters, self).__init__()

        self.key_pair = Parameter(
            "KeyPair",
            Type="AWS::EC2::KeyPair::KeyName",
            Description="Key pair to use to login to your instance"
        )

        self.db_password = Parameter(
            "DBPassword",
            Type="String",
            NoEcho=True,
            MinLength=8,
            Description="Choose a secure password for your database with at least 1 small letter, 1 large letter, 1 number, minimal length: 8 characters.",
            AllowedPattern="^(?=.*[A-Z])(?=.*[0-9])(?=.*[a-z]).{8,}$",
            ConstraintDescription="Database password must be at least 8 characters, with 1 small letter, 1 large letter and 1 number. "
        )

        self.db_instance_type = Parameter(
            "DBInstanceType",
            Type="String",
            AllowedValues=[
                "db.t2.micro", "db.t2.small", "db.t2.medium", "db.t2.large",
                "db.m4.large", "db.m4.xlarge", "db.m4.2xlarge", "db.m4.4xlarge", "db.m4.10xlarge"
            ],
            Default="db.t2.micro",
            Description="Instance class for your database. Defines amount of CPU and Memory."
        )

        self.db_storage_size = Parameter(
            "DBStorageSize",
            Type="Number",
            Default="10",
            Description="Storage size for your database in GB."
        )

        self.db_backup_retention = Parameter(
            "DBBackupRetention",
            Type="Number",
            Default="7",
            Description="Number of days to store automated daily database backups for."
        )

        self.ec2_instance_type = Parameter(
            "EC2InstanceType",
            Type="String",
            AllowedValues=[
                "t2.micro", "t2.small", "t2.medium", "t2.large", "t2.xlarge", "t2.2xlarge",
                "m4.large", "m4.xlarge", "m4.2xlarge",
                "m4.4xlarge", "m4.10xlarge", "m4.16xlarge",

            ],
            Default="t2.micro",
            Description="Instance class for your server. Defines amount of CPU and Memory."
        )
