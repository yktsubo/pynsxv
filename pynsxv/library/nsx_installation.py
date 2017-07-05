#!/usr/bin/env python
# coding=utf-8
#
# Copyright © 2015-2016 VMware, Inc. All Rights Reserved.
#
# Licensed under the X11 (MIT) (the “License”) set forth below;
#
# you may not use this file except in compliance with the License. Unless required by applicable law or agreed to in
# writing, software distributed under the License is distributed on an “AS IS” BASIS, without warranties or conditions
# of any kind, EITHER EXPRESS OR IMPLIED. See the License for the specific language governing permissions and
# limitations under the License. Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the
# Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.
#
# "THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN
# AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.”

__author__ = 'Dimitri Desmidt, Emanuele Mazza, Yves Fauser'

import argparse
import ConfigParser
import json
from libutils import get_scope, connect_to_vc, check_for_parameters
from tabulate import tabulate
from nsxramlclient.client import NsxClient
from argparse import RawTextHelpFormatter
from pkg_resources import resource_filename
import OpenSSL, ssl

def register_vc_config(client_session, vcenter_ip, vcenter_user,vcenter_passwd):

    """
    This function will register NSX to vCenter
    :param client_session: An instance of an NsxClient Session
    :return: returns a tuple, the first item is the logical switch ID in NSX as string, the second is string
             containing the logical switch URL location as returned from the API
    """
    vc_config = show_vc_config(client_session)
    api_cert = ssl.get_server_certificate((vcenter_ip, 9443),ssl_version=2)
    x509_api = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, api_cert)
    api_cert_thumbp = x509_api.digest('sha1')
    vc_config['vcInfo']['ipAddress'] = vcenter_ip
    vc_config['vcInfo']['userName'] = vcenter_user
    vc_config['vcInfo']['password'] = vcenter_passwd
    vc_config['vcInfo']['certificateThumbprint'] = api_cert_thumbp
    vc_config['vcInfo']['assignRoleToUser'] = 'true'

    if 'vcInventoryLastUpdateTime' in vc_config['vcInfo']:
        vc_config['vcInfo'].pop('vcInventoryLastUpdateTime')

    response = client_session.update('vCenterConfig', request_body_dict=vc_config)

    return response

def _register_vc_config(client_session,vcenter_ip, vcenter_user,vcenter_passwd,**kwargs):
    response = register_vc_config(client_session,vcenter_ip, vcenter_user,vcenter_passwd)

    if kwargs['verbose']:
        print(response)
    else:
        status, _ = show_vc_status(client_session)
        if status:
            print 'vCenter is registered to NSX'
        else:
            print 'Failed to register vCenter to NSX'

def show_vc_status(client_session):
    """
    This function will show vcenter status
    :param client_session: An instance of an NsxClient Session
    :return: returns a tuple, the first item is the logical switch ID in NSX as string, the second is string
             containing the logical switch URL location as returned from the API
    """
    status_response = client_session.read('vCenterStatus')
    if status_response['body']['vcConfigStatus']['connected'] == 'true':
        return True, status_response
    else:
        return False, status_response

def _show_vc_status(client_session, **kwargs):
    vc_status, vc_response = show_vc_status(client_session)

    if kwargs['verbose']:
        print(vc_response)
    else:
        if vc_status:
            print 'VC is connected'
        else:
            print 'VC is not connected'

def show_vc_config(client_session):
    """
    This function will show vcenter config
    :param client_session: An instance of an NsxClient Session
    :return: returns a tuple, the first item is the logical switch ID in NSX as string, the second is string
             containing the logical switch URL location as returned from the API
    """
    vc_response = client_session.read('vCenterConfig')
    vc_config = vc_response['body']
    return vc_config,vc_response

def _show_vc_config(client_session, **kwargs):
    vc_config, vc_response = show_vc_config(client_session)

    if kwargs['verbose']:
        print vc_response
    else:
        vc_status, _ = show_vc_status(client_session)
        if vc_status or vc_config['vcInfo'].has_key('ipAddress'):
            result = [[vc_status,vc_config['vcInfo']['ipAddress'],vc_config['vcInfo']['userName']]]
            print tabulate(result, headers=['Status', 'vCenter IP','vCenter Username'], tablefmt="psql")
        else:
            print 'VC is not registered'

def register_sso_config(client_session, vcenter_ip, vcenter_user,vcenter_passwd):

    """
    This function will register SSO in NSX
    :param client_session: An instance of an NsxClient Session
    :return: returns a tuple, the first item is the logical switch ID in NSX as string, the second is string
             containing the logical switch URL location as returned from the API
    """
    lookup_service_full_url = 'https://{}:{}/{}'.format(vcenter_ip,443,'lookupservice/sdk')

    sso_cert = ssl.get_server_certificate((vcenter_ip,443),
                                           ssl_version=2)
    x509_sso = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, sso_cert)
    sso_cert_thumbp = x509_sso.digest('sha1')

    sso_reg = client_session.extract_resource_body_example('ssoConfig', 'create')
    sso_reg['ssoConfig']['ssoAdminUsername'] = vcenter_user
    sso_reg['ssoConfig']['ssoAdminUserpassword'] = vcenter_passwd
    sso_reg['ssoConfig']['ssoLookupServiceUrl'] = lookup_service_full_url
    sso_reg['ssoConfig']['certificateThumbprint'] = sso_cert_thumbp
    sso_config_response = client_session.create('ssoConfig', request_body_dict=sso_reg)

    return sso_config_response

def _register_sso_config(client_session,vcenter_ip, vcenter_user,vcenter_passwd,**kwargs):
    sso_config_response = register_sso_config(client_session,vcenter_ip, vcenter_user,vcenter_passwd)

    if kwargs['verbose']:
        print sso_config_response
    else:
        status, _ = show_sso_status(client_session)
        if status:
            print 'SSO is registered in NSX'
        else:
            print 'Failed to register SSO in NSX'

def show_sso_status(client_session):
    """
    This function will show sso config
    :param client_session: An instance of an NsxClient Session
    :return: returns a tuple, the first item is the logical switch ID in NSX as string, the second is string
             containing the logical switch URL location as returned from the API
    """

    status_response = client_session.read('ssoStatus')
    status = status_response['body']['boolean']
    if status == 'true':
        return True, status_response
    else:
        return False, status_response

def _show_sso_status(client_session, **kwargs):
    sso_status, sso_response = show_sso_status(client_session)

    if kwargs['verbose']:
        print sso_response
    else:
        if sso_status:
            print 'SSO is registered in NSX'
        else:
            print 'SSO is not registered in NSX'

def show_sso_config(client_session):
    """
    This function will show sso config
    :param client_session: An instance of an NsxClient Session
    :return: returns a tuple, the first item is the logical switch ID in NSX as string, the second is string
             containing the logical switch URL location as returned from the API
    """

    sso_response = client_session.read('ssoConfig')
    sso_config = sso_response['body']
    return sso_config, sso_response

def _show_sso_config(client_session, **kwargs):
    sso_config, sso_response = show_sso_config(client_session)

    if kwargs['verbose']:
        print sso_response
    else:
        sso_status, _ = show_sso_status(client_session)
        if sso_status or sso_config['ssoConfig'].has_key('ssoLookupServiceUrl'):
            result = [[sso_status,sso_config['ssoConfig']['ssoAdminUsername'],sso_config['ssoConfig']['ssoLookupServiceUrl']]]
            print tabulate(result, headers=['Status', 'ssoAdminUsername','ssoLookupServiceUrl'], tablefmt="psql")
        else:
            print 'SSO is not registered'

def register_license(client_session, vccontent, license_text):

    """
    This function will register license of NSX in vCenter
    :param client_session: An instance of an NsxClient Session
    :param vccontent: VC contenet
    :return: returns a tuple, the first item is the logical switch ID in NSX as string, the second is string
             containing the logical switch URL location as returned from the API
    """
    license_response = vccontent.licenseManager.licenseAssignmentManager.UpdateAssignedLicense("nsx-netsec",license_text)

    return license_response

def _register_license(client_session, vccontent,**kwargs):
    needed_params = ['license_text']
    if not check_for_parameters(needed_params, kwargs):
        return None

    license_response = register_license(client_session,vccontent,kwargs['license_text'])

    if kwargs['verbose']:
        print license_response
    else:
        print license_response

def contruct_parser(subparsers):
    parser = subparsers.add_parser('installation', description="Functions for NSX installation",
                                   help="Functions for NSX installation",
                                   formatter_class=RawTextHelpFormatter)

    parser.add_argument("command", help="""
    register_vc_config:   register vcenter to nsx
    show_vc_status:       show vc status information 
    show_vc_config:       show vc registration information 
    register_sso_config:  register sso in nsx
    show_sso_status:      show sso registration information 
    show_sso_config:      show sso config information 
    register_license:     register nsx license
    """)

    parser.add_argument("-l",
                        "--license_text",
                        help="License text")

    parser.set_defaults(func=_installation_main)

def _installation_main(args):
    if args.debug:
        debug = True
    else:
        debug = False

    config = ConfigParser.ConfigParser()
    assert config.read(args.ini), 'could not read config file {}'.format(args.ini)

    try:
        nsxramlfile = config.get('nsxraml', 'nsxraml_file')
    except (ConfigParser.NoSectionError):
        nsxramlfile_dir = resource_filename(__name__, 'api_spec')
        nsxramlfile = '{}/nsxvapi.raml'.format(nsxramlfile_dir)

    client_session = NsxClient(nsxramlfile, config.get('nsxv', 'nsx_manager'),
                               config.get('nsxv', 'nsx_username'), config.get('nsxv', 'nsx_password'), debug=debug)

    if args.command in ['register_license']:
        vccontent = connect_to_vc(config.get('vcenter', 'vcenter'), config.get('vcenter', 'vcenter_user'),
                                  config.get('vcenter', 'vcenter_passwd'))
    else:
        vccontent = None

    vcenter_ip = config.get('vcenter', 'vcenter')
    vcenter_user = config.get('vcenter', 'vcenter_user')
    vcenter_passwd = config.get('vcenter', 'vcenter_passwd')

    try:
        command_selector = {
            'register_vc_config': _register_vc_config,
            'show_vc_status': _show_vc_status,
            'show_vc_config': _show_vc_config,
            'register_sso_config': _register_sso_config,
            'show_sso_status': _show_sso_status,
            'show_sso_config': _show_sso_config,
            'register_license': _register_license
            }
        command_selector[args.command](client_session, vccontent=vccontent,
                                       vcenter_ip=vcenter_ip, vcenter_user=vcenter_user,
                                       vcenter_passwd=vcenter_passwd,license_text=args.license_text,
                                       verbose=args.verbose)
    except KeyError as e:
        print('Unknown command {}'.format(e))


def main():
    main_parser = argparse.ArgumentParser()
    subparsers = main_parser.add_subparsers()
    contruct_parser(subparsers)
    args = main_parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
