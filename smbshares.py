# -*- coding: utf-8 -*-
"""Various classes & functions I use in different places

    SMBShares: Class to retrieve network SMB shares and local drives
"""
__version_info__ = (0, 0, 1)
__version__ = '.'.join(map(str, __version_info__))

import concurrent.futures
from socket import gethostbyaddr, getdefaulttimeout, setdefaulttimeout
from win32net import NetShareEnum
from win32api import GetLogicalDriveStrings


class SMBShares:
    """Class to retrieve network SMB shares and local drives

        new_class=SMBShares(root='192.168.0', first=1, last=255         # root of ip and range to search
    attr:
        drive_list                # list of locally mapped drives ['C:','D:',...]
        machine_info              # Dict of info for addresses with data share keyed by IP
        shares_list               # List of shares formatted as \\server\share
        
    info:
        ip range is max of 255 addresses
    """

    def __init__(self, root: str ='192.168.0', first: int = 1, last: int = 254, timeout:float = 2):
        # Generate list of all possible addresses
        nodes = list('{}.{}'.format(root, str(i)) for i in range(first, last + 1))
        # Dict of all responding addresses
        self.active_nodes = {}
        netbios = set()
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(nodes)) as executor:
            sock_timeout = getdefaulttimeout()
            setdefaulttimeout(1)
            _names = {executor.submit(self._get_names, address): address for address in nodes}
            setdefaulttimeout(sock_timeout)
            try:
                for future in concurrent.futures.as_completed(_names, timeout=timeout):
                    _name = _names[future]
                    try:
                        data = future.result()
                    except Exception as exc:
                        print('%r generated an exception: %s' % (_name, exc))
                    else:
                        if data[1]:
                            if data[1][0].split('.')[0].upper() not in netbios:
                                netbios.add(data[1][0].split('.')[0].upper())
                                self.active_nodes[data[0]] = data[1]
            except concurrent.futures.TimeoutError:
                pass
            
        # Dict of info for addresses with data shares
        self.machines_info = {}
        # List of shares formatted as \\server\share
        self.shares_list = []
        # list of drives
        self.drives_list = [letter[0:2] for letter in GetLogicalDriveStrings().split('\x00') if letter != '']

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.active_nodes)) as executor:
            _shares = {executor.submit(self._get_shares, node): node for node in self.active_nodes.keys()}
            try:
                for future in concurrent.futures.as_completed(_shares, timeout=timeout):
                    _share = _shares[future]
                    try:
                        data = future.result()
                    except Exception as exc:
                        print('%r generated an exception: %s' % (_share, exc))
                    else:
                        if data[3]:
                            self.machines_info[data[0]] = [data[1], data[2]]
                            for share in data[3]:
                                self.shares_list.append(f'\\\\{data[1]}\{share}')
            except concurrent.futures.TimeoutError:
                pass

       
    def _get_names(self, node:str) -> tuple:

        try:
            return node, gethostbyaddr(node)
        except Exception as e:
            return node, ()
    
    def _get_shares(self, node:str) -> list:
        name = 'timed_out'
        try:
            name = self.active_nodes[node][0]
            info = NetShareEnum(name, 1)
            local_shares = list(local_share['netname'] for local_share in info[0] if
                                local_share['type'] == 0 and
                                local_share['netname'].lower() not in ['netlogon', 'sysvol'] and not
                                local_share['netname'].endswith('$'))
            # if local_shares:
            #     self.machines_info[node] = [name, info]
            #     for share in local_shares:
            #         self.shares_list.append(f'\\\\{name}\{share}')
            return [node, name, info, local_shares]

        except Exception as e:
            return [node, name, {}, []]

    
    def get_drive_list(self):
        return list(letter[0:2] for letter in GetLogicalDriveStrings().split('\x00') if letter != '').sort()
    
    def get_machine_list(self):
        return self.machines_info
    
    def get_shares_list(self):
        return self.shares_list

_enum = SMBShares()
drives_list = _enum.drives_list
machines_info = _enum.machines_info
shares_list = _enum.shares_list
active_nodes = _enum.active_nodes

if __name__ == '__main__':
    #enum_net = SMBShares(timeout=5)
    print(drives_list)
    for k, v in active_nodes.items():
        print(f'{k} = {v}')
    for k, v in machines_info.items():
        print(f'{k} = {v[0]} total of {v[1][1]}shares')
        for share in v[1][0]:
            print(f'\t{share}')
    for share in shares_list:
        print(share)

