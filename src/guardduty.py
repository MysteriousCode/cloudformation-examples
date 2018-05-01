from awacs import aws
from troposphere import Parameter, Ref, Template, Equals, Condition, Not, AWS_ACCOUNT_ID
from troposphere import guardduty, sns, events

MASTER_ACCOUNT_ID = "1234"
MEMBER_ACCOUNT_ID = "5678"
MEMBER_ACCOUNT_EMAIL = "user@example.com"

t = Template()

t.add_description("GuardDuty example deployment for master and member accounts")

member_invitation = t.add_parameter(Parameter(
    "MemberInvitation",
    Type="String",
    Description="Invitation ID for member account, leave empty on master account"
))

t.add_condition("IsMaster", Equals(Ref(AWS_ACCOUNT_ID), MASTER_ACCOUNT_ID))
t.add_condition("IsMember", Not(Condition("IsMaster")))

detector = t.add_resource(guardduty.Detector(
    "Detector",
    Enable=True
))

master = t.add_resource(guardduty.Master(
    "Master",
    Condition="IsMember",
    DetectorId=Ref(detector),
    MasterId=MASTER_ACCOUNT_ID,
    InvitationId=Ref(member_invitation),
))

# You can create multiple members if you have multiple members accounts
member = t.add_resource(guardduty.Member(
    "Member",
    Condition="IsMaster",
    Status="Invited",
    MemberId=MEMBER_ACCOUNT_ID,
    Email=MEMBER_ACCOUNT_EMAIL,
    DetectorId=Ref(detector)
))

snstopic = t.add_resource(sns.Topic(
    "SNSTopic",
    Condition="IsMaster",
    Subscription=[
        # put any subscriptions here
    ]
))

event = t.add_resource(events.Rule(
    "EventsRule",
    Condition="IsMaster",
    EventPattern={
        "source": [
            "aws.guardduty"
        ]
    },
    State="ENABLED",
    Targets=[
        events.Target(
            Arn=Ref(snstopic),
            Id="sns",
        )
    ]
))

# Allow events to send notifications to SNS
t.add_resource(sns.TopicPolicy(
    "SNSTopicPolicy",
    Condition="IsMaster",
    PolicyDocument=aws.Policy(
        Statement=[
            aws.Statement(
                Effect=aws.Allow,
                Action=[
                    aws.Action("sns", "Publish"),
                ],
                Principal=aws.Principal("Service", "events.amazonaws.com"),
                Resource=[Ref(snstopic)],
            ),
        ]
    ),
    Topics=[Ref(snstopic)]
))

print(t.to_json())
