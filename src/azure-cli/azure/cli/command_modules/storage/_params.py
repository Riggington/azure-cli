# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.profiles import ResourceType
from azure.cli.core.commands.validators import get_default_location_from_resource_group
from azure.cli.core.commands.parameters import (tags_type, file_type, get_location_type, get_enum_type,
                                                get_three_state_flag)

from ._validators import (get_datetime_type, validate_metadata, get_permission_validator, get_permission_help_string,
                          resource_type_type, services_type, validate_entity, validate_select, validate_blob_type,
                          validate_included_datasets, validate_custom_domain, validate_container_public_access,
                          validate_table_payload_format, validate_key, add_progress_callback, process_resource_group,
                          storage_account_key_options, process_file_download_namespace, process_metric_update_namespace,
                          get_char_options_validator, validate_bypass, validate_encryption_source, validate_marker,
                          validate_storage_data_plane_list, validate_azcopy_upload_destination_url,
                          validate_azcopy_remove_arguments, as_user_validator)


def load_arguments(self, _):  # pylint: disable=too-many-locals, too-many-statements
    from argcomplete.completers import FilesCompleter
    from six import u as unicode_string

    from knack.arguments import ignore_type, CLIArgumentType

    from azure.cli.core.commands.parameters import get_resource_name_completion_list

    from .sdkutil import get_table_data_type
    from .completers import get_storage_name_completion_list

    t_base_blob_service = self.get_sdk('blob.baseblobservice#BaseBlobService')
    t_file_service = self.get_sdk('file#FileService')
    t_queue_service = self.get_sdk('queue#QueueService')
    t_table_service = get_table_data_type(self.cli_ctx, 'table', 'TableService')

    acct_name_type = CLIArgumentType(options_list=['--account-name', '-n'], help='The storage account name.',
                                     id_part='name',
                                     completer=get_resource_name_completion_list('Microsoft.Storage/storageAccounts'))
    blob_name_type = CLIArgumentType(options_list=['--blob-name', '-b'], help='The blob name.',
                                     completer=get_storage_name_completion_list(t_base_blob_service, 'list_blobs',
                                                                                parent='container_name'))

    container_name_type = CLIArgumentType(options_list=['--container-name', '-c'], help='The container name.',
                                          completer=get_storage_name_completion_list(t_base_blob_service,
                                                                                     'list_containers'))
    directory_type = CLIArgumentType(options_list=['--directory-name', '-d'], help='The directory name.',
                                     completer=get_storage_name_completion_list(t_file_service,
                                                                                'list_directories_and_files',
                                                                                parent='share_name'))
    file_name_type = CLIArgumentType(options_list=['--file-name', '-f'],
                                     completer=get_storage_name_completion_list(t_file_service,
                                                                                'list_directories_and_files',
                                                                                parent='share_name'))
    share_name_type = CLIArgumentType(options_list=['--share-name', '-s'], help='The file share name.',
                                      completer=get_storage_name_completion_list(t_file_service, 'list_shares'))
    table_name_type = CLIArgumentType(options_list=['--table-name', '-t'],
                                      completer=get_storage_name_completion_list(t_table_service, 'list_tables'))
    queue_name_type = CLIArgumentType(options_list=['--queue-name', '-q'], help='The queue name.',
                                      completer=get_storage_name_completion_list(t_queue_service, 'list_queues'))
    progress_type = CLIArgumentType(help='Include this flag to disable progress reporting for the command.',
                                    action='store_true', validator=add_progress_callback)
    socket_timeout_type = CLIArgumentType(help='The socket timeout(secs), used by the service to regulate data flow.',
                                          type=int)
    num_results_type = CLIArgumentType(
        default=5000, help='Specifies the maximum number of results to return. Provide "*" to return all.',
        validator=validate_storage_data_plane_list)

    sas_help = 'The permissions the SAS grants. Allowed values: {}. Do not use if a stored access policy is ' \
               'referenced with --id that specifies this value. Can be combined.'

    with self.argument_context('storage') as c:
        c.argument('container_name', container_name_type)
        c.argument('directory_name', directory_type)
        c.argument('share_name', share_name_type)
        c.argument('table_name', table_name_type)
        c.argument('retry_wait', options_list=('--retry-interval',))
        c.ignore('progress_callback')
        c.argument('metadata', nargs='+',
                   help='Metadata in space-separated key=value pairs. This overwrites any existing metadata.',
                   validator=validate_metadata)
        c.argument('timeout', help='Request timeout in seconds. Applies to each call to the service.', type=int)

    with self.argument_context('storage', arg_group='Precondition') as c:
        c.argument('if_modified_since',
                   help='Commence only if modified since supplied UTC datetime (Y-m-d\'T\'H:M\'Z\')',
                   type=get_datetime_type(False))
        c.argument('if_unmodified_since',
                   help='Commence only if unmodified since supplied UTC datetime (Y-m-d\'T\'H:M\'Z\')',
                   type=get_datetime_type(False))
        c.argument('if_match')
        c.argument('if_none_match')

    for item in ['delete', 'show', 'update', 'show-connection-string', 'keys', 'network-rule', 'revoke-delegation-keys']:  # pylint: disable=line-too-long
        with self.argument_context('storage account {}'.format(item)) as c:
            c.argument('account_name', acct_name_type, options_list=['--name', '-n'])
            c.argument('resource_group_name', required=False, validator=process_resource_group)

    with self.argument_context('storage account check-name') as c:
        c.argument('name', options_list=['--name', '-n'])

    with self.argument_context('storage account create') as c:
        t_account_type, t_sku_name, t_kind = self.get_models('AccountType', 'SkuName', 'Kind',
                                                             resource_type=ResourceType.MGMT_STORAGE)

        c.register_common_storage_account_options()
        c.argument('location', get_location_type(self.cli_ctx), validator=get_default_location_from_resource_group)
        c.argument('account_type', help='The storage account type', arg_type=get_enum_type(t_account_type))
        c.argument('account_name', acct_name_type, options_list=['--name', '-n'], completer=None)
        c.argument('kind', help='Indicates the type of storage account.',
                   arg_type=get_enum_type(t_kind, default='storage'))
        c.argument('tags', tags_type)
        c.argument('custom_domain', help='User domain assigned to the storage account. Name is the CNAME source.')
        c.argument('sku', help='The storage account SKU.', arg_type=get_enum_type(t_sku_name, default='standard_ragrs'))
        c.argument('enable_files_aadds', arg_type=get_three_state_flag(), min_api='2018-11-01',
                   help='Enable the identity based authentication settings for Azure Files.')

    with self.argument_context('storage account update') as c:
        c.register_common_storage_account_options()
        c.argument('custom_domain',
                   help='User domain assigned to the storage account. Name is the CNAME source. Use "" to clear '
                        'existing value.',
                   validator=validate_custom_domain)
        c.argument('use_subdomain', help='Specify whether to use indirect CNAME validation.',
                   arg_type=get_enum_type(['true', 'false']))
        c.argument('tags', tags_type, default=None)
        c.argument('enable_files_aadds', arg_type=get_three_state_flag(), min_api='2018-11-01',
                   help='Enable the identity based authentication settings for Azure Files.')

    with self.argument_context('storage account update', arg_group='Customer managed key', min_api='2017-06-01') as c:
        c.extra('encryption_key_name', help='The name of the KeyVault key', )
        c.extra('encryption_key_vault', help='The Uri of the KeyVault')
        c.extra('encryption_key_version', help='The version of the KeyVault key')
        c.argument('encryption_key_source',
                   arg_type=get_enum_type(['Microsoft.Storage', 'Microsoft.Keyvault']),
                   help='The default encryption service',
                   validator=validate_encryption_source)
        c.ignore('encryption_key_vault_properties')

    for scope in ['storage account create', 'storage account update']:
        with self.argument_context(scope, resource_type=ResourceType.MGMT_STORAGE, min_api='2017-06-01',
                                   arg_group='Network Rule') as c:
            t_bypass, t_default_action = self.get_models('Bypass', 'DefaultAction',
                                                         resource_type=ResourceType.MGMT_STORAGE)

            c.argument('bypass', nargs='+', validator=validate_bypass, arg_type=get_enum_type(t_bypass),
                       help='Bypass traffic for space-separated uses.')
            c.argument('default_action', arg_type=get_enum_type(t_default_action),
                       help='Default action to apply when no rule matches.')

    with self.argument_context('storage account show-connection-string') as c:
        c.argument('protocol', help='The default endpoint protocol.', arg_type=get_enum_type(['http', 'https']))
        c.argument('sas_token', help='The SAS token to be used in the connection-string.')
        c.argument('key_name', options_list=['--key'], help='The key to use.',
                   arg_type=get_enum_type(list(storage_account_key_options.keys())))
        for item in ['blob', 'file', 'queue', 'table']:
            c.argument('{}_endpoint'.format(item), help='Custom endpoint for {}s.'.format(item))

    with self.argument_context('storage account keys renew') as c:
        c.argument('key_name', options_list=['--key'], help='The key to regenerate.', validator=validate_key,
                   arg_type=get_enum_type(list(storage_account_key_options.keys())))
        c.argument('account_name', acct_name_type, id_part=None)

    with self.argument_context('storage account management-policy create') as c:
        c.argument('policy', type=file_type, completer=FilesCompleter(),
                   help='The Storage Account ManagementPolicies Rules, in JSON format. See more details in: '
                        'https://docs.microsoft.com/azure/storage/common/storage-lifecycle-managment-concepts.')
        c.argument('account_name', help='The name of the storage account within the specified resource group.')

    with self.argument_context('storage account management-policy update') as c:
        c.argument('account_name', help='The name of the storage account within the specified resource group.')

    with self.argument_context('storage account keys list') as c:
        c.argument('account_name', acct_name_type, id_part=None)

    with self.argument_context('storage account network-rule') as c:
        from ._validators import validate_subnet
        c.argument('account_name', acct_name_type, id_part=None)
        c.argument('ip_address', help='IPv4 address or CIDR range.')
        c.argument('subnet', help='Name or ID of subnet. If name is supplied, `--vnet-name` must be supplied.')
        c.argument('vnet_name', help='Name of a virtual network.', validator=validate_subnet)
        c.argument('action', help='The action of virtual network rule.')

    with self.argument_context('storage account generate-sas') as c:
        t_account_permissions = self.get_sdk('common.models#AccountPermissions')
        c.register_sas_arguments()
        c.argument('services', type=services_type(self))
        c.argument('resource_types', type=resource_type_type(self))
        c.argument('expiry', type=get_datetime_type(True))
        c.argument('start', type=get_datetime_type(True))
        c.argument('account_name', acct_name_type, options_list=['--account-name'])
        c.argument('permission', options_list=('--permissions',),
                   help='The permissions the SAS grants. Allowed values: {}. Can be combined.'.format(
                       get_permission_help_string(t_account_permissions)),
                   validator=get_permission_validator(t_account_permissions))
        c.ignore('sas_token')

    with self.argument_context('storage logging show') as c:
        c.extra('services', validator=get_char_options_validator('bqt', 'services'), default='bqt')

    with self.argument_context('storage logging update') as c:
        c.extra('services', validator=get_char_options_validator('bqt', 'services'), options_list='--services',
                required=True)
        c.argument('log', validator=get_char_options_validator('rwd', 'log'))
        c.argument('retention', type=int)
        c.argument('version', type=float)

    with self.argument_context('storage metrics show') as c:
        c.extra('services', validator=get_char_options_validator('bfqt', 'services'), default='bfqt')
        c.argument('interval', arg_type=get_enum_type(['hour', 'minute', 'both']))

    with self.argument_context('storage metrics update') as c:
        c.extra('services', validator=get_char_options_validator('bfqt', 'services'), options_list='--services',
                required=True)
        c.argument('hour', validator=process_metric_update_namespace, arg_type=get_enum_type(['true', 'false']))
        c.argument('minute', arg_type=get_enum_type(['true', 'false']))
        c.argument('api', arg_type=get_enum_type(['true', 'false']))
        c.argument('retention', type=int)

    with self.argument_context('storage blob') as c:
        c.argument('blob_name', options_list=('--name', '-n'), arg_type=blob_name_type)
        c.argument('destination_path', help='The destination path that will be appended to the blob name.')

    with self.argument_context('storage blob list') as c:
        c.argument('include', validator=validate_included_datasets)
        c.argument('num_results', arg_type=num_results_type)

    with self.argument_context('storage blob generate-sas') as c:
        from .completers import get_storage_acl_name_completion_list

        t_blob_permissions = self.get_sdk('blob.models#BlobPermissions')
        c.register_sas_arguments()
        c.argument('cache_control', help='Response header value for Cache-Control when resource is accessed'
                                         'using this shared access signature.')
        c.argument('content_disposition', help='Response header value for Content-Disposition when resource is accessed'
                                               'using this shared access signature.')
        c.argument('content_encoding', help='Response header value for Content-Encoding when resource is accessed'
                                            'using this shared access signature.')
        c.argument('content_language', help='Response header value for Content-Language when resource is accessed'
                                            'using this shared access signature.')
        c.argument('content_type', help='Response header value for Content-Type when resource is accessed'
                                        'using this shared access signature.')
        c.argument('full_uri', action='store_true',
                   help='Indicates that this command return the full blob URI and the shared access signature token.')
        c.argument('as_user', min_api='2018-11-09', is_preview=True, action='store_true',
                   validator=as_user_validator,
                   help="Indicates that this command return the SAS signed with the user delegation key. "
                        "The expiry parameter and '--auth-mode login' are required if this argument is specified. ")
        c.argument('id', options_list='--policy-name',
                   help='The name of a stored access policy within the container\'s ACL.',
                   completer=get_storage_acl_name_completion_list(t_base_blob_service, 'container_name',
                                                                  'get_container_acl'))
        c.argument('permission', options_list='--permissions',
                   help=sas_help.format(get_permission_help_string(t_blob_permissions)),
                   validator=get_permission_validator(t_blob_permissions))

    with self.argument_context('storage blob update') as c:
        t_blob_content_settings = self.get_sdk('blob.models#ContentSettings')
        c.register_content_settings_argument(t_blob_content_settings, update=True)

    with self.argument_context('storage blob exists') as c:
        c.argument('blob_name', required=True)

    with self.argument_context('storage blob url') as c:
        c.argument('protocol', arg_type=get_enum_type(['http', 'https'], 'https'), help='Protocol to use.')
        c.argument('snapshot', help='An string value that uniquely identifies the snapshot. The value of'
                                    'this query parameter indicates the snapshot version.')

    with self.argument_context('storage blob set-tier') as c:
        from azure.cli.command_modules.storage._validators import blob_tier_validator

        c.argument('blob_type', options_list=('--type', '-t'), arg_type=get_enum_type(('block', 'page')))
        c.argument('tier', validator=blob_tier_validator)
        c.argument('timeout', type=int)

    with self.argument_context('storage blob service-properties delete-policy update') as c:
        c.argument('enable', arg_type=get_enum_type(['true', 'false']), help='Enables/disables soft-delete.')
        c.argument('days_retained', type=int,
                   help='Number of days that soft-deleted blob will be retained. Must be in range [1,365].')

    with self.argument_context('storage blob service-properties update', min_api='2018-03-28') as c:
        c.argument('delete_retention', arg_type=get_three_state_flag(), arg_group='Soft Delete',
                   help='Enables soft-delete.')
        c.argument('delete_retention_period', type=int, arg_group='Soft Delete',
                   help='Number of days that soft-deleted blob will be retained. Must be in range [1,365].')
        c.argument('static_website', arg_group='Static Website', arg_type=get_three_state_flag(),
                   help='Enables static-website.')
        c.argument('index_document', help='Represents the name of the index document. This is commonly "index.html".',
                   arg_group='Static Website')
        c.argument('error_document_404_path', options_list=['--404-document'], arg_group='Static Website',
                   help='Represents the path to the error document that should be shown when an error 404 is issued,'
                        ' in other words, when a browser requests a page that does not exist.')

    with self.argument_context('storage blob upload') as c:
        from ._validators import page_blob_tier_validator
        from .sdkutil import get_blob_types, get_blob_tier_names

        t_blob_content_settings = self.get_sdk('blob.models#ContentSettings')
        c.register_content_settings_argument(t_blob_content_settings, update=False)

        c.argument('file_path', options_list=('--file', '-f'), type=file_type, completer=FilesCompleter())
        c.argument('max_connections', type=int)
        c.argument('blob_type', options_list=('--type', '-t'), validator=validate_blob_type,
                   arg_type=get_enum_type(get_blob_types()))
        c.argument('validate_content', action='store_true', min_api='2016-05-31')
        c.extra('no_progress', progress_type)
        c.extra('socket_timeout', socket_timeout_type)
        # TODO: Remove once #807 is complete. Smart Create Generation requires this parameter.
        # register_extra_cli_argument('storage blob upload', '_subscription_id', options_list=('--subscription',),
        #                              help=argparse.SUPPRESS)
        c.argument('tier', validator=page_blob_tier_validator,
                   arg_type=get_enum_type(get_blob_tier_names(self.cli_ctx, 'PremiumPageBlobTier')),
                   min_api='2017-04-17')

    with self.argument_context('storage blob upload-batch') as c:
        from .sdkutil import get_blob_types

        t_blob_content_settings = self.get_sdk('blob.models#ContentSettings')
        c.register_content_settings_argument(t_blob_content_settings, update=False, arg_group='Content Control')
        c.ignore('source_files', 'destination_container_name')

        c.argument('source', options_list=('--source', '-s'))
        c.argument('destination', options_list=('--destination', '-d'))
        c.argument('max_connections', type=int,
                   help='Maximum number of parallel connections to use when the blob size exceeds 64MB.')
        c.argument('maxsize_condition', arg_group='Content Control')
        c.argument('validate_content', action='store_true', min_api='2016-05-31', arg_group='Content Control')
        c.argument('blob_type', options_list=('--type', '-t'), arg_type=get_enum_type(get_blob_types()))
        c.extra('no_progress', progress_type)
        c.extra('socket_timeout', socket_timeout_type)

    with self.argument_context('storage blob download') as c:
        c.argument('file_path', options_list=('--file', '-f'), type=file_type, completer=FilesCompleter())
        c.argument('max_connections', type=int)
        c.argument('start_range', type=int)
        c.argument('end_range', type=int)
        c.argument('validate_content', action='store_true', min_api='2016-05-31')
        c.extra('no_progress', progress_type)
        c.extra('socket_timeout', socket_timeout_type)

    with self.argument_context('storage blob download-batch') as c:
        c.ignore('source_container_name')
        c.argument('destination', options_list=('--destination', '-d'))
        c.argument('source', options_list=('--source', '-s'))
        c.extra('no_progress', progress_type)
        c.extra('socket_timeout', socket_timeout_type)
        c.argument('max_connections', type=int,
                   help='Maximum number of parallel connections to use when the blob size exceeds 64MB.')

    with self.argument_context('storage blob delete') as c:
        from .sdkutil import get_delete_blob_snapshot_type_names
        c.argument('delete_snapshots', arg_type=get_enum_type(get_delete_blob_snapshot_type_names()))

    with self.argument_context('storage blob delete-batch') as c:
        c.ignore('source_container_name')
        c.argument('source', options_list=('--source', '-s'))
        c.argument('delete_snapshots', arg_type=get_enum_type(get_delete_blob_snapshot_type_names()),
                   help='Required if the blob has associated snapshots.')
        c.argument('lease_id', help='The active lease id for the blob.')

    with self.argument_context('storage blob lease') as c:
        c.argument('lease_duration', type=int)
        c.argument('lease_break_period', type=int)
        c.argument('blob_name', arg_type=blob_name_type)

    with self.argument_context('storage copy') as c:
        c.argument('destination', options_list=['--destination', '-d'], help="The path/url of copy destination. \
            It can be local path, an url to azure storage server. For more imformation, please refer to [link here]. \
            If you provide destination parameter here, you do not need to provide arguments in copy \
            destination arguments group and copy destination arguments will be deprecated  in future.")
        c.argument('source', options_list=['--source', '-s'], help="The path/url of copy source. \
            It can be local path, an url to azure storage server or AWS S3 buckets. For more imformation, please refer to [link here]. \
            If you provide source parameter here, you do not need to provide arguments in copy source arguments group and copy source \
            arguments will be deprecated in future.")
        for item in ['destination', 'source']:
            c.argument('{}_account_name'.format(item), arg_group='Copy {}'.format(item),
                       help='Storage account name of copy {}'.format(item))
            c.argument('{}_container'.format(item), arg_group='Copy {}'.format(item),
                       help='Container name of copy {} storage account'.format(item))
            c.argument('{}_blob'.format(item), arg_group='Copy {}'.format(item),
                       help='Blob name in blob container of copy {} storage account'.format(item))
            c.argument('{}_share'.format(item), arg_group='Copy {}'.format(item),
                       help='File share name of copy {} storage account'.format(item))
            c.argument('{}_file_path'.format(item), arg_group='Copy {}'.format(item),
                       help='File path in file share of copy {} storage account'.format(item))
            c.argument('{}_local_path'.format(item), arg_group='Copy {}'.format(item),
                       help='Local file path')
        c.argument('recursive', action='store_true', help='Look into sub-directories \
                    recursively when uploading from local file system.')
        c.argument('put_md5', action='store_true', help='Create an MD5 hash of each file, and save the hash \
                    as the Content-MD5 property of the destination blob/file.Only available when uploading.')

    with self.argument_context('storage blob copy') as c:
        for item in ['destination', 'source']:
            c.argument('{}_if_modified_since'.format(item), arg_group='Pre-condition')
            c.argument('{}_if_unmodified_since'.format(item), arg_group='Pre-condition')
            c.argument('{}_if_match'.format(item), arg_group='Pre-condition')
            c.argument('{}_if_none_match'.format(item), arg_group='Pre-condition')
        c.argument('container_name', container_name_type, options_list=('--destination-container', '-c'))
        c.argument('blob_name', blob_name_type, options_list=('--destination-blob', '-b'),
                   help='Name of the destination blob. If the exists, it will be overwritten.')
        c.argument('source_lease_id', arg_group='Copy Source')

    with self.argument_context('storage blob copy start') as c:
        from azure.cli.command_modules.storage._validators import validate_source_uri

        c.register_source_uri_arguments(validator=validate_source_uri)

    with self.argument_context('storage blob copy start-batch', arg_group='Copy Source') as c:
        from azure.cli.command_modules.storage._validators import get_source_file_or_blob_service_client

        c.argument('source_client', ignore_type, validator=get_source_file_or_blob_service_client)

        c.extra('source_account_name')
        c.extra('source_account_key')
        c.extra('source_uri')
        c.argument('source_sas')
        c.argument('source_container')
        c.argument('source_share')

    with self.argument_context('storage blob incremental-copy start') as c:
        from azure.cli.command_modules.storage._validators import process_blob_source_uri

        c.register_source_uri_arguments(validator=process_blob_source_uri, blob_only=True)
        c.argument('destination_if_modified_since', arg_group='Pre-condition')
        c.argument('destination_if_unmodified_since', arg_group='Pre-condition')
        c.argument('destination_if_match', arg_group='Pre-condition')
        c.argument('destination_if_none_match', arg_group='Pre-condition')
        c.argument('container_name', container_name_type, options_list=('--destination-container', '-c'))
        c.argument('blob_name', blob_name_type, options_list=('--destination-blob', '-b'),
                   help='Name of the destination blob. If the exists, it will be overwritten.')
        c.argument('source_lease_id', arg_group='Copy Source')

    with self.argument_context('storage blob sync') as c:
        c.extra('destination_container', options_list=['--container', '-c'], required=True,
                help='The sync destination container.')
        c.extra('destination_path', options_list=['--destination', '-d'],
                validator=validate_azcopy_upload_destination_url,
                help='The sync destination path.')
        c.argument('source', options_list=['--source', '-s'],
                   help='The source file path to sync from.')
        c.ignore('destination')

    with self.argument_context('storage container') as c:
        from .sdkutil import get_container_access_type_names
        c.argument('container_name', container_name_type, options_list=('--name', '-n'))
        c.argument('public_access', validator=validate_container_public_access,
                   arg_type=get_enum_type(get_container_access_type_names()),
                   help='Specifies whether data in the container may be accessed publicly.')

    with self.argument_context('storage container create') as c:
        c.argument('container_name', container_name_type, options_list=('--name', '-n'), completer=None)
        c.argument('fail_on_exist', help='Throw an exception if the container already exists.')

    with self.argument_context('storage container delete') as c:
        c.argument('fail_not_exist', help='Throw an exception if the container does not exist.')
        c.argument('bypass_immutability_policy', action='store_true', help='Bypasses upcoming service behavior that '
                   'will block a container from being deleted if it has a immutability-policy. Specifying this will '
                   'ignore arguments aside from those used to identify the container ("--name", "--account-name").')
        c.argument('lease_id', help="If specified, delete_container only succeeds if the container's lease is active "
                                    "and matches this ID. Required if the container has an active lease.")
        c.ignore('processed_resource_group')
        c.ignore('processed_account_name')
        c.ignore('mgmt_client')

    with self.argument_context('storage container exists') as c:
        c.ignore('blob_name', 'snapshot')

    with self.argument_context('storage container list') as c:
        c.argument('num_results', arg_type=num_results_type)

    with self.argument_context('storage container set-permission') as c:
        c.ignore('signed_identifiers')

    with self.argument_context('storage container lease') as c:
        c.argument('container_name', container_name_type)

    with self.argument_context('storage container') as c:
        c.argument('account_name', completer=get_resource_name_completion_list('Microsoft.Storage/storageAccounts'))
        c.argument('resource_group_name', required=False, validator=process_resource_group)

    with self.argument_context('storage container immutability-policy') as c:
        c.argument('immutability_period_since_creation_in_days', options_list='--period')
        c.argument('container_name', container_name_type)

    with self.argument_context('storage container legal-hold') as c:
        c.argument('container_name', container_name_type)
        c.argument('tags', nargs='+',
                   help='Each tag should be 3 to 23 alphanumeric characters and is normalized to lower case')

    with self.argument_context('storage container policy') as c:
        from .completers import get_storage_acl_name_completion_list
        t_container_permissions = self.get_sdk('blob.models#ContainerPermissions')

        c.argument('container_name', container_name_type)
        c.argument('policy_name', options_list=('--name', '-n'), help='The stored access policy name.',
                   completer=get_storage_acl_name_completion_list(t_base_blob_service, 'container_name',
                                                                  'get_container_acl'))
        help_str = 'Allowed values: {}. Can be combined'.format(get_permission_help_string(t_container_permissions))
        c.argument('permission', options_list='--permissions', help=help_str,
                   validator=get_permission_validator(t_container_permissions))

        c.argument('start', type=get_datetime_type(True),
                   help='start UTC datetime (Y-m-d\'T\'H:M:S\'Z\'). Defaults to time of request.')
        c.argument('expiry', type=get_datetime_type(True), help='expiration UTC datetime in (Y-m-d\'T\'H:M:S\'Z\')')

    for item in ['create', 'delete', 'list', 'show', 'update']:
        with self.argument_context('storage container policy {}'.format(item)) as c:
            c.extra('lease_id', options_list='--lease-id', help='The container lease ID.')

    with self.argument_context('storage container generate-sas') as c:
        from .completers import get_storage_acl_name_completion_list
        t_container_permissions = self.get_sdk('blob.models#ContainerPermissions')
        c.register_sas_arguments()
        c.argument('id', options_list='--policy-name',
                   help='The name of a stored access policy within the container\'s ACL.',
                   completer=get_storage_acl_name_completion_list(t_container_permissions, 'container_name',
                                                                  'get_container_acl'))
        c.argument('permission', options_list='--permissions',
                   help=sas_help.format(get_permission_help_string(t_container_permissions)),
                   validator=get_permission_validator(t_container_permissions))
        c.argument('cache_control', help='Response header value for Cache-Control when resource is accessed'
                                         'using this shared access signature.')
        c.argument('content_disposition', help='Response header value for Content-Disposition when resource is accessed'
                                               'using this shared access signature.')
        c.argument('content_encoding', help='Response header value for Content-Encoding when resource is accessed'
                                            'using this shared access signature.')
        c.argument('content_language', help='Response header value for Content-Language when resource is accessed'
                                            'using this shared access signature.')
        c.argument('content_type', help='Response header value for Content-Type when resource is accessed'
                                        'using this shared access signature.')
        c.argument('as_user', min_api='2018-11-09', is_preview=True, action='store_true',
                   validator=as_user_validator,
                   help="Indicates that this command return the SAS signed with the user delegation key. "
                        "The expiry parameter and '--auth-mode login' are required if this argument is specified. ")
    with self.argument_context('storage container lease') as c:
        c.argument('lease_duration', type=int)
        c.argument('lease_break_period', type=int)

    with self.argument_context('storage share') as c:
        c.argument('share_name', share_name_type, options_list=('--name', '-n'))

    with self.argument_context('storage share url') as c:
        c.argument('unc', action='store_true', help='Output UNC network path.')
        c.argument('protocol', arg_type=get_enum_type(['http', 'https'], 'https'), help='Protocol to use.')

    with self.argument_context('storage share list') as c:
        c.argument('num_results', arg_type=num_results_type)

    with self.argument_context('storage share exists') as c:
        c.ignore('directory_name', 'file_name')

    with self.argument_context('storage share policy') as c:
        from .completers import get_storage_acl_name_completion_list

        t_file_svc = self.get_sdk('file#FileService')
        t_share_permissions = self.get_sdk('file.models#SharePermissions')

        c.argument('container_name', share_name_type)
        c.argument('policy_name', options_list=('--name', '-n'), help='The stored access policy name.',
                   completer=get_storage_acl_name_completion_list(t_file_svc, 'container_name', 'get_share_acl'))

        help_str = 'Allowed values: {}. Can be combined'.format(get_permission_help_string(t_share_permissions))
        c.argument('permission', options_list='--permissions', help=help_str,
                   validator=get_permission_validator(t_share_permissions))

        c.argument('start', type=get_datetime_type(True),
                   help='start UTC datetime (Y-m-d\'T\'H:M:S\'Z\'). Defaults to time of request.')
        c.argument('expiry', type=get_datetime_type(True), help='expiration UTC datetime in (Y-m-d\'T\'H:M:S\'Z\')')

    with self.argument_context('storage share delete') as c:
        from .sdkutil import get_delete_file_snapshot_type_names
        c.argument('delete_snapshots', arg_type=get_enum_type(get_delete_file_snapshot_type_names()),
                   help='Specify the deletion strategy when the share has snapshots.')

    with self.argument_context('storage share generate-sas') as c:
        from .completers import get_storage_acl_name_completion_list

        t_share_permissions = self.get_sdk('file.models#SharePermissions')
        c.register_sas_arguments()
        c.argument('id', options_list='--policy-name',
                   help='The name of a stored access policy within the share\'s ACL.',
                   completer=get_storage_acl_name_completion_list(t_share_permissions, 'share_name', 'get_share_acl'))
        c.argument('permission', options_list='--permissions',
                   help=sas_help.format(get_permission_help_string(t_share_permissions)),
                   validator=get_permission_validator(t_share_permissions))

    with self.argument_context('storage directory') as c:
        c.argument('directory_name', directory_type, options_list=('--name', '-n'))

    with self.argument_context('storage directory exists') as c:
        c.ignore('file_name')
        c.argument('directory_name', required=True)

    with self.argument_context('storage file') as c:
        c.argument('file_name', file_name_type, options_list=('--name', '-n'))
        c.argument('directory_name', directory_type, required=False)

    with self.argument_context('storage file copy') as c:
        c.argument('share_name', share_name_type, options_list=('--destination-share', '-s'),
                   help='Name of the destination share. The share must exist.')

    with self.argument_context('storage file copy cancel') as c:
        c.register_path_argument(options_list=('--destination-path', '-p'))

    with self.argument_context('storage file delete') as c:
        c.register_path_argument()

    with self.argument_context('storage file download') as c:
        c.register_path_argument()
        c.argument('file_path', options_list=('--dest',), type=file_type, required=False,
                   help='Path of the file to write to. The source filename will be used if not specified.',
                   validator=process_file_download_namespace, completer=FilesCompleter())
        c.argument('path', validator=None)  # validator called manually from process_file_download_namespace
        c.extra('no_progress', progress_type)
        c.argument('max_connections', type=int)
        c.argument('start_range', type=int)
        c.argument('end_range', type=int)

    with self.argument_context('storage file exists') as c:
        c.register_path_argument()

    with self.argument_context('storage file generate-sas') as c:
        from .completers import get_storage_acl_name_completion_list

        c.register_path_argument()
        c.register_sas_arguments()

        t_file_svc = self.get_sdk('file.fileservice#FileService')
        t_file_permissions = self.get_sdk('file.models#FilePermissions')
        c.argument('id', options_list='--policy-name',
                   help='The name of a stored access policy within the container\'s ACL.',
                   completer=get_storage_acl_name_completion_list(t_file_svc, 'container_name', 'get_container_acl'))
        c.argument('permission', options_list='--permissions',
                   help=sas_help.format(get_permission_help_string(t_file_permissions)),
                   validator=get_permission_validator(t_file_permissions))

    with self.argument_context('storage file list') as c:
        from .completers import dir_path_completer
        c.argument('directory_name', options_list=('--path', '-p'), help='The directory path within the file share.',
                   completer=dir_path_completer)
        c.argument('num_results', arg_type=num_results_type)

    with self.argument_context('storage file metadata show') as c:
        c.register_path_argument()

    with self.argument_context('storage file metadata update') as c:
        c.register_path_argument()

    with self.argument_context('storage file resize') as c:
        c.register_path_argument()
        c.argument('content_length', options_list='--size')

    with self.argument_context('storage file show') as c:
        c.register_path_argument()

    with self.argument_context('storage file update') as c:
        t_file_content_settings = self.get_sdk('file.models#ContentSettings')

        c.register_path_argument()
        c.register_content_settings_argument(t_file_content_settings, update=True)

    with self.argument_context('storage file upload') as c:
        t_file_content_settings = self.get_sdk('file.models#ContentSettings')

        c.register_path_argument(default_file_param='local_file_path')
        c.register_content_settings_argument(t_file_content_settings, update=False, guess_from_file='local_file_path')
        c.argument('local_file_path', options_list='--source', type=file_type, completer=FilesCompleter())
        c.extra('no_progress', progress_type)
        c.argument('max_connections', type=int)

    with self.argument_context('storage file url') as c:
        c.register_path_argument()
        c.argument('protocol', arg_type=get_enum_type(['http', 'https'], 'https'), help='Protocol to use.')

    with self.argument_context('storage file upload-batch') as c:
        from ._validators import process_file_upload_batch_parameters
        c.argument('source', options_list=('--source', '-s'), validator=process_file_upload_batch_parameters)
        c.argument('destination', options_list=('--destination', '-d'))
        c.argument('max_connections', arg_group='Download Control', type=int)
        c.argument('validate_content', action='store_true', min_api='2016-05-31')
        c.register_content_settings_argument(t_file_content_settings, update=False, arg_group='Content Settings')
        c.extra('no_progress', progress_type)

    with self.argument_context('storage file download-batch') as c:
        from ._validators import process_file_download_batch_parameters
        c.argument('source', options_list=('--source', '-s'), validator=process_file_download_batch_parameters)
        c.argument('destination', options_list=('--destination', '-d'))
        c.argument('max_connections', arg_group='Download Control', type=int)
        c.argument('validate_content', action='store_true', min_api='2016-05-31')
        c.extra('no_progress', progress_type)

    with self.argument_context('storage file delete-batch') as c:
        from ._validators import process_file_batch_source_parameters
        c.argument('source', options_list=('--source', '-s'), validator=process_file_batch_source_parameters)

    with self.argument_context('storage file copy start') as c:
        from azure.cli.command_modules.storage._validators import validate_source_uri

        c.register_path_argument(options_list=('--destination-path', '-p'))
        c.register_source_uri_arguments(validator=validate_source_uri)
        c.extra('file_snapshot', default=None, arg_group='Copy Source',
                help='The file snapshot for the source storage account.')

    with self.argument_context('storage file copy start-batch', arg_group='Copy Source') as c:
        from ._validators import get_source_file_or_blob_service_client
        c.argument('source_client', ignore_type, validator=get_source_file_or_blob_service_client)
        c.extra('source_account_name')
        c.extra('source_account_key')
        c.extra('source_uri')
        c.argument('source_sas')
        c.argument('source_container')
        c.argument('source_share')

    with self.argument_context('storage cors list') as c:
        c.extra('services', validator=get_char_options_validator('bfqt', 'services'), default='bqft',
                options_list='--services', required=False)

    with self.argument_context('storage cors add') as c:
        c.extra('services', validator=get_char_options_validator('bfqt', 'services'), required=True,
                options_list='--services')
        c.argument('max_age')
        c.argument('origins', nargs='+')
        c.argument('methods', nargs='+',
                   arg_type=get_enum_type(['DELETE', 'GET', 'HEAD', 'MERGE', 'POST', 'OPTIONS', 'PUT']))
        c.argument('allowed_headers', nargs='+')
        c.argument('exposed_headers', nargs='+')

    with self.argument_context('storage cors clear') as c:
        c.extra('services', validator=get_char_options_validator('bfqt', 'services'), required=True,
                options_list='--services')

    with self.argument_context('storage queue generate-sas') as c:
        from .completers import get_storage_acl_name_completion_list

        t_queue_permissions = self.get_sdk('queue.models#QueuePermissions')

        c.register_sas_arguments()

        c.argument('id', options_list='--policy-name',
                   help='The name of a stored access policy within the share\'s ACL.',
                   completer=get_storage_acl_name_completion_list(t_queue_permissions, 'queue_name', 'get_queue_acl'))
        c.argument('permission', options_list='--permissions',
                   help=sas_help.format(get_permission_help_string(t_queue_permissions)),
                   validator=get_permission_validator(t_queue_permissions))

    with self.argument_context('storage queue') as c:
        c.argument('queue_name', queue_name_type, options_list=('--name', '-n'))

    with self.argument_context('storage queue create') as c:
        c.argument('queue_name', queue_name_type, options_list=('--name', '-n'), completer=None)

    with self.argument_context('storage queue policy') as c:
        from .completers import get_storage_acl_name_completion_list

        t_queue_permissions = self.get_sdk('queue.models#QueuePermissions')

        c.argument('container_name', queue_name_type)
        c.argument('policy_name', options_list=('--name', '-n'), help='The stored access policy name.',
                   completer=get_storage_acl_name_completion_list(t_queue_service, 'container_name', 'get_queue_acl'))

        help_str = 'Allowed values: {}. Can be combined'.format(get_permission_help_string(t_queue_permissions))
        c.argument('permission', options_list='--permissions', help=help_str,
                   validator=get_permission_validator(t_queue_permissions))

        c.argument('start', type=get_datetime_type(True),
                   help='start UTC datetime (Y-m-d\'T\'H:M:S\'Z\'). Defaults to time of request.')
        c.argument('expiry', type=get_datetime_type(True), help='expiration UTC datetime in (Y-m-d\'T\'H:M:S\'Z\')')

    with self.argument_context('storage message') as c:
        c.argument('queue_name', queue_name_type)
        c.argument('message_id', options_list='--id')
        c.argument('content', type=unicode_string, help='Message content, up to 64KB in size.')

    with self.argument_context('storage remove') as c:
        from .completers import file_path_completer

        c.extra('container_name', container_name_type, validator=validate_azcopy_remove_arguments)
        c.extra('blob_name', options_list=('--name', '-n'), arg_type=blob_name_type)
        c.extra('share_name', share_name_type, help='The file share name.')
        c.extra('path', options_list=('--path', '-p'),
                help='The path to the file within the file share.',
                completer=file_path_completer)
        c.argument('exclude', help='Exclude files whose name matches the pattern list.')
        c.argument('include', help='Only include files whose name matches the pattern list.')
        c.argument('recursive', options_list=['--recursive', '-r'], action='store_true',
                   help='Look into sub-directories recursively when deleting between directories.')
        c.ignore('destination')
        c.ignore('service')
        c.ignore('target')

    with self.argument_context('storage table') as c:
        c.argument('table_name', table_name_type, options_list=('--name', '-n'))

    with self.argument_context('storage table create') as c:
        c.argument('table_name', table_name_type, options_list=('--name', '-n'), completer=None)
        c.argument('fail_on_exist', help='Throw an exception if the table already exists.')

    with self.argument_context('storage table policy') as c:
        from ._validators import table_permission_validator
        from .completers import get_storage_acl_name_completion_list

        c.argument('container_name', table_name_type)
        c.argument('policy_name', options_list=('--name', '-n'), help='The stored access policy name.',
                   completer=get_storage_acl_name_completion_list(t_table_service, 'table_name', 'get_table_acl'))

        help_str = 'Allowed values: (r)ead/query (a)dd (u)pdate (d)elete. Can be combined.'
        c.argument('permission', options_list='--permissions', help=help_str, validator=table_permission_validator)

        c.argument('start', type=get_datetime_type(True),
                   help='start UTC datetime (Y-m-d\'T\'H:M:S\'Z\'). Defaults to time of request.')
        c.argument('expiry', type=get_datetime_type(True), help='expiration UTC datetime in (Y-m-d\'T\'H:M:S\'Z\')')

    with self.argument_context('storage table generate-sas') as c:
        from .completers import get_storage_acl_name_completion_list

        c.register_sas_arguments()
        c.argument('id', options_list='--policy-name',
                   help='The name of a stored access policy within the table\'s ACL.',
                   completer=get_storage_acl_name_completion_list(t_table_service, 'table_name', 'get_table_acl'))
        c.argument('permission', options_list='--permissions',
                   help=sas_help.format('(r)ead/query (a)dd (u)pdate (d)elete'),
                   validator=table_permission_validator)

    with self.argument_context('storage entity') as c:
        c.ignore('property_resolver')
        c.argument('entity', options_list=('--entity', '-e'), validator=validate_entity, nargs='+')
        c.argument('select', nargs='+', validator=validate_select,
                   help='Space-separated list of properties to return for each entity.')

    with self.argument_context('storage entity insert') as c:
        c.argument('if_exists', arg_type=get_enum_type(['fail', 'merge', 'replace']))

    with self.argument_context('storage entity query') as c:
        c.argument('accept', default='minimal', validator=validate_table_payload_format,
                   arg_type=get_enum_type(['none', 'minimal', 'full']),
                   help='Specifies how much metadata to include in the response payload.')
        c.argument('marker', validator=validate_marker, nargs='+')
