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

__author__ = 'Yuki Tsuboi'

import argparse
import ConfigParser
import json
from libutils import get_scope, connect_to_vc, check_for_parameters
from tabulate import tabulate
from argparse import RawTextHelpFormatter
from libutils import VIM_TYPES
from libutils import get_all_objs

from pprint import pprint
def list_vmhost(vccontent):
    vmhost_list = []
    vmhost_summary_list = []
    container = vccontent.viewManager.CreateContainerView(vccontent.rootFolder, VIM_TYPES['host'], True)
    for managed_object_ref in container.view:
        vmhost_list.append({'name': managed_object_ref.name,
                                  'moid':managed_object_ref._moId,
                                  'vm': managed_object_ref.vm,
                                  'network':managed_object_ref.network,
                                  'datastore':managed_object_ref.datastore})
        vmhost_summary_list.append((managed_object_ref.name,
                               managed_object_ref._moId,
                               len(managed_object_ref.vm),
                               len(managed_object_ref.network),
                               len(managed_object_ref.datastore)))
    container.Destroy()
    return vmhost_list, vmhost_summary_list

def _list_vmhost(vccontent, **kwargs):
    vmhost_list, vmhost_summary_list = list_vmhost(vccontent)
    if kwargs['verbose']:
        pprint(vmhost_list)
    else: 
        print tabulate(vmhost_summary_list, headers=["name", "moid", "# of vm", "# of network", "# of datstore"], tablefmt="psql")
        pass

def contruct_parser(subparsers):
    parser = subparsers.add_parser('vmhost', description="Functions for vShpere VMhost",
                                   help="Functions for vShpere VMhost",
                                   formatter_class=RawTextHelpFormatter)

    parser.add_argument("command", help="""
    list:          list vmhost
    """)

    parser.set_defaults(func=_vmhost_main)

def _vmhost_main(args):
    if args.debug:
        debug = True
    else:
        debug = False

    config = ConfigParser.ConfigParser()
    assert config.read(args.ini), 'could not read config file {}'.format(args.ini)

    # try:
    #     nsxramlfile = config.get('nsxraml', 'nsxraml_file')
    # except (ConfigParser.NoSectionError):
    #     nsxramlfile_dir = resource_filename(__name__, 'api_spec')
    #     nsxramlfile = '{}/nsxvapi.raml'.format(nsxramlfile_dir)

    # client_session = NsxClient(nsxramlfile, config.get('nsxv', 'nsx_manager'),
    #                            config.get('nsxv', 'nsx_username'), config.get('nsxv', 'nsx_password'), debug=debug)

    vccontent = connect_to_vc(config.get('vcenter', 'vcenter'), config.get('vcenter', 'vcenter_user'),
                              config.get('vcenter', 'vcenter_passwd'))

    try:
        command_selector = {
            'list': _list_vmhost
            }
        command_selector[args.command](vccontent,
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
