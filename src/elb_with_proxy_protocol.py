from troposphere import Template
from troposphere.elasticloadbalancing import Listener, LoadBalancer

t = Template()

t.add_description("ELB with Proxy Protocol enabled for ports 80 and 443")

elb = t.add_resource(LoadBalancer(
    "ElasticLoadBalancer",
    Listeners=[
        Listener(
            LoadBalancerPort="80",
            InstancePort="80",
            Protocol="TCP"
        ),
        Listener(
            LoadBalancerPort="443",
            InstancePort="443",
            Protocol="TCP"
        ),
    ],
    Policies=[
        {
            "PolicyName": "EnableProxyProtocol",
            "PolicyType": "ProxyProtocolPolicyType",
            "Attributes": [{
                "Name": "ProxyProtocol",
                "Value": "true"
            }],
            "InstancePorts": ["80", "443"]
        }
    ]
))

print(t.to_json())
