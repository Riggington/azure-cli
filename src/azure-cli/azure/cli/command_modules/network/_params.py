# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, too-many-lines
from argcomplete.completers import FilesCompleter

import six

from knack.arguments import CLIArgumentType, ignore_type

from azure.cli.core.commands.parameters import (get_location_type, get_resource_name_completion_list,
                                                tags_type, zone_type, zones_type,
                                                file_type, get_resource_group_completion_list,
                                                get_three_state_flag, get_enum_type)
from azure.cli.core.commands.validators import get_default_location_from_resource_group
from azure.cli.core.commands.template_create import get_folded_parameter_help_string
from azure.cli.command_modules.network._validators import (
    dns_zone_name_type,
    validate_ssl_cert, validate_cert, validate_inbound_nat_rule_id_list,
    validate_address_pool_id_list, validate_inbound_nat_rule_name_or_id,
    validate_address_pool_name_or_id, load_cert_file, validate_metadata,
    validate_peering_type, validate_dns_record_type, validate_route_filter, validate_target_listener,
    validate_private_ip_address,
    get_servers_validator, get_public_ip_validator, get_nsg_validator, get_subnet_validator,
    get_network_watcher_from_vm, get_network_watcher_from_location,
    get_asg_validator, get_vnet_validator, validate_ip_tags, validate_ddos_name_or_id,
    validate_service_endpoint_policy, validate_delegations, validate_subresource_list,
    validate_er_peer_circuit, validate_ag_address_pools, validate_custom_error_pages,
    validate_custom_headers, validate_status_code_ranges, validate_subnet_ranges,
    WafConfigExclusionAction, validate_express_route_peering, validate_virtual_hub,
    validate_express_route_port, bandwidth_validator_factory,
    get_header_configuration_validator, validate_nat_gateway, validate_match_variables,
    validate_waf_policy, get_subscription_list_validator, validate_frontend_ip_configs,
    validate_application_gateway_identity)
from azure.mgmt.trafficmanager.models import MonitorProtocol, ProfileStatus
from azure.cli.command_modules.network._completers import (
    subnet_completion_list, get_lb_subresource_completion_list, get_ag_subresource_completion_list,
    ag_url_map_rule_completion_list, tm_endpoint_completion_list, service_endpoint_completer,
    get_sdk_completer)
from azure.cli.core.util import get_json_object


# pylint: disable=too-many-locals, too-many-branches, too-many-statements
def load_arguments(self, _):

    (Access, ApplicationGatewayFirewallMode, ApplicationGatewayProtocol, ApplicationGatewayRedirectType,
     ApplicationGatewayRequestRoutingRuleType, ApplicationGatewaySkuName, ApplicationGatewaySslProtocol, AuthenticationMethod,
     Direction,
     ExpressRouteCircuitSkuFamily, ExpressRouteCircuitSkuTier, ExpressRoutePortsEncapsulation,
     FlowLogFormatType, HTTPMethod, IPAllocationMethod,
     IPVersion, LoadBalancerSkuName, LoadDistribution, ProbeProtocol, ProcessorArchitecture, Protocol, PublicIPAddressSkuName,
     RouteNextHopType, SecurityRuleAccess, SecurityRuleProtocol, SecurityRuleDirection, TransportProtocol,
     VirtualNetworkGatewaySkuName, VirtualNetworkGatewayType, VpnClientProtocol, VpnType, ZoneType) = self.get_models(
         'Access', 'ApplicationGatewayFirewallMode', 'ApplicationGatewayProtocol', 'ApplicationGatewayRedirectType',
         'ApplicationGatewayRequestRoutingRuleType', 'ApplicationGatewaySkuName', 'ApplicationGatewaySslProtocol', 'AuthenticationMethod',
         'Direction',
         'ExpressRouteCircuitSkuFamily', 'ExpressRouteCircuitSkuTier', 'ExpressRoutePortsEncapsulation',
         'FlowLogFormatType', 'HTTPMethod', 'IPAllocationMethod',
         'IPVersion', 'LoadBalancerSkuName', 'LoadDistribution', 'ProbeProtocol', 'ProcessorArchitecture', 'Protocol', 'PublicIPAddressSkuName',
         'RouteNextHopType', 'SecurityRuleAccess', 'SecurityRuleProtocol', 'SecurityRuleDirection', 'TransportProtocol',
         'VirtualNetworkGatewaySkuName', 'VirtualNetworkGatewayType', 'VpnClientProtocol', 'VpnType', 'ZoneType')

    if self.supported_api_version(min_api='2018-02-01'):
        ExpressRoutePeeringType = self.get_models('ExpressRoutePeeringType')
    else:
        # for Stack compatibility
        ExpressRoutePeeringType = self.get_models('ExpressRouteCircuitPeeringType')

    default_existing = 'If only one exists, omit to use as default.'

    # taken from Xplat. No enums in SDK
    routing_registry_values = ['ARIN', 'APNIC', 'AFRINIC', 'LACNIC', 'RIPENCC', 'RADB', 'ALTDB', 'LEVEL3']

    name_arg_type = CLIArgumentType(options_list=['--name', '-n'], metavar='NAME')
    nic_type = CLIArgumentType(options_list='--nic-name', metavar='NAME', help='The network interface (NIC).', id_part='name', completer=get_resource_name_completion_list('Microsoft.Network/networkInterfaces'))
    nsg_name_type = CLIArgumentType(options_list='--nsg-name', metavar='NAME', help='Name of the network security group.')
    circuit_name_type = CLIArgumentType(options_list='--circuit-name', metavar='NAME', help='ExpressRoute circuit name.', id_part='name', completer=get_resource_name_completion_list('Microsoft.Network/expressRouteCircuits'))
    virtual_network_name_type = CLIArgumentType(options_list='--vnet-name', metavar='NAME', help='The virtual network (VNet) name.', completer=get_resource_name_completion_list('Microsoft.Network/virtualNetworks'))
    subnet_name_type = CLIArgumentType(options_list='--subnet-name', metavar='NAME', help='The subnet name.')
    load_balancer_name_type = CLIArgumentType(options_list='--lb-name', metavar='NAME', help='The load balancer name.', completer=get_resource_name_completion_list('Microsoft.Network/loadBalancers'), id_part='name')
    private_ip_address_type = CLIArgumentType(help='Static private IP address to use.', validator=validate_private_ip_address)
    cookie_based_affinity_type = CLIArgumentType(arg_type=get_three_state_flag(positive_label='Enabled', negative_label='Disabled', return_label=True))
    http_protocol_type = CLIArgumentType(get_enum_type(ApplicationGatewayProtocol))
    ag_servers_type = CLIArgumentType(nargs='+', help='Space-separated list of IP addresses or DNS names corresponding to backend servers.', validator=get_servers_validator())
    app_gateway_name_type = CLIArgumentType(help='Name of the application gateway.', options_list='--gateway-name', completer=get_resource_name_completion_list('Microsoft.Network/applicationGateways'), id_part='name')

    # region NetworkRoot
    with self.argument_context('network') as c:
        c.argument('subnet_name', subnet_name_type)
        c.argument('virtual_network_name', virtual_network_name_type, id_part='name')
        c.argument('tags', tags_type)
        c.argument('network_security_group_name', nsg_name_type, id_part='name')
        c.argument('private_ip_address', private_ip_address_type)
        c.argument('private_ip_address_version', arg_type=get_enum_type(IPVersion))
        c.argument('enable_tcp_reset', arg_type=get_three_state_flag(), help='Receive bidirectional TCP reset on TCP flow idle timeout or unexpected connection termination. Only used when protocol is set to TCP.', min_api='2018-07-01')
        c.argument('location', get_location_type(self.cli_ctx), validator=get_default_location_from_resource_group)
        c.argument('cache_result', arg_type=get_enum_type(['in', 'out', 'inout']), options_list='--cache', help='Cache the JSON object instead of sending off immediately.')
    # endregion

    # region ApplicationGateways
    with self.argument_context('network application-gateway') as c:
        c.argument('application_gateway_name', app_gateway_name_type, options_list=['--name', '-n'])
        c.argument('sku', arg_group='Gateway', help='The name of the SKU.', arg_type=get_enum_type(ApplicationGatewaySkuName), default=ApplicationGatewaySkuName.standard_medium.value)
        c.argument('min_capacity', min_api='2018-07-01', help='Lower bound on the number of application gateway instances.', type=int)
        c.argument('max_capacity', min_api='2018-12-01', help='Upper bound on the number of application gateway instances.', type=int)
        c.ignore('virtual_network_type', 'private_ip_address_allocation')
        c.argument('zones', zones_type)
        c.argument('custom_error_pages', min_api='2018-08-01', nargs='+', help='Space-separated list of custom error pages in `STATUS_CODE=URL` format.', validator=validate_custom_error_pages)
        c.argument('firewall_policy', options_list='--waf-policy', min_api='2018-12-01', help='Name or ID of a web application firewall (WAF) policy.', validator=validate_waf_policy)

    with self.argument_context('network application-gateway', arg_group='Identity') as c:
        c.argument('user_assigned_identity', options_list='--identity', help="Name or ID of the ManagedIdentity Resource", validator=validate_application_gateway_identity)

    with self.argument_context('network application-gateway', arg_group='Network') as c:
        c.argument('virtual_network_name', virtual_network_name_type)
        c.argument('private_ip_address')
        c.argument('public_ip_address_allocation', help='The kind of IP allocation to use when creating a new public IP.', default=IPAllocationMethod.dynamic.value)
        c.argument('subnet_address_prefix', help='The CIDR prefix to use when creating a new subnet.')
        c.argument('vnet_address_prefix', help='The CIDR prefix to use when creating a new VNet.')

    with self.argument_context('network application-gateway', arg_group='Gateway') as c:
        c.argument('servers', ag_servers_type)
        c.argument('capacity', help='The number of instances to use with the application gateway.', type=int)
        c.argument('http_settings_cookie_based_affinity', cookie_based_affinity_type, help='Enable or disable HTTP settings cookie-based affinity.')
        c.argument('http_settings_protocol', http_protocol_type, help='The HTTP settings protocol.')
        c.argument('enable_http2', arg_type=get_three_state_flag(positive_label='Enabled', negative_label='Disabled'), options_list=['--http2'], help='Use HTTP2 for the application gateway.', min_api='2017-10-01')
        c.ignore('public_ip_address_type', 'frontend_type', 'subnet_type')

    with self.argument_context('network application-gateway create') as c:
        c.argument('validate', help='Generate and validate the ARM template without creating any resources.', action='store_true')
        c.argument('routing_rule_type', arg_group='Gateway', help='The request routing rule type.', arg_type=get_enum_type(ApplicationGatewayRequestRoutingRuleType))
        public_ip_help = get_folded_parameter_help_string('public IP address', allow_none=True, allow_new=True, default_none=True)
        c.argument('public_ip_address', help=public_ip_help, completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'), arg_group='Network')
        subnet_help = get_folded_parameter_help_string('subnet', other_required_option='--vnet-name', allow_new=True)
        c.argument('subnet', help=subnet_help, completer=subnet_completion_list, arg_group='Network')

    with self.argument_context('network application-gateway create', arg_group='Gateway') as c:
        c.argument('cert_data', options_list='--cert-file', type=file_type, completer=FilesCompleter(), help='The path to the PFX certificate file.')
        c.argument('frontend_port', help='The front end port number.')
        c.argument('cert_password', help='The certificate password')
        c.argument('http_settings_port', help='The HTTP settings port.')
        c.argument('servers', ag_servers_type)
        c.argument('key_vault_secret_id', help="Secret Id of (base-64 encoded unencrypted pfx) 'Secret' or 'Certificate' object stored in Azure KeyVault. You need enable soft delete for keyvault to use this feature.", is_preview=True)

    with self.argument_context('network application-gateway update', arg_group=None) as c:
        c.argument('sku', default=None)
        c.argument('enable_http2')
        c.argument('capacity', help='The number of instances to use with the application gateway.', type=int)

    ag_subresources = [
        {'name': 'auth-cert', 'display': 'authentication certificate', 'ref': 'authentication_certificates'},
        {'name': 'ssl-cert', 'display': 'SSL certificate', 'ref': 'ssl_certificates'},
        {'name': 'frontend-ip', 'display': 'frontend IP configuration', 'ref': 'frontend_ip_configurations'},
        {'name': 'frontend-port', 'display': 'frontend port', 'ref': 'frontend_ports'},
        {'name': 'address-pool', 'display': 'backend address pool', 'ref': 'backend_address_pools'},
        {'name': 'http-settings', 'display': 'backed HTTP settings', 'ref': 'backend_http_settings_collection'},
        {'name': 'http-listener', 'display': 'HTTP listener', 'ref': 'http_listeners'},
        {'name': 'rule', 'display': 'request routing rule', 'ref': 'request_routing_rules'},
        {'name': 'probe', 'display': 'probe', 'ref': 'probes'},
        {'name': 'url-path-map', 'display': 'URL path map', 'ref': 'url_path_maps'},
        {'name': 'redirect-config', 'display': 'redirect configuration', 'ref': 'redirect_configurations'}
    ]
    if self.supported_api_version(min_api='2018-08-01'):
        ag_subresources.append({'name': 'root-cert', 'display': 'trusted root certificate', 'ref': 'trusted_root_certificates'})
    if self.supported_api_version(min_api='2018-12-01'):
        ag_subresources.append({'name': 'rewrite-rule set', 'display': 'rewrite rule set', 'ref': 'rewrite_rule_sets'})

    for item in ag_subresources:
        with self.argument_context('network application-gateway {}'.format(item['name'])) as c:
            c.argument('item_name', options_list=['--name', '-n'], id_part='child_name_1', help='The name of the {}.'.format(item['display']), completer=get_ag_subresource_completion_list(item['ref']))
            c.argument('resource_name', options_list='--gateway-name', help='The name of the application gateway.', id_part='name')
            c.argument('application_gateway_name', app_gateway_name_type)
            c.argument('private_ip_address', arg_group=None)
            c.argument('virtual_network_name', arg_group=None)

        with self.argument_context('network application-gateway {} create'.format(item['name'])) as c:
            c.argument('item_name', options_list=['--name', '-n'], help='The name of the {}.'.format(item['display']), completer=None)

        with self.argument_context('network application-gateway {} list'.format(item['name'])) as c:
            c.argument('resource_name', options_list=['--gateway-name'], id_part=None)

    for item in ['create', 'http-settings']:
        with self.argument_context('network application-gateway {}'.format(item)) as c:
            c.argument('connection_draining_timeout', min_api='2016-12-01', type=int, help='The time in seconds after a backend server is removed during which on open connection remains active. Range: 0 (disabled) to 3600', arg_group='Gateway' if item == 'create' else None)

    with self.argument_context('network application-gateway address-pool') as c:
        c.argument('servers', ag_servers_type, arg_group=None)

    for scope in ['auth-cert', 'root-cert']:
        with self.argument_context('network application-gateway {}'.format(scope)) as c:
            c.argument('cert_data', options_list='--cert-file', help='Certificate file path.', type=file_type, completer=FilesCompleter(), validator=validate_cert)

    with self.argument_context('network application-gateway root-cert') as c:
        c.argument('keyvault_secret', help='KeyVault secret ID.')

    with self.argument_context('network application-gateway frontend-ip') as c:
        c.argument('subnet', validator=get_subnet_validator(), help='The name or ID of the subnet.')
        c.argument('public_ip_address', validator=get_public_ip_validator(), help='The name or ID of the public IP address.', completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'))
        c.argument('virtual_network_name', help='The name of the virtual network corresponding to the subnet.', id_part=None, arg_group=None)

    for item in ['frontend-port', 'http-settings']:
        with self.argument_context('network application-gateway {}'.format(item)) as c:
            c.argument('port', help='The port number.', type=int)

    for item in ['http-settings', 'probe']:
        with self.argument_context('network application-gateway {}'.format(item)) as c:
            c.argument('protocol', http_protocol_type, help='The HTTP settings protocol.')

    with self.argument_context('network application-gateway http-listener') as c:
        c.argument('frontend_ip', help='The name or ID of the frontend IP configuration.', completer=get_ag_subresource_completion_list('frontend_ip_configurations'))
        c.argument('frontend_port', help='The name or ID of the frontend port.', completer=get_ag_subresource_completion_list('frontend_ports'))
        c.argument('ssl_cert', help='The name or ID of the SSL certificate to use.', completer=get_ag_subresource_completion_list('ssl_certificates'))
        c.ignore('protocol')
        c.argument('host_name', help='Host name to use for multisite gateways.')

    with self.argument_context('network application-gateway http-listener create') as c:
        c.argument('frontend_ip', help='The name or ID of the frontend IP configuration. {}'.format(default_existing))

    with self.argument_context('network application-gateway rewrite-rule') as c:
        rewrite_rule_set_name_type = CLIArgumentType(help='Name of the rewrite rule set.', options_list='--rule-set-name', id_part='child_name_1')
        rewrite_rule_name_type = CLIArgumentType(help='Name of the rewrite rule.', options_list='--rule-name', id_part='child_name_2')
        c.argument('rule_name', rewrite_rule_name_type, options_list=['--name', '-n'])
        c.argument('rule_set_name', rewrite_rule_set_name_type)
        c.argument('application_gateway_name', app_gateway_name_type)
        c.argument('response_headers', nargs='+', help='Space-separated list of HEADER=VALUE pairs.', validator=get_header_configuration_validator('response_headers'), completer=get_sdk_completer('application_gateways', 'list_available_response_headers'))
        c.argument('request_headers', nargs='+', help='Space-separated list of HEADER=VALUE pairs.', validator=get_header_configuration_validator('request_headers'), completer=get_sdk_completer('application_gateways', 'list_available_request_headers'))
        c.argument('sequence', type=int, help='Determines the execution order of the rule in the rule set.')

    with self.argument_context('network application-gateway rewrite-rule condition') as c:
        c.argument('rule_name', rewrite_rule_name_type)
        c.argument('variable', help='The variable whose value is being evaluated.', completer=get_sdk_completer('application_gateways', 'list_available_server_variables'))
        c.argument('pattern', help='The pattern, either fixed string or regular expression, that evaluates the truthfulness of the condition')
        c.argument('ignore_case', arg_type=get_three_state_flag(), help='Make comparison case-insensitive.')
        c.argument('negate', arg_type=get_three_state_flag(), help='Check the negation of the condition.')

    with self.argument_context('network application-gateway rule create') as c:
        c.argument('address_pool', help='The name or ID of the backend address pool. {}'.format(default_existing))
        c.argument('http_settings', help='The name or ID of the HTTP settings. {}'.format(default_existing))
        c.argument('http_listener', help='The name or ID of the HTTP listener. {}'.format(default_existing))

    for scope in ['rewrite-rule list', 'rewrite-rule condition list']:
        with self.argument_context('network application-gateway {}'.format(scope)) as c:
            c.argument('application_gateway_name', app_gateway_name_type, id_part=None)

    with self.argument_context('network lb rule create') as c:
        c.argument('backend_address_pool_name', help='The name of the backend address pool. {}'.format(default_existing))
        c.argument('frontend_ip_name', help='The name of the frontend IP configuration. {}'.format(default_existing))

    for item in ['rule', 'pool']:
        with self.argument_context('network lb inbound-nat-{} create'.format(item)) as c:
            c.argument('frontend_ip_name', help='The name of the frontend IP configuration. {}'.format(default_existing))

    with self.argument_context('network application-gateway http-settings') as c:
        c.argument('cookie_based_affinity', cookie_based_affinity_type, help='Enable or disable cookie-based affinity.')
        c.argument('timeout', help='Request timeout in seconds.')
        c.argument('probe', help='Name or ID of the probe to associate with the HTTP settings.', completer=get_ag_subresource_completion_list('probes'))
        c.argument('auth_certs', nargs='+', min_api='2016-09-01', help='Space-separated list of authentication certificates (names or IDs) to associate with the HTTP settings.')
        c.argument('root_certs', nargs='+', min_api='2019-04-01', help='Space-separated list of trusted root certificates (names or IDs) to associate with the HTTP settings. --host-name or --host-name-from-backend-pool is required when this field is set.')

    with self.argument_context('network application-gateway probe') as c:
        c.argument('host', help='The name of the host to send the probe.')
        c.argument('path', help='The relative path of the probe. Valid paths start from "/"')
        c.argument('interval', help='The time interval in seconds between consecutive probes.')
        c.argument('threshold', help='The number of failed probes after which the back end server is marked down.')
        c.argument('timeout', help='The probe timeout in seconds.')

    with self.argument_context('network application-gateway rule') as c:
        c.argument('address_pool', help='The name or ID of the backend address pool.', completer=get_ag_subresource_completion_list('backend_address_pools'))
        c.argument('http_listener', help='The name or ID of the HTTP listener.', completer=get_ag_subresource_completion_list('http_listeners'))
        c.argument('http_settings', help='The name or ID of the backend HTTP settings.', completer=get_ag_subresource_completion_list('backend_http_settings_collection'))
        c.argument('rule_type', help='The rule type (Basic, PathBasedRouting).')
        c.argument('url_path_map', help='The name or ID of the URL path map.', completer=get_ag_subresource_completion_list('url_path_maps'))

    with self.argument_context('network application-gateway ssl-cert') as c:
        c.argument('cert_data', options_list='--cert-file', type=file_type, completer=FilesCompleter(), help='The path to the PFX certificate file.', validator=validate_ssl_cert)
        c.argument('cert_password', help='Certificate password.')
        c.argument('key_vault_secret_id', help="Secret Id of (base-64 encoded unencrypted pfx) 'Secret' or 'Certificate' object stored in Azure KeyVault.", is_preview=True)

    with self.argument_context('network application-gateway ssl-policy') as c:
        c.argument('clear', action='store_true', help='Clear SSL policy.')
        c.argument('disabled_ssl_protocols', nargs='+', help='Space-separated list of protocols to disable.', arg_type=get_enum_type(ApplicationGatewaySslProtocol))

    with self.argument_context('network application-gateway url-path-map') as c:
        c.argument('rule_name', help='The name of the url-path-map rule.', arg_group='First Rule')
        c.argument('paths', nargs='+', help='Space-separated list of paths to associate with the rule. Valid paths start and end with "/" (ex: "/bar/")', arg_group='First Rule')
        c.argument('address_pool', help='The name or ID of the backend address pool to use with the created rule.', completer=get_ag_subresource_completion_list('backend_address_pools'), arg_group='First Rule')
        c.argument('http_settings', help='The name or ID of the HTTP settings to use with the created rule.', completer=get_ag_subresource_completion_list('backend_http_settings_collection'), arg_group='First Rule')

    with self.argument_context('network application-gateway url-path-map create') as c:
        c.argument('default_address_pool', help='The name or ID of the default backend address pool, if different from --address-pool.', completer=get_ag_subresource_completion_list('backend_address_pools'))
        c.argument('default_http_settings', help='The name or ID of the default HTTP settings, if different from --http-settings.', completer=get_ag_subresource_completion_list('backend_http_settings_collection'))

    with self.argument_context('network application-gateway url-path-map update') as c:
        c.argument('default_address_pool', help='The name or ID of the default backend address pool.', completer=get_ag_subresource_completion_list('backend_address_pools'))
        c.argument('default_http_settings', help='The name or ID of the default HTTP settings.', completer=get_ag_subresource_completion_list('backend_http_settings_collection'))

    with self.argument_context('network application-gateway url-path-map rule') as c:
        c.argument('item_name', options_list=['--name', '-n'], help='The name of the url-path-map rule.', completer=ag_url_map_rule_completion_list, id_part='child_name_2')
        c.argument('url_path_map_name', options_list='--path-map-name', help='The name of the URL path map.', completer=get_ag_subresource_completion_list('url_path_maps'), id_part='child_name_1')
        c.argument('address_pool', help='The name or ID of the backend address pool. If not specified, the default for the map will be used.', completer=get_ag_subresource_completion_list('backend_address_pools'))
        c.argument('http_settings', help='The name or ID of the HTTP settings. If not specified, the default for the map will be used.', completer=get_ag_subresource_completion_list('backend_http_settings_collection'))
        for item in ['address_pool', 'http_settings', 'redirect_config', 'paths']:
            c.argument(item, arg_group=None)

    with self.argument_context('network application-gateway url-path-map rule create') as c:
        c.argument('item_name', options_list=['--name', '-n'], help='The name of the url-path-map rule.', completer=None)

    with self.argument_context('network application-gateway waf-config') as c:
        c.argument('disabled_rule_groups', nargs='+')
        c.argument('disabled_rules', nargs='+')
        c.argument('enabled', help='Specify whether the application firewall is enabled.', arg_type=get_enum_type(['true', 'false']))
        c.argument('firewall_mode', min_api='2016-09-01', help='Web application firewall mode.', arg_type=get_enum_type(ApplicationGatewayFirewallMode, default='detection'))

    with self.argument_context('network application-gateway waf-config', min_api='2018-08-01') as c:
        c.argument('file_upload_limit', help='File upload size limit in MB.', type=int)
        c.argument('max_request_body_size', help='Max request body size in KB.', type=int)
        c.argument('request_body_check', arg_type=get_three_state_flag(), help='Allow WAF to check the request body.')
        c.argument('exclusions', nargs='+', options_list='--exclusion', action=WafConfigExclusionAction)

    for item in ['ssl-policy', 'waf-config']:
        with self.argument_context('network application-gateway {}'.format(item)) as c:
            c.argument('application_gateway_name', app_gateway_name_type)

    with self.argument_context('network application-gateway waf-config list-rule-sets') as c:
        c.argument('_type', options_list=['--type'])

    with self.argument_context('network application-gateway redirect-config', min_api='2017-06-01') as c:
        c.argument('redirect_type', options_list=['--type', '-t'], help='HTTP redirection type', arg_type=get_enum_type(ApplicationGatewayRedirectType))
        c.argument('include_path', arg_type=get_three_state_flag())
        c.argument('include_query_string', arg_type=get_three_state_flag())
        c.argument('target_listener', validator=validate_target_listener, help='Name or ID of the HTTP listener to redirect the request to.')
        c.argument('target_url', help='URL to redirect the request to.')

    with self.argument_context('network application-gateway ssl-policy predefined', min_api='2017-06-01') as c:
        c.argument('predefined_policy_name', name_arg_type)

    with self.argument_context('network application-gateway ssl-policy', min_api='2017-06-01') as c:
        c.argument('policy_name', name_arg_type)
        c.argument('cipher_suites', nargs='+')
        c.argument('min_protocol_version')
        c.argument('disabled_ssl_protocols', nargs='+', help='Space-separated list of protocols to disable.')

    with self.argument_context('network application-gateway http-settings', min_api='2017-06-01') as c:
        c.argument('host_name', help='Host header sent to the backend servers.')
        c.argument('host_name_from_backend_pool', help='Use host name of the backend server as the host header.', arg_type=get_three_state_flag())
        c.argument('affinity_cookie_name', help='Name used for the affinity cookie.')
        c.argument('enable_probe', help='Whether the probe is enabled.', arg_type=get_three_state_flag())
        c.argument('path', help='Path that will prefix all HTTP requests.')

    with self.argument_context('network application-gateway probe', min_api='2017-06-01') as c:
        c.argument('host', default=None, required=False, help='The name of the host to send the probe.')
        c.argument('host_name_from_http_settings', help='Use host header from HTTP settings.', arg_type=get_three_state_flag())
        c.argument('min_servers', type=int, help='Minimum number of servers that are always marked healthy.')
        c.argument('match_body', help='Body that must be contained in the health response.')
        c.argument('match_status_codes', nargs='+', help='Space-separated list of allowed ranges of healthy status codes for the health response.')

    with self.argument_context('network application-gateway url-path-map', min_api='2017-06-01') as c:
        c.argument('default_redirect_config', help='The name or ID of the default redirect configuration.')
        c.argument('redirect_config', help='The name or ID of the redirect configuration to use with the created rule.', arg_group='First Rule')

    with self.argument_context('network application-gateway rule', min_api='2017-06-01') as c:
        c.argument('redirect_config', help='The name or ID of the redirect configuration to use with the created rule.')

    with self.argument_context('network application-gateway identity', min_api='2019-04-01') as c:
        c.argument('application_gateway_name', app_gateway_name_type)
    # endregion

    # region ApplicationGatewayWAFPolicies
    (WebApplicationFirewallAction, WebApplicationFirewallMatchVariable,
     WebApplicationFirewallOperator, WebApplicationFirewallRuleType,
     WebApplicationFirewallTransform) = self.get_models(
         'WebApplicationFirewallAction', 'WebApplicationFirewallMatchVariable',
         'WebApplicationFirewallOperator', 'WebApplicationFirewallRuleType',
         'WebApplicationFirewallTransform')
    with self.argument_context('network application-gateway waf-policy', min_api='2018-12-01') as c:
        c.argument('policy_name', name_arg_type, id_part='name', help='The name of the application gateway WAF policy.')

    with self.argument_context('network application-gateway waf-policy rule', min_api='2018-12-01') as c:
        c.argument('policy_name', options_list='--policy-name')
        c.argument('rule_name', options_list=['--name', '-n'], id_part='child_name_1', help='Name of the WAF policy rule.')
        c.argument('priority', type=int, help='Rule priority. Lower values are evaluated prior to higher values.')
        c.argument('action', arg_type=get_enum_type(WebApplicationFirewallAction), help='Action to take.')
        c.argument('rule_type', arg_type=get_enum_type(WebApplicationFirewallRuleType), help='Type of rule.')

    with self.argument_context('network application-gateway waf-policy rule list', min_api='2018-12-01') as c:
        c.argument('policy_name', options_list='--policy-name', id_part=None)

    with self.argument_context('network application-gateway waf-policy rule match-condition', min_api='2018-12-01') as c:
        c.argument('operator', arg_type=get_enum_type(WebApplicationFirewallOperator), help='Operator for matching.')
        c.argument('negation_condition', options_list='--negate', arg_type=get_three_state_flag(), help='Match the negative of the condition.')
        c.argument('match_values', options_list='--values', nargs='+', help='Space-separated list of values to match.')
        c.argument('transforms', arg_type=get_enum_type(WebApplicationFirewallTransform), nargs='+', help='Space-separated list of transforms to apply when matching.')
        if WebApplicationFirewallMatchVariable:
            help_string = 'Space-separated list of `VARIABLE[.SELECTOR]` variables to use when matching. Variable values: {}'.format(', '.join(x for x in WebApplicationFirewallMatchVariable))
            c.argument('match_variables', nargs='+', help=help_string, validator=validate_match_variables)
        c.argument('index', type=int, help='Index of the match condition to remove.')

    with self.argument_context('network application-gateway waf-policy rule match-condition list', min_api='2018-12-01') as c:
        c.argument('policy_name', options_list='--policy-name', id_part=None)
    # region

    # region ApplicationSecurityGroups
    with self.argument_context('network asg') as c:
        c.argument('application_security_group_name', name_arg_type, id_part='name', help='The name of the application security group.')
    # endregion

    # region DDoS Protection Plans
    with self.argument_context('network ddos-protection') as c:
        for dest in ['ddos_plan_name', 'ddos_protection_plan_name']:
            c.argument(dest, name_arg_type, help='Name of the DDoS protection plan.', id_part='name')
        c.argument('vnets', nargs='*', help='Space-separated list of VNets (name or IDs) to associate with the plan.', validator=get_vnet_validator('vnets'))
    # endregion

    # region DNS
    with self.argument_context('network dns') as c:
        c.argument('record_set_name', name_arg_type, help='The name of the record set, relative to the name of the zone.')
        c.argument('relative_record_set_name', name_arg_type, help='The name of the record set, relative to the name of the zone.')
        c.argument('zone_name', options_list=['--zone-name', '-z'], help='The name of the zone.', type=dns_zone_name_type)
        c.argument('metadata', nargs='+', help='Metadata in space-separated key=value pairs. This overwrites any existing metadata.', validator=validate_metadata)

    with self.argument_context('network dns list-references') as c:
        c.argument('target_resources', nargs='+', help='Space-separated list of resource IDs you wish to query.', validator=validate_subresource_list)

    with self.argument_context('network dns zone') as c:
        c.argument('zone_name', name_arg_type)
        c.ignore('location')

        c.argument('zone_type', help='Type of DNS zone to create.', arg_type=get_enum_type(ZoneType))
        c.argument('registration_vnets', arg_group='Private Zone', nargs='+', help='Space-separated names or IDs of virtual networks that register hostnames in this DNS zone.', validator=get_vnet_validator('registration_vnets'))
        c.argument('resolution_vnets', arg_group='Private Zone', nargs='+', help='Space-separated names or IDs of virtual networks that resolve records in this DNS zone.', validator=get_vnet_validator('resolution_vnets'))

    with self.argument_context('network dns zone import') as c:
        c.argument('file_name', options_list=['--file-name', '-f'], type=file_type, completer=FilesCompleter(), help='Path to the DNS zone file to import')

    with self.argument_context('network dns zone export') as c:
        c.argument('file_name', options_list=['--file-name', '-f'], type=file_type, completer=FilesCompleter(), help='Path to the DNS zone file to save')

    with self.argument_context('network dns zone update') as c:
        c.ignore('if_none_match')

    with self.argument_context('network dns zone create') as c:
        c.argument('parent_zone_name', options_list=['--parent-name', '-p'], help='Specify if parent zone exists for this zone and delegation for the child zone in the parent is to be added.')

    with self.argument_context('network dns record-set') as c:
        c.argument('target_resource', min_api='2018-05-01', help='ID of an Azure resource from which the DNS resource value is taken.')
        for item in ['record_type', 'record_set_type']:
            c.argument(item, ignore_type, validator=validate_dns_record_type)

    for item in ['', 'a', 'aaaa', 'caa', 'cname', 'mx', 'ns', 'ptr', 'srv', 'txt']:
        with self.argument_context('network dns record-set {} create'.format(item)) as c:
            c.argument('ttl', help='Record set TTL (time-to-live)')
            c.argument('if_none_match', help='Create the record set only if it does not already exist.', action='store_true')

    for item in ['a', 'aaaa', 'caa', 'cname', 'mx', 'ns', 'ptr', 'srv', 'txt']:
        with self.argument_context('network dns record-set {} add-record'.format(item)) as c:
            c.argument('record_set_name', options_list=['--record-set-name', '-n'], help='The name of the record set relative to the zone. Creates a new record set if one does not exist.')

        with self.argument_context('network dns record-set {} remove-record'.format(item)) as c:
            c.argument('record_set_name', options_list=['--record-set-name', '-n'], help='The name of the record set relative to the zone.')
            c.argument('keep_empty_record_set', action='store_true', help='Keep the empty record set if the last record is removed.')

    with self.argument_context('network dns record-set cname set-record') as c:
        c.argument('record_set_name', options_list=['--record-set-name', '-n'], help='The name of the record set relative to the zone. Creates a new record set if one does not exist.')

    with self.argument_context('network dns record-set soa') as c:
        c.argument('relative_record_set_name', ignore_type, default='@')

    with self.argument_context('network dns record-set a') as c:
        c.argument('ipv4_address', options_list=['--ipv4-address', '-a'], help='IPV4 address in string notation.')

    with self.argument_context('network dns record-set aaaa') as c:
        c.argument('ipv6_address', options_list=['--ipv6-address', '-a'], help='IPV6 address in string notation.')

    with self.argument_context('network dns record-set caa') as c:
        c.argument('value', help='Value of the CAA record.')
        c.argument('flags', help='Integer flags for the record.', type=int)
        c.argument('tag', help='Record tag')

    with self.argument_context('network dns record-set cname') as c:
        c.argument('cname', options_list=['--cname', '-c'], help='Canonical name.')

    with self.argument_context('network dns record-set mx') as c:
        c.argument('exchange', options_list=['--exchange', '-e'], help='Exchange metric.')
        c.argument('preference', options_list=['--preference', '-p'], help='Preference metric.')

    with self.argument_context('network dns record-set ns') as c:
        c.argument('dname', options_list=['--nsdname', '-d'], help='Name server domain name.')

    with self.argument_context('network dns record-set ns add-record') as c:
        c.argument('subscription_id', options_list=['--subscriptionid', '-s'], help='Subscription id to add name server record')
        c.ignore('_subscription')

    with self.argument_context('network dns record-set ptr') as c:
        c.argument('dname', options_list=['--ptrdname', '-d'], help='PTR target domain name.')

    with self.argument_context('network dns record-set soa') as c:
        c.argument('host', options_list=['--host', '-t'], help='Host name.')
        c.argument('email', options_list=['--email', '-e'], help='Email address.')
        c.argument('expire_time', options_list=['--expire-time', '-x'], help='Expire time (seconds).')
        c.argument('minimum_ttl', options_list=['--minimum-ttl', '-m'], help='Minimum TTL (time-to-live, seconds).')
        c.argument('refresh_time', options_list=['--refresh-time', '-f'], help='Refresh value (seconds).')
        c.argument('retry_time', options_list=['--retry-time', '-r'], help='Retry time (seconds).')
        c.argument('serial_number', options_list=['--serial-number', '-s'], help='Serial number.')

    with self.argument_context('network dns record-set srv') as c:
        c.argument('priority', options_list=['--priority', '-p'], help='Priority metric.')
        c.argument('weight', options_list=['--weight', '-w'], help='Weight metric.')
        c.argument('port', options_list=['--port', '-r'], help='Service port.')
        c.argument('target', options_list=['--target', '-t'], help='Target domain name.')

    with self.argument_context('network dns record-set txt') as c:
        c.argument('value', options_list=['--value', '-v'], nargs='+', help='Space-separated list of text values which will be concatenated together.')

    # endregion

    # region ExpressRoutes
    device_path_values = ['primary', 'secondary']
    er_circuit_name_type = CLIArgumentType(options_list='--circuit-name', metavar='NAME', help='ExpressRoute circuit name.', id_part='name', completer=get_resource_name_completion_list('Microsoft.Network/expressRouteCircuits'))
    er_gateway_name_type = CLIArgumentType(options_list='--gateway-name', metavar='NAME', help='ExpressRoute gateway name.', id_part='name', completer=get_resource_name_completion_list('Microsoft.Network/expressRouteGateways'))
    er_port_name_type = CLIArgumentType(options_list='--port-name', metavar='NAME', help='ExpressRoute port name.', id_part='name', completer=get_resource_name_completion_list('Microsoft.Network/expressRoutePorts'))
    er_bandwidth_type = CLIArgumentType(options_list='--bandwidth', nargs='+')
    sku_family_type = CLIArgumentType(help='Chosen SKU family of ExpressRoute circuit.', arg_type=get_enum_type(ExpressRouteCircuitSkuFamily), default=ExpressRouteCircuitSkuFamily.metered_data.value)
    sku_tier_type = CLIArgumentType(help='SKU Tier of ExpressRoute circuit.', arg_type=get_enum_type(ExpressRouteCircuitSkuTier), default=ExpressRouteCircuitSkuTier.standard.value)
    with self.argument_context('network express-route') as c:
        c.argument('circuit_name', circuit_name_type, options_list=['--name', '-n'])
        c.argument('sku_family', sku_family_type)
        c.argument('sku_tier', sku_tier_type)
        c.argument('bandwidth_in_mbps', er_bandwidth_type, validator=bandwidth_validator_factory(mbps=True), help='Bandwidth of the circuit. Usage: INT {Mbps,Gbps}. Defaults to Mbps')
        c.argument('service_provider_name', options_list='--provider', help="Name of the ExpressRoute Service Provider.")
        c.argument('peering_location', help="Name of the peering location.")
        c.argument('device_path', options_list='--path', arg_type=get_enum_type(device_path_values))
        c.argument('vlan_id', type=int)
        c.argument('allow_global_reach', arg_type=get_three_state_flag(), min_api='2018-07-01', help='Enable global reach on the circuit.')
        c.argument('express_route_port', help='Name or ID of an ExpressRoute port.', min_api='2018-08-01', validator=validate_express_route_port)
        c.argument('allow_classic_operations', arg_type=get_three_state_flag(), min_api='2017-10-01', help='Allow classic operations.')

    with self.argument_context('network express-route update') as c:
        c.argument('sku_family', sku_family_type, default=None)
        c.argument('sku_tier', sku_tier_type, default=None)

    with self.argument_context('network express-route auth') as c:
        c.argument('circuit_name', circuit_name_type)
        c.argument('authorization_name', name_arg_type, id_part='child_name_1', help='Authorization name')

    with self.argument_context('network express-route auth create') as c:
        c.argument('authorization_parameters', ignore_type)
        c.extra('cmd')

    with self.argument_context('network express-route peering') as c:
        # Using six.integer_types so we get int for Py3 and long for Py2
        c.argument('peer_asn', help='Autonomous system number of the customer/connectivity provider.', type=six.integer_types[-1])
        c.argument('vlan_id', help='Identifier used to identify the customer.')
        c.argument('circuit_name', circuit_name_type)
        c.argument('peering_name', name_arg_type, id_part='child_name_1')
        c.argument('peering_type', validator=validate_peering_type, arg_type=get_enum_type(ExpressRoutePeeringType), help='BGP peering type for the circuit.')
        c.argument('sku_family', arg_type=get_enum_type(ExpressRouteCircuitSkuFamily))
        c.argument('sku_tier', arg_type=get_enum_type(ExpressRouteCircuitSkuTier))
        c.argument('primary_peer_address_prefix', options_list=['--primary-peer-subnet'], help='/30 subnet used to configure IP addresses for primary interface.')
        c.argument('secondary_peer_address_prefix', options_list=['--secondary-peer-subnet'], help='/30 subnet used to configure IP addresses for secondary interface.')
        c.argument('shared_key', help='Key for generating an MD5 for the BGP session.')

    with self.argument_context('network express-route peering', arg_group='Microsoft Peering') as c:
        c.argument('ip_version', min_api='2017-06-01', help='The IP version to update Microsoft Peering settings for.', arg_type=get_enum_type(['IPv4', 'IPv6']))
        c.argument('advertised_public_prefixes', nargs='+', help='Space-separated list of prefixes to be advertised through the BGP peering.')
        c.argument('customer_asn', help='Autonomous system number of the customer.')
        c.argument('routing_registry_name', arg_type=get_enum_type(routing_registry_values), help='Internet Routing Registry / Regional Internet Registry')
        c.argument('route_filter', min_api='2016-12-01', help='Name or ID of a route filter to apply to the peering settings.', validator=validate_route_filter)
        c.argument('legacy_mode', min_api='2017-10-01', type=int, help='Integer representing the legacy mode of the peering.')

    with self.argument_context('network express-route peering connection') as c:
        c.argument('authorization_key', help='The authorization key used when the peer circuit is in another subscription.')
        c.argument('address_prefix', help='/29 IP address space to carve out customer addresses for tunnels.')
        c.argument('peering_name', options_list=['--peering-name'], help='Name of BGP peering (i.e. AzurePrivatePeering).', id_part='child_name_1')
        c.argument('connection_name', options_list=['--name', '-n'], help='Name of the peering connection.', id_part='child_name_2')
        c.argument('peer_circuit', help='Name or ID of the peer ExpressRoute circuit.', validator=validate_er_peer_circuit)

    with self.argument_context('network express-route peering peer-connection') as c:
        c.argument('circuit_name', circuit_name_type, id_part=None)
        c.argument('peering_name', options_list=['--peering-name'], help='Name of BGP peering (i.e. AzurePrivatePeering).', id_part=None)
        c.argument('connection_name', options_list=['--name', '-n'], help='Name of the peering peer-connection.', id_part=None)
    # endregion

    # region ExpressRoute Gateways
    with self.argument_context('network express-route gateway', min_api='2018-08-01') as c:
        c.argument('express_route_gateway_name', er_gateway_name_type, options_list=['--name', '-n'])
        c.argument('min_val', help='Minimum number of scale units deployed for gateway.', type=int, arg_group='Autoscale')
        c.argument('max_val', help='Maximum number of scale units deployed for gateway.', type=int, arg_group='Autoscale')
        c.argument('virtual_hub', help='Name or ID of the virtual hub to associate with the gateway.', validator=validate_virtual_hub)

    with self.argument_context('network express-route gateway connection', min_api='2018-08-01') as c:
        c.argument('express_route_gateway_name', er_gateway_name_type)
        c.argument('connection_name', options_list=['--name', '-n'], help='ExpressRoute connection name.', id_part='child_name_1')
        c.argument('routing_weight', help='Routing weight associated with the connection.', type=int)
        c.argument('authorization_key', help='Authorization key to establish the connection.')

    with self.argument_context('network express-route gateway connection', arg_group='Peering', min_api='2018-08-01') as c:
        c.argument('peering', help='Name or ID of an ExpressRoute peering.', validator=validate_express_route_peering)
        c.argument('circuit_name', er_circuit_name_type, id_part=None)

    with self.argument_context('network express-route gateway connection list', min_api='2018-08-01') as c:
        c.argument('express_route_gateway_name', er_gateway_name_type, id_part=None)

    with self.argument_context('network express-route port', min_api='2018-08-01') as c:
        c.argument('express_route_port_name', er_port_name_type, options_list=['--name', '-n'])
        c.argument('encapsulation', arg_type=get_enum_type(ExpressRoutePortsEncapsulation), help='Encapsulation method on physical ports.')
        c.argument('bandwidth_in_gbps', er_bandwidth_type, validator=bandwidth_validator_factory(mbps=False),
                   help='Bandwidth of the circuit. Usage: INT {Mbps,Gbps}. Defaults to Gbps')
        c.argument('peering_location', help='The name of the peering location that the port is mapped to physically.')

    with self.argument_context('network express-route port link', min_api='2018-08-01') as c:
        c.argument('express_route_port_name', er_port_name_type)
        c.argument('link_name', options_list=['--name', '-n'], id_part='child_name_1')

    with self.argument_context('network express-route port link list', min_api='2018-08-01') as c:
        c.argument('express_route_port_name', er_port_name_type, id_part=None)

    with self.argument_context('network express-route port location', min_api='2018-08-01') as c:
        c.argument('location_name', options_list=['--location', '-l'])
    # endregion

    # region PrivateEndpoint
    private_endpoint_name = CLIArgumentType(options_list='--endpoint-name', id_part='name', help='Name of the private endpoint.', completer=get_resource_name_completion_list('Microsoft.Network/interfaceEndpoints'))

    with self.argument_context('network private-endpoint') as c:
        c.argument('private_endpoint_name', private_endpoint_name, options_list=['--name', '-n'])
        c.argument('location', get_location_type(self.cli_ctx), validator=get_default_location_from_resource_group)
        c.argument('subnet', validator=get_subnet_validator(), help='Name or ID of an existing subnet. If name is specified, also specify --vnet-name.', id_part=None)
        c.argument('virtual_network_name', help='The virtual network (VNet) associated with the subnet (Omit if supplying a subnet id).', metavar='', id_part=None)
        c.argument('private_connection_resource_id', help='The resource id of which private enpoint connect to')
        c.argument('group_ids', nargs='+', help='The ID(s) of the group(s) obtained from the remote resource that this private endpoint should connect to. You can use "az network private-resource show to obtain the list of group ids."')
        c.argument('request_message', help='A message passed to the owner of the remote resource with this connection request. Restricted to 140 chars.')
        c.argument('manual_request', help='Use manual request to establish the connection', arg_type=get_three_state_flag())
        c.argument('connection_name', help='Name of the private link service connection.')
        c.ignore('expand')
    # endregion

    # region PrivateLinkService
    service_name = CLIArgumentType(options_list='--service-name', id_part='name', help='Name of the private link service.', completer=get_resource_name_completion_list('Microsoft.Network/privateLinkServices'))
    with self.argument_context('network private-link-service') as c:
        c.argument('service_name', service_name, options_list=['--name', '-n'])
        c.argument('auto_approval', nargs='+', help='Space-separated list of subscription IDs to auto-approve.', validator=get_subscription_list_validator('auto_approval', 'PrivateLinkServicePropertiesAutoApproval'))
        c.argument('visibility', nargs='+', help='Space-separated list of subscription IDs for which the private link service is visible.', validator=get_subscription_list_validator('visibility', 'PrivateLinkServicePropertiesVisibility'))
        c.argument('frontend_ip_configurations', nargs='+', options_list='--lb-frontend-ip-configs', help='Space-separated list of names or IDs of load balancer frontend IP configurations to link to. If names are used, also supply `--lb-name`.', validator=validate_frontend_ip_configs)
        c.argument('load_balancer_name', options_list='--lb-name', help='Name of the load balancer to retrieve frontend IP configs from. Ignored if a frontend IP configuration ID is supplied.')
        c.argument('private_endpoint_connections', nargs='+', help='Space-separated list of private endpoint connections.')
        c.argument('fqdns', nargs='+', help='Space-separated list of FQDNs.')
        c.argument('location', get_location_type(self.cli_ctx), validator=get_default_location_from_resource_group)

    with self.argument_context('network private-link-service', arg_group='IP Configuration') as c:
        c.argument('private_ip_address', private_ip_address_type)
        c.argument('private_ip_allocation_method', help='Private IP address allocation method', arg_type=get_enum_type(IPAllocationMethod))
        c.argument('private_ip_address_version', help='IP version of the private IP address.', arg_type=get_enum_type(IPVersion, 'ipv4'))
        c.argument('public_ip_address', help='Name or ID of the a public IP address to use.', completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'), validator=get_public_ip_validator())
        c.argument('subnet', help='Name or ID of subnet to use. If name provided, also supply `--vnet-name`.', validator=get_subnet_validator())
        c.argument('virtual_network_name', options_list='--vnet-name')

    with self.argument_context('network private-link-service connection') as c:
        c.argument('service_name', service_name, id_part=None)
        c.argument('pe_connection_name', help='Name of the private endpoint connection. List them by using "az network private-link-service show".', options_list=['--name', '-n'])
        c.argument('action_required', help='A message indicating if changes on the service provider require any updates on the consumer.')
        c.argument('description', help='The reason for approval/rejection of the connection.')
        c.argument('connection_status', help='Indicates whether the connection has been Approved/Rejected/Removed by the owner of the service.', arg_type=get_enum_type(['Approved', 'Rejected', 'Removed']))

    with self.argument_context('network private-link-service ip-configs') as c:
        c.argument('service_name', service_name)
        c.argument('ip_config_name', help='Name of the ip configuration.', options_list=['--name', '-n'])
        c.argument('virtual_network_name', id_part=None)
    # endregion

    # region LoadBalancers
    lb_subresources = [
        {'name': 'address-pool', 'display': 'backend address pool', 'ref': 'backend_address_pools'},
        {'name': 'frontend-ip', 'display': 'frontend IP configuration', 'ref': 'frontend_ip_configurations'},
        {'name': 'inbound-nat-rule', 'display': 'inbound NAT rule', 'ref': 'inbound_nat_rules'},
        {'name': 'inbound-nat-pool', 'display': 'inbound NAT pool', 'ref': 'inbound_nat_pools'},
        {'name': 'rule', 'display': 'load balancing rule', 'ref': 'load_balancing_rules'},
        {'name': 'probe', 'display': 'probe', 'ref': 'probes'},
        {'name': 'outbound-rule', 'display': 'outbound rule', 'ref': 'outbound_rules'},
    ]
    for item in lb_subresources:
        with self.argument_context('network lb {}'.format(item['name'])) as c:
            c.argument('item_name', options_list=['--name', '-n'], help='The name of the {}'.format(item['display']), completer=get_lb_subresource_completion_list(item['ref']), id_part='child_name_1')
            c.argument('resource_name', options_list='--lb-name', help='The name of the load balancer.', completer=get_resource_name_completion_list('Microsoft.Network/loadBalancers'))
            c.argument('load_balancer_name', load_balancer_name_type)

    with self.argument_context('network lb') as c:
        c.argument('load_balancer_name', load_balancer_name_type, options_list=['--name', '-n'])
        c.argument('frontend_port', help='Port number')
        c.argument('frontend_port_range_start', help='Port number')
        c.argument('frontend_port_range_end', help='Port number')
        c.argument('backend_port', help='Port number')
        c.argument('frontend_ip_name', help='The name of the frontend IP configuration.', completer=get_lb_subresource_completion_list('frontend_ip_configurations'))
        c.argument('floating_ip', help='Enable floating IP.', arg_type=get_three_state_flag())
        c.argument('idle_timeout', help='Idle timeout in minutes.', type=int)
        c.argument('protocol', help='Network transport protocol.', arg_type=get_enum_type(TransportProtocol))
        c.argument('private_ip_address_version', min_api='2019-04-01', help='The private IP address version to use.', default=IPVersion.ipv4.value if IPVersion else '')
        for item in ['backend_pool_name', 'backend_address_pool_name']:
            c.argument(item, options_list='--backend-pool-name', help='The name of the backend address pool.', completer=get_lb_subresource_completion_list('backend_address_pools'))

    with self.argument_context('network lb create') as c:
        c.argument('frontend_ip_zone', zone_type, min_api='2017-06-01', options_list=['--frontend-ip-zone'], help='used to create internal facing Load balancer')
        c.argument('validate', help='Generate and validate the ARM template without creating any resources.', action='store_true')
        c.argument('sku', min_api='2017-08-01', help='Load balancer SKU', arg_type=get_enum_type(LoadBalancerSkuName, default='basic'))

    with self.argument_context('network lb create', arg_group='Public IP') as c:
        public_ip_help = get_folded_parameter_help_string('public IP address', allow_none=True, allow_new=True)
        c.argument('public_ip_address', help=public_ip_help, completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'))
        c.argument('public_ip_address_allocation', help='IP allocation method.', arg_type=get_enum_type(IPAllocationMethod))
        c.argument('public_ip_dns_name', help='Globally unique DNS name for a new public IP.')
        c.argument('public_ip_zone', zone_type, min_api='2017-06-01', options_list=['--public-ip-zone'], help='used to created a new public ip for the load balancer, a.k.a public facing Load balancer')
        c.ignore('public_ip_address_type')

    with self.argument_context('network lb create', arg_group='Subnet') as c:
        subnet_help = get_folded_parameter_help_string('subnet', other_required_option='--vnet-name', allow_new=True, allow_none=True, default_none=True)
        c.argument('subnet', help=subnet_help, completer=subnet_completion_list)
        c.argument('subnet_address_prefix', help='The CIDR address prefix to use when creating a new subnet.')
        c.argument('virtual_network_name', virtual_network_name_type)
        c.argument('vnet_address_prefix', help='The CIDR address prefix to use when creating a new VNet.')
        c.ignore('vnet_type', 'subnet_type')

    with self.argument_context('network lb frontend-ip') as c:
        c.argument('zone', zone_type, min_api='2017-06-01')

    for item in ['create', 'update']:
        with self.argument_context('network lb frontend-ip {}'.format(item)) as c:
            c.argument('public_ip_address', help='Name or ID of the existing public IP to associate with the configuration.')
            c.argument('subnet', help='Name or ID of an existing subnet. If name is specified, also specify --vnet-name.')
            c.argument('virtual_network_name', virtual_network_name_type, help='The virtual network (VNet) associated with the subnet (Omit if supplying a subnet id).', id_part=None, metavar='')
            c.ignore('private_ip_address_allocation')

    with self.argument_context('network lb frontend-ip create') as c:
        c.argument('private_ip_address', help='Static private IP address to associate with the configuration.')

    with self.argument_context('network lb frontend-ip update') as c:
        c.argument('private_ip_address', help='Static private IP address to associate with the configuration. Use "" to remove the static address and use a dynamic address instead.')

    with self.argument_context('network lb probe') as c:
        c.argument('interval', help='Probing time interval in seconds.')
        c.argument('path', help='The endpoint to interrogate (http only).')
        c.argument('port', help='The port to interrogate.')
        c.argument('protocol', help='The protocol to probe.', arg_type=get_enum_type(ProbeProtocol))
        c.argument('threshold', help='The number of consecutive probe failures before an instance is deemed unhealthy.')

    with self.argument_context('network lb outbound-rule') as c:
        c.argument('backend_address_pool', options_list='--address-pool', help='Name or ID of the backend address pool.')
        c.argument('frontend_ip_configurations', options_list='--frontend-ip-configs', help='Space-separated list of frontend IP configuration names or IDs.', nargs='+')
        c.argument('protocol', arg_type=get_enum_type(TransportProtocol), help='Network transport protocol.')
        c.argument('outbound_ports', type=int, help='The number of outbound ports to be used for NAT.')

    with self.argument_context('network lb rule') as c:
        c.argument('load_distribution', help='Affinity rule settings.', arg_type=get_enum_type(LoadDistribution))
        c.argument('probe_name', help='Name of an existing probe to associate with this rule.')
        c.argument('disable_outbound_snat', min_api='2018-08-01', help='Configures SNAT for the VMs in the backend pool to use the publicIP address specified in the frontend of the load balancing rule.', arg_type=get_three_state_flag())
    # endregion

    # region LocalGateway
    with self.argument_context('network local-gateway') as c:
        c.argument('local_network_gateway_name', name_arg_type, help='Name of the local network gateway.', completer=get_resource_name_completion_list('Microsoft.Network/localNetworkGateways'), id_part='name')
        c.argument('local_address_prefix', nargs='+', options_list='--local-address-prefixes', help='List of CIDR block prefixes representing the address space of the OnPremise VPN\'s subnet.')
        c.argument('gateway_ip_address', help='Gateway\'s public IP address. (e.g. 10.1.1.1).')
        c.argument('bgp_peering_address', arg_group='BGP Peering', help='IP address from the OnPremise VPN\'s subnet to use for BGP peering.')

    with self.argument_context('network local-gateway create') as c:
        c.ignore('use_bgp_settings')

    for item in ['local-gateway', 'vnet-gateway']:
        with self.argument_context('network {}'.format(item)) as c:
            c.argument('asn', arg_group='BGP Peering', help='Autonomous System Number to use for the BGP settings.')
            c.argument('peer_weight', arg_group='BGP Peering', help='Weight (0-100) added to routes learned through BGP peering.')
    # endregion

    # region NetworkInterfaces (NIC)
    with self.argument_context('network nic') as c:
        c.argument('enable_accelerated_networking', min_api='2016-09-01', options_list=['--accelerated-networking'], help='Enable accelerated networking.', arg_type=get_three_state_flag())
        c.argument('network_interface_name', nic_type, options_list=['--name', '-n'])
        c.argument('internal_dns_name_label', options_list='--internal-dns-name', help='The internal DNS name label.', arg_group='DNS')
        c.argument('dns_servers', help='Space-separated list of DNS server IP addresses.', nargs='+', arg_group='DNS')
        c.argument('enable_ip_forwarding', options_list='--ip-forwarding', help='Enable IP forwarding.', arg_type=get_three_state_flag())

    with self.argument_context('network nic create') as c:
        c.argument('private_ip_address_version', min_api='2016-09-01', help='The private IP address version to use.', default=IPVersion.ipv4.value if IPVersion else '')
        c.argument('network_interface_name', nic_type, options_list=['--name', '-n'], id_part=None)

        public_ip_help = get_folded_parameter_help_string('public IP address', allow_none=True, default_none=True)
        c.argument('public_ip_address', help=public_ip_help, completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'))

        nsg_help = get_folded_parameter_help_string('network security group', allow_none=True, default_none=True)
        c.argument('network_security_group', help=nsg_help, completer=get_resource_name_completion_list('Microsoft.Network/networkSecurityGroups'))

        subnet_help = get_folded_parameter_help_string('subnet', other_required_option='--vnet-name')
        c.argument('subnet', help=subnet_help, completer=subnet_completion_list)

    with self.argument_context('network nic update') as c:
        c.argument('network_security_group', help='Name or ID of the associated network security group.', validator=get_nsg_validator(), completer=get_resource_name_completion_list('Microsoft.Network/networkSecurityGroups'))
        c.argument('dns_servers', help='Space-separated list of DNS server IP addresses. Use "" to revert to default Azure servers.', nargs='+', arg_group='DNS')

    for item in ['create', 'ip-config update', 'ip-config create']:
        with self.argument_context('network nic {}'.format(item)) as c:
            c.argument('application_security_groups', min_api='2017-09-01', help='Space-separated list of application security groups.', nargs='+', validator=get_asg_validator(self, 'application_security_groups'))

        with self.argument_context('network nic {}'.format(item), arg_group='Load Balancer') as c:
            c.extra('load_balancer_name', options_list='--lb-name', completer=get_resource_name_completion_list('Microsoft.Network/loadBalancers'), help='The name of the load balancer to use when adding NAT rules or address pools by name (ignored when IDs are specified).')
            c.argument('load_balancer_backend_address_pool_ids', options_list='--lb-address-pools', nargs='+', validator=validate_address_pool_id_list, help='Space-separated list of names or IDs of load balancer address pools to associate with the NIC. If names are used, --lb-name must be specified.', completer=get_lb_subresource_completion_list('backendAddressPools'))
            c.argument('load_balancer_inbound_nat_rule_ids', options_list='--lb-inbound-nat-rules', nargs='+', validator=validate_inbound_nat_rule_id_list, help='Space-separated list of names or IDs of load balancer inbound NAT rules to associate with the NIC. If names are used, --lb-name must be specified.', completer=get_lb_subresource_completion_list('inboundNatRules'))

        with self.argument_context('network nic {}'.format(item), arg_group='Application Gateway') as c:
            c.argument('app_gateway_backend_address_pools', options_list='--app-gateway-address-pools', nargs='+', help='Space-separated list of names or IDs of application gateway backend address pools to associate with the NIC. If names are used, --gateway-name must be specified.', validator=validate_ag_address_pools, completer=get_ag_subresource_completion_list('backendAddressPools'))
            c.extra('application_gateway_name', app_gateway_name_type, help='The name of the application gateway to use when adding address pools by name (ignored when IDs are specified).')

    with self.argument_context('network nic ip-config') as c:
        c.argument('network_interface_name', options_list='--nic-name', metavar='NIC_NAME', help='The network interface (NIC).', id_part='name', completer=get_resource_name_completion_list('Microsoft.Network/networkInterfaces'))
        c.argument('ip_config_name', options_list=['--name', '-n'], metavar='IP_CONFIG_NAME', help='The name of the IP configuration.', id_part='child_name_1')
        c.argument('resource_name', options_list='--nic-name', metavar='NIC_NAME', help='The network interface (NIC).', id_part='name', completer=get_resource_name_completion_list('Microsoft.Network/networkInterfaces'))
        c.argument('item_name', options_list=['--name', '-n'], metavar='IP_CONFIG_NAME', help='The name of the IP configuration.', id_part='child_name_1')
        c.argument('subnet', validator=get_subnet_validator(), help='Name or ID of an existing subnet. If name is specified, also specify --vnet-name.')
        c.argument('virtual_network_name', help='The virtual network (VNet) associated with the subnet (Omit if supplying a subnet id).', id_part=None, metavar='')
        c.argument('public_ip_address', help='Name or ID of the public IP to use.', validator=get_public_ip_validator())
        c.argument('make_primary', action='store_true', help='Set to make this configuration the primary one for the NIC.')
        c.argument('private_ip_address', private_ip_address_type, help='Static IP address to use or "" to use a dynamic address.')

    with self.argument_context('network nic ip-config address-pool') as c:
        c.argument('load_balancer_name', options_list='--lb-name', help='The name of the load balancer containing the address pool (Omit if suppying an address pool ID).', completer=get_resource_name_completion_list('Microsoft.Network/loadBalancers'))
        c.argument('application_gateway_name', app_gateway_name_type, help='The name of an application gateway containing the address pool (Omit if suppying an address pool ID).', id_part=None)
        c.argument('backend_address_pool', options_list='--address-pool', help='The name or ID of an existing backend address pool.', validator=validate_address_pool_name_or_id)

    with self.argument_context('network nic ip-config inbound-nat-rule') as c:
        c.argument('load_balancer_name', options_list='--lb-name', help='The name of the load balancer associated with the NAT rule (Omit if suppying a NAT rule ID).', completer=get_resource_name_completion_list('Microsoft.Network/loadBalancers'))
        c.argument('inbound_nat_rule', options_list='--inbound-nat-rule', help='The name or ID of an existing inbound NAT rule.', validator=validate_inbound_nat_rule_name_or_id)

    for item in ['address-pool', 'inbound-nat-rule']:
        with self.argument_context('network nic ip-config {}'.format(item)) as c:
            c.argument('ip_config_name', options_list=['--ip-config-name', '-n'], metavar='IP_CONFIG_NAME', help='The name of the IP configuration.', id_part=None)
            c.argument('network_interface_name', nic_type, id_part=None)

    # endregion

    # region NetworkSecurityGroups
    with self.argument_context('network nsg') as c:
        c.argument('network_security_group_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/networkSecurityGroups'), id_part='name')

    with self.argument_context('network nsg create') as c:
        c.argument('name', name_arg_type)

    with self.argument_context('network nsg rule') as c:
        c.argument('security_rule_name', name_arg_type, id_part='child_name_1', help='Name of the network security group rule')
        c.argument('network_security_group_name', options_list='--nsg-name', metavar='NSGNAME', help='Name of the network security group', id_part='name')
        c.argument('include_default', help='Include default security rules in the output.')

    with self.argument_context('network nsg rule create') as c:
        c.argument('network_security_group_name', options_list='--nsg-name', metavar='NSGNAME', help='Name of the network security group', id_part=None)

    for item in ['create', 'update']:
        with self.argument_context('network nsg rule {}'.format(item)) as c:
            c.argument('priority', help='Rule priority, between 100 (highest priority) and 4096 (lowest priority). Must be unique for each rule in the collection.', type=int)
            c.argument('description', help='Rule description')
            c.argument('access', help=None, arg_type=get_enum_type(SecurityRuleAccess), default=SecurityRuleAccess.allow.value if item == 'create' else None)
            c.argument('protocol', help='Network protocol this rule applies to.', arg_type=get_enum_type(SecurityRuleProtocol), default=SecurityRuleProtocol.asterisk.value if item == 'create' else None)
            c.argument('direction', help=None, arg_type=get_enum_type(SecurityRuleDirection), default=SecurityRuleDirection.inbound.value if item == 'create' else None)

        with self.argument_context('network nsg rule {}'.format(item), min_api='2017-06-01') as c:
            c.argument('source_port_ranges', nargs='+', help="Space-separated list of ports or port ranges between 0-65535. Use '*' to match all ports.", arg_group='Source')
            c.argument('source_address_prefixes', nargs='+', help="Space-separated list of CIDR prefixes or IP ranges. Alternatively, specify ONE of 'VirtualNetwork', 'AzureLoadBalancer', 'Internet' or '*' to match all IPs.", arg_group='Source')
            c.argument('destination_port_ranges', nargs='+', help="Space-separated list of ports or port ranges between 0-65535. Use '*' to match all ports.", arg_group='Destination')
            c.argument('destination_address_prefixes', nargs='+', help="Space-separated list of CIDR prefixes or IP ranges. Alternatively, specify ONE of 'VirtualNetwork', 'AzureLoadBalancer', 'Internet' or '*' to match all IPs.", arg_group='Destination')

        with self.argument_context('network nsg rule {}'.format(item), max_api='2017-03-01') as c:
            c.argument('source_port_range', help="Port or port range between 0-65535. Use '*' to match all ports.", arg_group='Source')
            c.argument('source_address_prefix', help="CIDR prefix or IP range. Use '*' to match all IPs. Can also use 'VirtualNetwork', 'AzureLoadBalancer', and 'Internet'.", arg_group='Source')
            c.argument('destination_port_range', help="Port or port range between 0-65535. Use '*' to match all ports.", arg_group='Destination')
            c.argument('destination_address_prefix', help="CIDR prefix or IP range. Use '*' to match all IPs. Can also use 'VirtualNetwork', 'AzureLoadBalancer', and 'Internet'.", arg_group='Destination')

        with self.argument_context('network nsg rule {}'.format(item), min_api='2017-09-01') as c:
            c.argument('source_asgs', nargs='+', help="Space-separated list of application security group names or IDs. Limited by backend server, temporarily this argument only supports one application security group name or ID", arg_group='Source', validator=get_asg_validator(self, 'source_asgs'))
            c.argument('destination_asgs', nargs='+', help="Space-separated list of application security group names or IDs. Limited by backend server, temporarily this argument only supports one application security group name or ID", arg_group='Destination', validator=get_asg_validator(self, 'destination_asgs'))

    # endregion

    # region NetworkWatchers
    with self.argument_context('network watcher') as c:
        c.argument('network_watcher_name', name_arg_type, help='Name of the Network Watcher.')
        c.argument('location', validator=None)
        c.ignore('watcher_rg')
        c.ignore('watcher_name')

    with self.argument_context('network watcher connection-monitor') as c:
        c.argument('network_watcher_name', arg_type=ignore_type, options_list=['--__NETWORK_WATCHER_NAME'])
        c.argument('connection_monitor_name', name_arg_type, help='Connection monitor name.')

    with self.argument_context('network watcher connection-monitor create') as c:
        c.argument('monitoring_interval', help='Monitoring interval in seconds.', type=int)
        c.argument('do_not_start', action='store_true', help='Create the connection monitor but do not start it immediately.')
        c.argument('source_resource', help='Name or ID of the resource from which to originate traffic.')
        c.argument('source_port', help='Port number from which to originate traffic.')
        c.ignore('location')

    with self.argument_context('network watcher connection-monitor', arg_group='Destination') as c:
        c.argument('dest_resource', help='Name of ID of the resource to receive traffic.')
        c.argument('dest_port', help='Port number on which to receive traffic.')
        c.argument('dest_address', help='The IP address or URI at which to receive traffic.')

    nw_validator = get_network_watcher_from_location(remove=True, watcher_name='network_watcher_name', rg_name='resource_group_name')
    for scope in ['list', 'show', 'start', 'stop', 'delete', 'query']:
        with self.argument_context('network watcher connection-monitor {}'.format(scope)) as c:
            c.extra('location', get_location_type(self.cli_ctx), required=True)
            c.argument('resource_group_name', arg_type=ignore_type, validator=nw_validator)

    with self.argument_context('network watcher configure') as c:
        c.argument('locations', get_location_type(self.cli_ctx), options_list=['--locations', '-l'], nargs='+')
        c.argument('enabled', arg_type=get_three_state_flag())

    with self.argument_context('network watcher show-topology') as c:
        c.extra('location')

    with self.argument_context('network watcher show-topology', arg_group='Target') as c:
        c.ignore('network_watcher_name', 'resource_group_name')
        c.argument('target_resource_group_name', options_list=['--resource-group', '-g'], completer=get_resource_group_completion_list)
        c.argument('target_vnet', options_list=['--vnet'], help='Name or ID of the virtual network to target.')
        c.argument('target_subnet', options_list=['--subnet'], help='Name or ID of the subnet to target. If name is used, --vnet NAME must also be supplied.')

    with self.argument_context('network watcher create') as c:
        c.argument('location', validator=get_default_location_from_resource_group)

    for item in ['test-ip-flow', 'show-next-hop', 'show-security-group-view', 'packet-capture create']:
        with self.argument_context('network watcher {}'.format(item)) as c:
            c.argument('watcher_name', ignore_type, validator=get_network_watcher_from_vm)
            c.ignore('location')
            c.ignore('watcher_rg')
            c.argument('vm', help='Name or ID of the VM to target. If the name of the VM is provided, the --resource-group is required.')
            c.argument('resource_group_name', help='Name of the resource group the target VM is in.')
            c.argument('nic', help='Name or ID of the NIC resource to test. If the VM has multiple NICs and IP forwarding is enabled on any of them, this parameter is required.')

    with self.argument_context('network watcher test-connectivity') as c:
        c.argument('source_port', type=int)
        c.argument('dest_resource', arg_group='Destination')
        c.argument('dest_address', arg_group='Destination')
        c.argument('dest_port', type=int, arg_group='Destination')
        c.argument('protocol', arg_type=get_enum_type(Protocol), help='Protocol to test on.')

    with self.argument_context('network watcher test-connectivity', arg_group='HTTP Configuration') as c:
        c.argument('method', arg_type=get_enum_type(HTTPMethod), help='HTTP method to use.')
        c.argument('headers', nargs='+', help='Space-separated list of headers in `KEY=VALUE` format.')
        c.argument('valid_status_codes', nargs='+', type=int, help='Space-separated list of HTTP status codes considered valid.')

    with self.argument_context('network watcher packet-capture') as c:
        c.argument('capture_name', name_arg_type, help='Name of the packet capture session.')
        c.argument('storage_account', arg_group='Storage')
        c.argument('storage_path', arg_group='Storage')
        c.argument('file_path', arg_group='Storage')
        c.argument('filters', type=get_json_object)

    with self.argument_context('network watcher flow-log') as c:
        c.argument('nsg', help='Name or ID of the network security group.')
        c.argument('enabled', arg_type=get_three_state_flag())

    with self.argument_context('network watcher flow-log', arg_group='Format', min_api='2018-10-01') as c:
        c.argument('log_format', options_list='--format', help='File type of the flow log.', arg_type=get_enum_type(FlowLogFormatType))
        c.argument('log_version', help='Version (revision) of the flow log.', type=int)

    with self.argument_context('network watcher flow-log', arg_group='Traffic Analytics', min_api='2018-10-01') as c:
        c.argument('traffic_analytics_interval', type=int, options_list='--interval', help='Interval in minutes at which to conduct flow analytics. Temporarily allowed values are 10 and 60.', min_api='2018-12-01')
        c.argument('traffic_analytics_workspace', options_list='--workspace', help='Name or ID of a Log Analytics workspace.')
        c.argument('traffic_analytics_enabled', options_list='--traffic-analytics', arg_type=get_three_state_flag(), help='Enable traffic analytics. Defaults to true if `--workspace` is provided.')

    for item in ['list', 'stop', 'delete', 'show', 'show-status']:
        with self.argument_context('network watcher packet-capture {}'.format(item)) as c:
            c.extra('location')
            c.argument('location', get_location_type(self.cli_ctx), required=True)
            c.argument('packet_capture_name', name_arg_type)
            c.argument('network_watcher_name', ignore_type, options_list=['--network-watcher-name'], validator=get_network_watcher_from_location(remove=True, rg_name='resource_group_name', watcher_name='network_watcher_name'))
            c.ignore('resource_group_name')

    with self.argument_context('network watcher test-ip-flow') as c:
        c.argument('direction', arg_type=get_enum_type(Direction))
        c.argument('protocol', arg_type=get_enum_type(Protocol))

    with self.argument_context('network watcher show-next-hop') as c:
        c.argument('source_ip', help='Source IPv4 address.')
        c.argument('dest_ip', help='Destination IPv4 address.')

    with self.argument_context('network watcher troubleshooting') as c:
        c.argument('resource', help='Name or ID of the resource to troubleshoot.')
        c.argument('resource_type', help='The resource type', options_list=['--resource-type', '-t'], id_part='resource_type', arg_type=get_enum_type(['vnetGateway', 'vpnConnection']))

    with self.argument_context('network watcher run-configuration-diagnostic', arg_group='Target') as c:
        c.argument('resource', help='Name or ID of the target resource to diagnose. If an ID is given, other resource arguments should not be given.')
        c.argument('resource_type', help='The resource type', options_list=['--resource-type', '-t'], id_part='resource_type', arg_type=get_enum_type(['virtualMachines', 'networkInterfaces', 'applicationGateways']))
        c.argument('parent', help='The parent path. (ex: virtualMachineScaleSets/vmss1)')
        c.argument('resource_group_name')

    with self.argument_context('network watcher run-configuration-diagnostic', arg_group='Query') as c:
        c.argument('queries', help='JSON list of queries to use. Use `@{path}` to load from a file.', type=get_json_object)
        c.argument('direction', arg_type=get_enum_type(Direction), help='Direction of the traffic.')
        c.argument('protocol', arg_type=get_enum_type(Protocol), help='Protocol to be verified on.')
        c.argument('destination', help="Traffic destination. Accepted values are '*', IP address/CIDR, or service tag.")
        c.argument('source', help="Traffic source. Accepted values are '*', IP address/CIDR, or service tag.")
        c.argument('destination_port', options_list='--port', help="Traffic destination port. Accepted values are '*', port number (3389) or port range (80-100).")
    # endregion

    # region NetworkProfile
    network_profile_name = CLIArgumentType(options_list='--profile-name', metavar='NAME', help='The network profile name.', id_part='name', completer=get_resource_name_completion_list('Microsoft.Network/networkProfiles'))

    with self.argument_context('network profile') as c:
        c.argument('network_profile_name', network_profile_name, options_list=['--name', '-n'])
    # endregion

    # region PublicIPAddresses
    with self.argument_context('network public-ip') as c:
        c.argument('public_ip_address_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'), id_part='name', help='The name of the public IP address.')
        c.argument('name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'), help='The name of the public IP address.')
        c.argument('reverse_fqdn', help='Reverse FQDN (fully qualified domain name).')
        c.argument('dns_name', help='Globally unique DNS entry.')
        c.argument('idle_timeout', help='Idle timeout in minutes.')
        c.argument('zone', zone_type, min_api='2017-06-01')
        c.argument('ip_tags', nargs='+', min_api='2017-11-01', help="Space-separated list of IP tags in 'TYPE=VAL' format.", validator=validate_ip_tags)

    with self.argument_context('network public-ip create') as c:
        c.argument('name', completer=None)
        c.ignore('dns_name_type')

    for item in ['create', 'update']:
        with self.argument_context('network public-ip {}'.format(item)) as c:
            c.argument('allocation_method', help='IP address allocation method', arg_type=get_enum_type(IPAllocationMethod))
            c.argument('sku', min_api='2017-08-01', help='Public IP SKU', arg_type=get_enum_type(PublicIPAddressSkuName))
            c.argument('version', min_api='2016-09-01', help='IP address type.', arg_type=get_enum_type(IPVersion, 'ipv4'))

    for scope in ['public-ip', 'lb frontend-ip']:
        with self.argument_context('network {}'.format(scope), min_api='2018-07-01') as c:
            c.argument('public_ip_prefix', help='Name or ID of a public IP prefix.')

    with self.argument_context('network public-ip prefix') as c:
        c.argument('public_ip_prefix_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/publicIPPrefixes'), id_part='name', help='The name of the public IP prefix.')
        c.argument('prefix_length', options_list='--length', help='Length of the prefix (i.e. XX.XX.XX.XX/<Length>)')
        c.argument('zone', zone_type)
    # endregion

    # region RouteFilters
    with self.argument_context('network route-filter') as c:
        c.argument('route_filter_name', name_arg_type, help='Name of the route filter.')
        c.argument('expand', arg_type=get_enum_type(['peerings']))

    with self.argument_context('network route-filter rule') as c:
        c.argument('route_filter_name', options_list=['--filter-name'], help='Name of the route filter.', id_part='name')
        c.argument('rule_name', name_arg_type, help='Name of the route filter rule.', id_part='child_name_1')
        c.argument('access', help='The access type of the rule.', arg_type=get_enum_type(Access))
        c.argument('communities', nargs='+')
    # endregion

    # region RouteTables
    with self.argument_context('network route-table') as c:
        c.argument('route_table_name', name_arg_type, help='Name of the route table.', completer=get_resource_name_completion_list('Microsoft.Network/routeTables'), id_part='name')
        c.argument('disable_bgp_route_propagation', arg_type=get_three_state_flag(), min_api='2017-10-01', help='Disable routes learned by BGP.')

    with self.argument_context('network route-table create') as c:
        c.extra('tags')
        c.extra('location')
        c.extra('cmd')
        c.argument('location', get_location_type(self.cli_ctx))
        c.ignore('parameters')

    with self.argument_context('network route-table route') as c:
        c.argument('route_name', name_arg_type, id_part='child_name_1', help='Route name')
        c.argument('route_table_name', options_list='--route-table-name', help='Route table name')
        c.argument('next_hop_type', help='The type of Azure hop the packet should be sent to.', arg_type=get_enum_type(RouteNextHopType))
        c.argument('next_hop_ip_address', help='The IP address packets should be forwarded to when using the VirtualAppliance hop type.')
        c.argument('address_prefix', help='The destination CIDR to which the route applies.')

    # endregion

    # region ServiceEndpoint
    service_endpoint_policy_name = CLIArgumentType(options_list='--policy-name', id_part='name', help='Name of the service endpoint policy.', completer=get_resource_name_completion_list('Microsoft.Network/serviceEndpointPolicies'))

    with self.argument_context('network service-endpoint policy') as c:
        c.argument('service_endpoint_policy_name', service_endpoint_policy_name, options_list=['--name', '-n'])

    with self.argument_context('network service-endpoint policy show') as c:
        c.ignore('expand')

    with self.argument_context('network service-endpoint policy-definition') as c:
        c.argument('service_endpoint_policy_name', service_endpoint_policy_name)
        c.argument('service_endpoint_policy_definition_name', name_arg_type, help='Name of the service endpoint policy definition', id_part='child_name_1')
        c.argument('description', help='Description of the policy definition.')
        c.argument('service', help='Service name the policy definition applies to.', completer=service_endpoint_completer)
        c.argument('service_resources', help='Space-separated list of service resources the definition applies to.', nargs='+')

    with self.argument_context('network service-endpoint policy-definition list') as c:
        c.argument('service_endpoint_policy_name', service_endpoint_policy_name, id_part=None)
    # endregion

    # region TrafficManagers
    monitor_protocol_type = CLIArgumentType(help='Monitor protocol.', arg_type=get_enum_type(MonitorProtocol, default='http'))
    with self.argument_context('network traffic-manager profile') as c:
        c.argument('traffic_manager_profile_name', name_arg_type, id_part='name', help='Traffic manager profile name', completer=get_resource_name_completion_list('Microsoft.Network/trafficManagerProfiles'))
        c.argument('profile_name', name_arg_type, id_part='name', completer=get_resource_name_completion_list('Microsoft.Network/trafficManagerProfiles'))
        c.argument('profile_status', options_list=['--status'], help='Status of the Traffic Manager profile.', arg_type=get_enum_type(ProfileStatus))
        c.argument('routing_method', help='Routing method.', arg_type=get_enum_type(['Performance', 'Weighted', 'Priority', 'Geographic', 'Multivalue', 'Subnet']))
        c.argument('unique_dns_name', help="Relative DNS name for the traffic manager profile. Resulting FQDN will be `<unique-dns-name>.trafficmanager.net` and must be globally unique.")
        c.argument('ttl', help='DNS config time-to-live in seconds.', type=int)

    with self.argument_context('network traffic-manager profile', arg_group='Monitor Configuration') as c:
        c.argument('monitor_path', help='Path to monitor. Use "" for none.', options_list=['--path', c.deprecate(target='--monitor-path', redirect='--path', hide=True)])
        c.argument('monitor_port', help='Port to monitor.', type=int, options_list=['--port', c.deprecate(target='--monitor-port', redirect='--port', hide=True)])
        c.argument('monitor_protocol', monitor_protocol_type, options_list=['--protocol', c.deprecate(target='--monitor-protocol', redirect='--protocol', hide=True)])
        c.argument('timeout', help='The time in seconds allowed for endpoints to response to a health check.', type=int)
        c.argument('interval', help='The interval in seconds at which health checks are conducted.', type=int)
        c.argument('max_failures', help='The number of consecutive failed health checks tolerated before an endpoint is considered degraded.', type=int)
        c.argument('monitor_custom_headers', options_list='--custom-headers', help='Space-separated list of NAME=VALUE pairs.', nargs='+', validator=validate_custom_headers)
        c.argument('status_code_ranges', help='Space-separated list of status codes in MIN-MAX or VAL format.', nargs='+', validator=validate_status_code_ranges)

    with self.argument_context('network traffic-manager profile update') as c:
        c.argument('monitor_protocol', monitor_protocol_type, default=None)

    with self.argument_context('network traffic-manager profile check-dns') as c:
        c.argument('name', name_arg_type, help='DNS prefix to verify availability for.', required=True)
        c.argument('type', ignore_type, default='Microsoft.Network/trafficManagerProfiles')

    endpoint_types = ['azureEndpoints', 'externalEndpoints', 'nestedEndpoints']
    with self.argument_context('network traffic-manager endpoint') as c:
        c.argument('endpoint_name', name_arg_type, id_part='child_name_1', help='Endpoint name.', completer=tm_endpoint_completion_list)
        c.argument('endpoint_type', options_list=['--type', '-t'], help='Endpoint type.', id_part='child_name_1', arg_type=get_enum_type(endpoint_types))
        c.argument('profile_name', help='Name of parent profile.', completer=get_resource_name_completion_list('Microsoft.Network/trafficManagerProfiles'), id_part='name')
        c.argument('endpoint_location', help="Location of the external or nested endpoints when using the 'Performance' routing method.")
        c.argument('endpoint_monitor_status', help='The monitoring status of the endpoint.')
        c.argument('endpoint_status', arg_type=get_enum_type(['Enabled', 'Disabled']), help="The status of the endpoint. If enabled the endpoint is probed for endpoint health and included in the traffic routing method.")
        c.argument('min_child_endpoints', help="The minimum number of endpoints that must be available in the child profile for the parent profile to be considered available. Only applicable to an endpoint of type 'NestedEndpoints'.")
        c.argument('priority', help="Priority of the endpoint when using the 'Priority' traffic routing method. Values range from 1 to 1000, with lower values representing higher priority.", type=int)
        c.argument('target', help='Fully-qualified DNS name of the endpoint.')
        c.argument('target_resource_id', help="The Azure Resource URI of the endpoint. Not applicable for endpoints of type 'ExternalEndpoints'.")
        c.argument('weight', help="Weight of the endpoint when using the 'Weighted' traffic routing method. Values range from 1 to 1000.", type=int)
        c.argument('geo_mapping', help="Space-separated list of country/region codes mapped to this endpoint when using the 'Geographic' routing method.", nargs='+')
        c.argument('subnets', nargs='+', help='Space-separated list of subnet CIDR prefixes (10.0.0.0/24) or subnet ranges (10.0.0.0-11.0.0.0).', validator=validate_subnet_ranges)
        c.argument('monitor_custom_headers', nargs='+', options_list='--custom-headers', help='Space-separated list of custom headers in KEY=VALUE format.', validator=validate_custom_headers)

    with self.argument_context('network traffic-manager endpoint create') as c:
        c.argument('target', help='Fully-qualified DNS name of the endpoint.')

    # endregion

    # region VirtualNetworks
    with self.argument_context('network vnet') as c:
        c.argument('virtual_network_name', virtual_network_name_type, options_list=['--name', '-n'], id_part='name')
        c.argument('vnet_prefixes', nargs='+', help='Space-separated list of IP address prefixes for the VNet.', options_list='--address-prefixes', metavar='PREFIX')
        c.argument('dns_servers', nargs='+', help='Space-separated list of DNS server IP addresses.', metavar='IP')
        c.argument('ddos_protection', arg_type=get_three_state_flag(), help='Control whether DDoS protection is enabled.', min_api='2017-09-01')
        c.argument('ddos_protection_plan', help='Name or ID of a DDoS protection plan to associate with the VNet.', min_api='2018-02-01', validator=validate_ddos_name_or_id)
        c.argument('vm_protection', arg_type=get_three_state_flag(), help='Enable VM protection for all subnets in the VNet.', min_api='2017-09-01')

    with self.argument_context('network vnet check-ip-address') as c:
        c.argument('ip_address', required=True)

    with self.argument_context('network vnet create') as c:
        c.argument('location', get_location_type(self.cli_ctx))
        c.argument('vnet_name', virtual_network_name_type, options_list=['--name', '-n'], completer=None)

    with self.argument_context('network vnet create', arg_group='Subnet') as c:
        c.argument('subnet_name', help='Name of a new subnet to create within the VNet.')
        c.argument('subnet_prefix', help='IP address prefix for the new subnet. If omitted, automatically reserves a /24 (or as large as available) block within the VNet address space.', metavar='PREFIX', max_api='2018-07-01')
        c.argument('subnet_prefix', options_list='--subnet-prefixes', nargs='+', min_api='2018-08-01', help='Space-separated list of address prefixes in CIDR format for the new subnet. If omitted, automatically reserves a /24 (or as large as available) block within the VNet address space.', metavar='PREFIXES')

    with self.argument_context('network vnet update') as c:
        c.argument('address_prefixes', nargs='+')

    with self.argument_context('network vnet peering') as c:
        c.argument('virtual_network_name', virtual_network_name_type)
        c.argument('virtual_network_peering_name', options_list=['--name', '-n'], help='The name of the VNet peering.', id_part='child_name_1')
        c.argument('remote_virtual_network', options_list=['--remote-vnet', c.deprecate(target='--remote-vnet-id', hide=True, expiration='2.1.0')], help='Resource ID or name of the remote VNet.')

    with self.argument_context('network vnet peering create') as c:
        c.argument('allow_virtual_network_access', options_list='--allow-vnet-access', action='store_true', help='Allows access from the local VNet to the remote VNet.')
        c.argument('allow_gateway_transit', action='store_true', help='Allows gateway link to be used in the remote VNet.')
        c.argument('allow_forwarded_traffic', action='store_true', help='Allows forwarded traffic from the local VNet to the remote VNet.')
        c.argument('use_remote_gateways', action='store_true', help='Allows VNet to use the remote VNet\'s gateway. Remote VNet gateway must have --allow-gateway-transit enabled for remote peering. Only 1 peering can have this flag enabled. Cannot be set if the VNet already has a gateway.')

    with self.argument_context('network vnet subnet') as c:
        c.argument('subnet_name', arg_type=subnet_name_type, options_list=['--name', '-n'], id_part='child_name_1')
        c.argument('nat_gateway', min_api='2019-02-01', validator=validate_nat_gateway, help='Name or ID of a NAT gateway to attach.')
        c.argument('address_prefix', metavar='PREFIX', help='Address prefix in CIDR format.', max_api='2018-07-01')
        c.argument('address_prefix', metavar='PREFIXES', options_list='--address-prefixes', nargs='+', help='Space-separated list of address prefixes in CIDR format.', min_api='2018-08-01')
        c.argument('virtual_network_name', virtual_network_name_type)
        c.argument('network_security_group', validator=get_nsg_validator(), help='Name or ID of a network security group (NSG).')
        c.argument('route_table', help='Name or ID of a route table to associate with the subnet.')
        c.argument('service_endpoints', nargs='+', min_api='2017-06-01')
        c.argument('service_endpoint_policy', nargs='+', min_api='2018-07-01', help='Space-separated list of names or IDs of service endpoint policies to apply.', validator=validate_service_endpoint_policy)
        c.argument('delegations', nargs='+', min_api='2017-08-01', help='Space-separated list of services to whom the subnet should be delegated. (e.g. Microsoft.Sql/servers)', validator=validate_delegations)
        c.argument('disable_private_endpoint_network_policies', arg_type=get_three_state_flag(), min_api='2019-04-01', help='Disable private endpoint network policies on the subnet.')
        c.argument('disable_private_link_service_network_policies', arg_type=get_three_state_flag(), min_api='2019-04-01', help='Disable private link service network policies on the subnet.')

    with self.argument_context('network vnet subnet update') as c:
        c.argument('network_security_group', validator=get_nsg_validator(), help='Name or ID of a network security group (NSG). Use empty string "" to detach it.')

    for scope in ['network vnet subnet list', 'network vnet peering list']:
        with self.argument_context(scope) as c:
            c.argument('ids', deprecate_info=c.deprecate(hide=True, expiration='2.1.0'))

    # endregion

    # region VirtualNetworkGateways
    vnet_gateway_type = CLIArgumentType(help='The gateway type.', arg_type=get_enum_type(VirtualNetworkGatewayType), default=VirtualNetworkGatewayType.vpn.value)
    vnet_gateway_sku_type = CLIArgumentType(help='VNet gateway SKU.', arg_type=get_enum_type(VirtualNetworkGatewaySkuName), default=VirtualNetworkGatewaySkuName.basic.value)
    vnet_gateway_routing_type = CLIArgumentType(help='VPN routing type.', arg_type=get_enum_type(VpnType), default=VpnType.route_based.value)
    with self.argument_context('network vnet-gateway') as c:
        c.argument('virtual_network_gateway_name', options_list=['--name', '-n'], help='Name of the VNet gateway.', completer=get_resource_name_completion_list('Microsoft.Network/virtualNetworkGateways'), id_part='name')
        c.argument('cert_name', help='Root certificate name', options_list=['--name', '-n'])
        c.argument('gateway_name', help='Virtual network gateway name')
        c.argument('gateway_type', vnet_gateway_type)
        c.argument('gateway_default_site', help='Name or ID of a local network gateway representing a local network site with default routes.')
        c.argument('sku', vnet_gateway_sku_type)
        c.argument('vpn_type', vnet_gateway_routing_type)
        c.argument('bgp_peering_address', arg_group='BGP Peering', help='IP address to use for BGP peering.')
        c.argument('public_ip_address', options_list=['--public-ip-addresses'], nargs='+', help='Specify a single public IP (name or ID) for an active-standby gateway. Specify two space-separated public IPs for an active-active gateway.', completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'))
        c.argument('address_prefixes', help='Space-separated list of CIDR prefixes representing the address space for the P2S Vpnclient.', nargs='+', arg_group='VPN Client')
        c.argument('radius_server', min_api='2017-06-01', help='Radius server address to connect to.', arg_group='VPN Client')
        c.argument('radius_secret', min_api='2017-06-01', help='Radius secret to use for authentication.', arg_group='VPN Client')
        c.argument('client_protocol', min_api='2017-06-01', help='Protocols to use for connecting', nargs='+', arg_group='VPN Client', arg_type=get_enum_type(VpnClientProtocol))
        c.argument('custom_routes', min_api='2019-02-01', help='Space-separated list of CIDR prefixes representing the custom routes address space specified by the customer for VpnClient.', nargs='+', arg_group='VPN Client')

    with self.argument_context('network vnet-gateway update') as c:
        c.argument('gateway_type', vnet_gateway_type, default=None)
        c.argument('sku', vnet_gateway_sku_type, default=None)
        c.argument('vpn_type', vnet_gateway_routing_type, default=None)

    with self.argument_context('network vnet-gateway create') as c:
        vnet_help = "Name or ID of an existing virtual network which has a subnet named 'GatewaySubnet'."
        c.argument('virtual_network', options_list='--vnet', help=vnet_help)

    with self.argument_context('network vnet-gateway update') as c:
        c.argument('enable_bgp', help='Enable BGP (Border Gateway Protocol)', arg_group='BGP Peering', arg_type=get_enum_type(['true', 'false']))
        c.argument('virtual_network', virtual_network_name_type, options_list='--vnet', help="Name or ID of a virtual network that contains a subnet named 'GatewaySubnet'.")
        c.extra('address_prefixes', options_list='--address-prefixes', help='List of address prefixes for the VPN gateway.  Prerequisite for uploading certificates.', nargs='+')

    with self.argument_context('network vnet-gateway root-cert create') as c:
        c.argument('public_cert_data', help='Base64 contents of the root certificate file or file path.', type=file_type, completer=FilesCompleter(), validator=load_cert_file('public_cert_data'))
        c.argument('cert_name', help='Root certificate name', options_list=['--name', '-n'])
        c.argument('gateway_name', help='Virtual network gateway name')

    with self.argument_context('network vnet-gateway revoked-cert create') as c:
        c.argument('thumbprint', help='Certificate thumbprint.')

    with self.argument_context('network vnet-gateway vpn-client') as c:
        c.argument('processor_architecture', help='Processor architecture of the target system.', arg_type=get_enum_type(ProcessorArchitecture))
        c.argument('authentication_method', help='Method used to authenticate with the generated client.', arg_type=get_enum_type(AuthenticationMethod))
        c.argument('radius_server_auth_certificate', help='Public certificate data for the Radius server auth certificate in Base-64 format. Required only if external Radius auth has been configured with EAPTLS auth.')
        c.argument('client_root_certificates', nargs='+', help='Space-separated list of client root certificate public certificate data in Base-64 format. Optional for external Radius-based auth with EAPTLS')
        c.argument('use_legacy', min_api='2017-06-01', help='Generate VPN client package using legacy implementation.', arg_type=get_three_state_flag())
    # endregion

    # region VirtualNetworkGatewayConnections
    with self.argument_context('network vpn-connection') as c:
        c.argument('virtual_network_gateway_connection_name', options_list=['--name', '-n'], metavar='NAME', id_part='name', help='Connection name.')
        c.argument('shared_key', help='Shared IPSec key.')
        c.argument('connection_name', help='Connection name.')
        c.argument('routing_weight', type=int, help='Connection routing weight')
        c.argument('use_policy_based_traffic_selectors', min_api='2017-03-01', help='Enable policy-based traffic selectors.', arg_type=get_three_state_flag())
        c.argument('express_route_gateway_bypass', min_api='2018-07-01', arg_type=get_three_state_flag(), help='Bypass ExpressRoute gateway for data forwarding.')

    with self.argument_context('network vpn-connection create') as c:
        c.argument('connection_name', options_list=['--name', '-n'], metavar='NAME', help='Connection name.')
        c.ignore('connection_type')
        for item in ['vnet_gateway2', 'local_gateway2', 'express_route_circuit2']:
            c.argument(item, arg_group='Destination')

    with self.argument_context('network vpn-connection update') as c:
        c.argument('enable_bgp', help='Enable BGP (Border Gateway Protocol)', arg_type=get_enum_type(['true', 'false']))

    with self.argument_context('network vpn-connection shared-key') as c:
        c.argument('connection_shared_key_name', options_list=['--name', '-n'], id_part='name')
        c.argument('virtual_network_gateway_connection_name', options_list='--connection-name', metavar='NAME', id_part='name')
        c.argument('key_length', type=int)

    param_map = {
        'dh_group': 'DhGroup',
        'ike_encryption': 'IkeEncryption',
        'ike_integrity': 'IkeIntegrity',
        'ipsec_encryption': 'IpsecEncryption',
        'ipsec_integrity': 'IpsecIntegrity',
        'pfs_group': 'PfsGroup'
    }
    for scope in ['vpn-connection', 'vnet-gateway']:
        with self.argument_context('network {} ipsec-policy'.format(scope)) as c:
            for dest, model_name in param_map.items():
                model = self.get_models(model_name)
                c.argument(dest, arg_type=get_enum_type(model))
            c.argument('sa_data_size_kilobytes', options_list=['--sa-max-size'], type=int)
            c.argument('sa_life_time_seconds', options_list=['--sa-lifetime'], type=int)
    # endregion

    # region Remove --ids from listsaz
    for scope in ['express-route auth', 'express-route peering']:
        with self.argument_context('network {} list'.format(scope)) as c:
            c.argument('circuit_name', id_part=None)

    with self.argument_context('network nic ip-config list') as c:
        c.argument('resource_name', id_part=None)

    with self.argument_context('network nsg rule list') as c:
        c.argument('network_security_group_name', id_part=None)

    with self.argument_context('network route-filter rule list') as c:
        c.argument('route_filter_name', id_part=None)

    with self.argument_context('network route-table route list') as c:
        c.argument('route_table_name', id_part=None)

    with self.argument_context('network traffic-manager endpoint list') as c:
        c.argument('profile_name', id_part=None)
    # endregion
