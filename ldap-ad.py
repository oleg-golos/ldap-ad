#!/usr/bin/env python3

import os
import re
import ldap3
import json
import configparser
import argparse
import ssl
from datetime import datetime, timedelta, tzinfo
from calendar import timegm

parser = argparse.ArgumentParser(
    description='Script to obtain host inventory from AD')
parser.add_argument('--list', action='store_true',
                    help='prints a json of hosts with groups and variables')
parser.add_argument('--host', help='returns variables of given host')
args = parser.parse_args()


class ADAnsibleInventory():

    def __init__(self):
        username = 'domain.local\ad_user'
        password = 'P@ssw0rd'
        basedn = 'DC=domain,DC=local'
        ldapuri = 'DC01.domain.local'
        port = '636'
        lastlogondays = 14
        EPOCH_AS_FILETIME = 116444736000000000  # January 1, 1970 as MS file time
        HUNDREDS_OF_NANOSECONDS = 10000000
        timestamp = datetime.now() - timedelta(days=lastlogondays)
        filetime = EPOCH_AS_FILETIME + (timegm(timestamp.timetuple()) * HUNDREDS_OF_NANOSECONDS)
        filetime = filetime + (timestamp.microsecond * 10)
        adfilter = "(&(sAMAccountType=805306369)(operatingSystem=Windows Server*)(lastlogontimestamp>={}))".format(filetime)
        #print(adfilter)

        self.inventory = {"_meta": {"hostvars": {}}}
        self.ad_connect(ldapuri, username, password, port)
        self.get_hosts(basedn, adfilter)
        self.org_hosts(basedn)
        self.add_vars()
        if args.list:
            print(json.dumps(self.inventory, indent=2))
        if args.host is not None:
            try:
                print(self.inventory['_meta']['hostvars'][args.host])
            except Exception:
                print('{}')

    def ad_connect(self, ldapuri, username, password, port):
        server = ldap3.Server(ldapuri)
        conn = ldap3.Connection(server,
                                auto_bind=True,
                                user=username,
                                password=password,
                                authentication=ldap3.NTLM)
        self.conn = conn

    def get_hosts(self, basedn, adfilter):
        self.conn.search(search_base=basedn,
                         search_filter=adfilter,
                         attributes=['cn', 'dnshostname','operatingSystem'])
        self.conn.response_to_json
        self.results = self.conn.response
        #print(self.results)

    def org_hosts(self, basedn):
        # Removes CN,OU, and DC and places into a list
        for computer in self.results:
            if computer['type'] == "searchResRef":
                continue
            org_list = (re.sub(r"..=", "", computer['dn'])).split(",")
            # Remove hostname
            del org_list[0]

            # Reverse list so top group is first
            org_list.reverse()

            org_range = range(0, (len(org_list)))
            for orgs in org_range:
                if computer['attributes']['dNSHostName']:
                    if orgs == org_range[-1]:
                        self.add_host(org_list[orgs],
                                      computer['attributes']['dNSHostName'])
            self.add_group(group="all",
                                       children=[])


    def add_host(self, group, host):
        group = "all"
        host = (''.join(host)).lower()
        if group not in self.inventory.keys():
            self.inventory[group] = {'hosts': []}
        self.inventory[group]['hosts'].append(host)

    def add_group(self, group, children):
        children = (''.join(children)).lower()
        if group not in self.inventory.keys():
            self.inventory[group] = {'hosts': []}

    def add_vars(self):
        self.inventory['all']['vars'] = {}
        self.inventory['all']['vars']['ansible_port'] = 5985
        self.inventory['all']['vars']['ansible_winrm_scheme'] = 'http'
        self.inventory['all']['vars']['ansible_connection'] = 'winrm'
        self.inventory['all']['vars']['ansible_winrm_transport'] = 'kerberos'

if __name__ == '__main__':
    ADAnsibleInventory()
