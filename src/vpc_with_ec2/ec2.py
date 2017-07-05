from awacs import aws, sts
from troposphere import AWS_REGION, FindInMap, GetAtt, Join, Ref
from troposphere import autoscaling, cloudwatch, iam, policies

from loadbalancer import LoadBalancer
from magicdict import MagicDict
from parameters import Parameters
from vpc import VPC


class EC2(MagicDict):
    def __init__(self, parameters, vpc, loadbalancer):
        """
        :type parameters Parameters
        :type vpc VPC
        :type loadbalancer LoadBalancer
        """
        super(EC2, self).__init__()

        # Ec2 instance
        self.instance_role = iam.Role(
            "InstanceRole",
            AssumeRolePolicyDocument=aws.Policy(
                Statement=[
                    aws.Statement(
                        Effect=aws.Allow,
                        Action=[sts.AssumeRole],
                        Principal=aws.Principal(
                            "Service", ["ec2.amazonaws.com"]
                        )
                    )
                ]
            ),
            Path="/",
        )

        self.instance_role_policy = iam.PolicyType(
            "InstanceRolePolicy",
            PolicyName=Join("-", [Ref("AWS::StackName"), "instance-policy"]),
            PolicyDocument=aws.Policy(
                Statement=[
                    aws.Statement(
                        Effect=aws.Allow,
                        Action=[
                            aws.Action("logs", "CreateLogGroup"),
                            aws.Action("logs", "CreateLogStream"),
                            aws.Action("logs", "PutLogEvents"),
                            aws.Action("logs", "DescribeLogStreams"),
                        ],
                        Resource=["arn:aws:logs:*:*:*"]
                    )
                ]
            ),
            Roles=[Ref(self.instance_role)]
        )

        self.instance_profile = iam.InstanceProfile(
            "InstanceProfile",
            Path="/",
            Roles=[Ref(self.instance_role)]
        )

        self.launch_configuration = autoscaling.LaunchConfiguration(
            "LaunchConfiguration",
            ImageId=FindInMap("AMIMap", Ref(AWS_REGION), "AMI"),
            InstanceType=Ref(parameters.ec2_instance_type),
            KeyName=Ref(parameters.key_pair),
            InstanceMonitoring=True,
            SecurityGroups=[
                GetAtt(loadbalancer.instance_security_group, "GroupId"),
            ],
            IamInstanceProfile=Ref(self.instance_profile),
        )

        self.auto_scaling_group = autoscaling.AutoScalingGroup(
            "AutoScalingGroup",
            LaunchConfigurationName=Ref(self.launch_configuration),
            MinSize=1,
            DesiredCapacity=1,
            MaxSize=10,
            HealthCheckType='ELB',
            HealthCheckGracePeriod=300,
            VPCZoneIdentifier=[Ref(vpc.public_subnet_1), Ref(vpc.public_subnet_2)],
            LoadBalancerNames=[Ref(loadbalancer.load_balancer)],
            Tags=[
                autoscaling.Tag("Name", Ref("AWS::StackName"), True)
            ],
            UpdatePolicy=policies.UpdatePolicy(
                AutoScalingRollingUpdate=policies.AutoScalingRollingUpdate(
                    PauseTime="PT30S",
                    MinInstancesInService=1,
                    MaxBatchSize=10,
                    WaitOnResourceSignals=False
                )
            ),
            TerminationPolicies=['OldestLaunchConfiguration', 'ClosestToNextInstanceHour', 'Default'],
            MetricsCollection=[
                autoscaling.MetricsCollection(
                    Granularity="1Minute"
                )
            ]
        )

        self.scale_up_policy = autoscaling.ScalingPolicy(
            "ScaleUPPolicy",
            AdjustmentType='ChangeInCapacity',
            AutoScalingGroupName=Ref(self.auto_scaling_group),
            PolicyType='StepScaling',
            MetricAggregationType='Average',
            StepAdjustments=[
                autoscaling.StepAdjustments(
                    MetricIntervalLowerBound=0,
                    ScalingAdjustment=1
                )
            ],
        )

        self.scale_down_policy = autoscaling.ScalingPolicy(
            "ScaleDOWNPolicy",
            AdjustmentType='ChangeInCapacity',
            AutoScalingGroupName=Ref(self.auto_scaling_group),
            PolicyType='StepScaling',
            MetricAggregationType='Average',
            StepAdjustments=[
                autoscaling.StepAdjustments(
                    MetricIntervalUpperBound=0,
                    ScalingAdjustment=-1
                )
            ],
        )

        self.ec2_high_cpu_usage_alarm = cloudwatch.Alarm(
            "EC2HighCPUUsageAlarm",
            ActionsEnabled=True,
            AlarmActions=[Ref(self.scale_up_policy)],
            ComparisonOperator='GreaterThanThreshold',
            Dimensions=[cloudwatch.MetricDimension(
                Name='AutoScalingGroupName',
                Value=Ref(self.auto_scaling_group)
            )],
            EvaluationPeriods=3,
            MetricName='CPUUtilization',
            Namespace='AWS/EC2',
            Period=300,
            Statistic='Average',
            Threshold='70',
        )

        self.ec2_low_cpu_usage_alarm = cloudwatch.Alarm(
            "EC2LowCPUUsageAlarm",
            ActionsEnabled=True,
            AlarmActions=[Ref(self.scale_down_policy)],
            ComparisonOperator='LessThanThreshold',
            Dimensions=[cloudwatch.MetricDimension(
                Name='AutoScalingGroupName',
                Value=Ref(self.auto_scaling_group)
            )],
            EvaluationPeriods=3,
            MetricName='CPUUtilization',
            Namespace='AWS/EC2',
            Period=300,
            Statistic='Average',
            Threshold='20',
        )
