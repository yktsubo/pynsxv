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

import argparse
import ConfigParser
import json
from libutils import get_ipsets
from argparse import RawTextHelpFormatter
from tabulate import tabulate
from nsxramlclient.client import NsxClient

__author__ = 'Yuki Tsuboi'


def ipset_create(client_session, ipset_name, ipset_address, scope_id='globalroot-0'):
    """
    This function will create a new ipset in NSX
    :param client_session: An instance of an NsxClient Session
    :param ipset_name: Name of ipset created
    :param ipset_address: address set of ipsets
    :return: returns a tuple, the first item is the ipset ID in NSX as string, the second is string
             containing the ipset URL location as returned from the API
    """
    # get a template dict for the ip set create
    ipset_dict = client_session.extract_resource_body_example('ipsetCreate', 'create')

    # fill the detials for the new ipset in the body dict
    ipset_dict['ipset']['name'] = ipset_name
    ipset_dict['ipset']['value'] = ipset_address
    ipset_dict['ipset']['inheritanceAllowed'] = 'True'

    # create new ipset
    new_ipset = client_session.create('ipsetCreate', uri_parameters={'scopeMoref': scope_id},
                              request_body_dict=ipset_dict)
    return new_ipset['body'], new_ipset['location']

def _ipset_create(client_session, **kwargs):

    ipset_name = kwargs['ipset_name']
    ipset_address = kwargs['ipset_address']
    scope_id = kwargs['scope_id']
    if not ipset_name:
        print 'You must specify a ipset name for create'
        return None

    # Use 'globalroot-0' if scope id is not specified
    if not scope_id:
        scope_id = 'globalroot-0'

    ipset_id, ipset_params = ipset_create(client_session, ipset_name, ipset_address, scope_id=scope_id)

    if kwargs['verbose']:
        print ipset_params
    else:
        print 'IPset {} created with the ID {}'.format(ipset_name, ipset_id)

def ipset_delete(client_session, ipset_name):
    """
    This function will delete a ipset in NSX
    :param client_session: An instance of an NsxClient Session
    :param ipset_name: The name of the ipset to delete
    :return: returns a tuple, the first item is a boolean indicating success or failure to delete the IPset,
             the second item is a string containing to ipset id of the deleted IPset
    """
    ipset_id, ipset_params = ipset_read(client_session, ipset_name)
    if not ipset_id:
        return False, None
    client_session.delete('ipset', uri_parameters={'ipsetId': ipset_id})
    return True, ipset_id

def _ipset_delete(client_session, **kwargs):
    ipset_name = kwargs['ipset_name']
    if not ipset_name:
        print 'You must specify a ipset name for deletion'
        return None

    result, ipset_id = ipset_delete(client_session, ipset_name)

    if result and kwargs['verbose']:
        return json.dumps(ipset_id)
    elif result:
        print 'IPset {} with the ID {} has been deleted'.format(ipset_name, ipset_id)
    else:
        print 'IPset deletion failed'

def ipset_read(client_session, ipset_name, scope_id='globalroot-0'):
    """
    This funtions retrieves details of a ipsetn NSX
    :param client_session: An instance of an NsxClient Session
    :param ipset_name: The name of the IPset to retrieve details from
    :return: returns a tuple, the first item is a string containing the IPset ID, the second is a dictionary
             containing the IPset details retrieved from the API
    """
    all_ipsets = get_ipsets(client_session, scope_id=scope_id)
    try:
        ipset_params = [scope for scope in all_ipsets if scope['name'] == ipset_name][0]
        ipset_id = ipset_params['objectId']
    except IndexError:
        return None, None
    return ipset_id, ipset_params

def _ipset_read(client_session, **kwargs):
    ipset_name = kwargs['ipset_name']
    scope_id = kwargs['scope_id']
    if not ipset_name:
        print 'You must specify a ipset name for read'
        return None

    # Use 'globalroot-0' if scope id is not specified
    if not scope_id:
        scope_id = 'globalroot-0'

    ipset_id, ipset_params = ipset_read(client_session, ipset_name,scope_id=scope_id)
    if ipset_params and kwargs['verbose']:
        print json.dumps(ipset_params)
    elif ipset_id:
        print 'IPset {} has the ID {}'.format(ipset_name, ipset_id)
    else:
        print 'IPset {} not found'.format(ipset_name)


def get_ipset_list(client_session):
    """
    This function returns all ipsets found in NSX
    :param client_session: An instance of an NsxClient Session
    :return: returns a tuple, the first item is a list of tuples with item 0 containing the IPset Name as string
             and item 1 containing the IPset id as string. The second item contains a list of dictionaries containing
             all ipset details
    """
    all_ipsets = get_ipsets(client_session)
    ipset_list = []
    for ipset in all_ipsets:
        try:
            ipset_name = ipset['name']
        except KeyError:
            ipset_name = '<empty name>'
        ipset_list.append((ipset_name, ipset['objectId']))
    return ipset_list, all_ipsets


def _ipset_list_print(client_session, **kwargs):
    ipset_list, ipset_params = get_ipset_list(client_session)
    if kwargs['verbose']:
        print ipset_params
    else:
        print tabulate(ipset_list, headers=["IPset name", "IPset ID"], tablefmt="psql")

def contruct_parser(subparsers):
    parser = subparsers.add_parser('ipset', description="Functions for ipsets",
                                   help="Functions for ipsets",
                                   formatter_class=RawTextHelpFormatter)

    parser.add_argument("command", help="""
    create:   create a new ipset
    read:     return the ipset id
    delete:   delete a ipset"
    list:     return a list of all ipsets
    """)

    parser.add_argument("-a",
                        "--ipset_address",
                        help="ipset address, needed for create")

    parser.add_argument("-s",
                        "--scope_id",
                        help="scope_id, globalroot-0 will be used if it's not specified")

    parser.add_argument("-n",
                        "--name",
                        help="ipset name, needed for create, read and delete")

    parser.set_defaults(func=_ipset_main)

def _ipset_main(args):
    if args.debug:
        debug = True
    else:
        debug = False

    config = ConfigParser.ConfigParser()
    assert config.read(args.ini), 'could not read config file {}'.format(args.ini)

    if args.scope_id:
        scope_id  = args.scope_id
    else:
        try:
            scope_id  = config.get('defaults', 'scope_id')
        except (ConfigParser.NoOptionError):
            scope_id  = 'globalroot-0'

    try:
        nsxramlfile = config.get('nsxraml', 'nsxraml_file')
    except (ConfigParser.NoSectionError):
        nsxramlfile_dir = resource_filename(__name__, 'api_spec')
        nsxramlfile = '{}/nsxvapi.raml'.format(nsxramlfile_dir)

    client_session = NsxClient(nsxramlfile, config.get('nsxv', 'nsx_manager'),
                               config.get('nsxv', 'nsx_username'), config.get('nsxv', 'nsx_password'), debug=debug)

    try:
        command_selector = {
            'list': _ipset_list_print,
            'create': _ipset_create,
            'delete': _ipset_delete,
            'read': _ipset_read
            }
        command_selector[args.command](client_session, scope_id=scope_id,
                                       ipset_name=args.name,ipset_address=args.ipset_address, verbose=args.verbose)
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
