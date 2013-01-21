#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Utility classes and functions

Created by: Rui Carmo
License: MIT (see LICENSE for details)
"""

import os, sys, time, re, subprocess, urllib, urllib2
import json, xml.dom.minidom
import socket, fcntl, struct

# URL shortener cache
_cache = {}

class JSONStruct:
  """Recursively build objects from a dict."""

  def __init__(self, obj):
    for k, v in obj.iteritems():
      if isinstance(v, dict):
        setattr(self, k, JSONStruct(v))
      else:
        setattr(self, k, v)

  def __getitem__(self, val):
    return self.__dict__[val]

  def __item_repr__(self, item):
    if type(item) in [list]:
        return '[%s]' % ','.join(map(lambda x: self.__item_repr__(x), item))
    elif type(item) in [str,unicode]:
        return '"%s"' % item
    return repr(item)

  def __repr__(self):
    return '{%s}' % str(', '.join('"%s": %s' % (k, self.__item_repr__(v)) for (k, v) in self.__dict__.iteritems()))


class InMemoryHandler(logging.Handler):
    """In memory logging handler with a circular buffer"""

    def __init__(self, limit=8192):
            # run the regular Handler __init__
            logging.Handler.__init__(self)
            # Our custom arguments
            self.limit = limit
            self.flush()

    def emit(self, record):
            # record.message is the log message
            self.records.append(record.message)
            if len(self.records) > self.limit:
                self.records.pop()

    def flush(self):
        self.records = []

    def dump(self):
        return records


def shorten(url):
    """Minimalist URL shortener using SAPO services"""
    if url not in _cache:
        u = '?'.join(('http://services.sapo.pt/PunyURL/GetCompressedURLByURL',urllib.urlencode({'url':url})))
        try:
            x = xml.dom.minidom.parseString(urllib2.urlopen(u).read())
            _cache[url] = x.getElementsByTagName('ascii')[0].firstChild.data
        except:
            _cache[url] = url
    return _cache[url]


def valid_mac_address(addr):
    """Validate a physical Ethernet address"""
    return re.match("[0-9a-f]{2}([-:][0-9a-f]{2}){5}$", addr.lower())


def valid_ip_address(addr):
    """Quick and dirty way to validate any kind of IP address"""
    try:
        socket.inet_aton(addr)
        return True
    except socket.error:
        return False


def get_pid_stats(pid):
    """Retrieve process kernel counters"""
    stats = open('/proc/%d/status' % pid,'r').readlines()
    return dict(filter(lambda x: len(x)==2,map(lambda x: x.split()[:2],stats)))


def get_pid_rss(pid):
    """Retrieve a process' resident set size"""
    try:
        return int(get_pid_stats(pid)['VmRSS:'])
    except:
        return 0


def get_net_bytes(dev='eth0'):
    """Read network interface traffic counters"""
    return {
        'rx': float(open('/sys/class/net/%s/statistics/rx_bytes' % dev,'r').read().strip()),
        'tx': float(open('/sys/class/net/%s/statistics/tx_bytes' % dev,'r').read().strip())
    }


def get_cpu_stat():
    cpu = open('/proc/stat','r').readlines()[0]
    return map(float,cpu.split()[1:5])


def get_cpu_usage(interval=0.1):
    """Estimates overall CPU usage during a short time interval"""
    t1 = get_cpu_stat()
    time.sleep(interval)
    t2 = get_cpu_stat() 
    delta = [t2[i] - t1[i] for i in range(len(t1))]
    try:
        return 1.0 - (delta[-1:].pop()/(sum(delta)*1.0))
    except: 
        return 0.0


def get_cpu_freq(cpu='cpu0'):
    """Retrieves the current CPU speed in MHz - for a single CPU"""
    return float(open('/sys/devices/system/cpu/%s/cpufreq/scaling_cur_freq' % cpu,'r').read().strip())/1000.0


def get_cpu_temp(cpu='cpu0'):
    """Retrieves the current CPU core temperature in degrees Celsius - specific to the Raspberry Pi"""
    return float(open('/sys/class/thermal/thermal_zone%s/temp' % cpu[-1],'r').read().strip())/1000.0


def get_uptime():
    """Retrieves the system uptime, in seconds"""
    return float(open('/proc/uptime', 'r').read().split(' ')[0])


def get_mac_address(dev="eth0"):
    """Retrieves the MAC address from the /sys virtual filesystem - will only work on Linux."""
    return open('/sys/class/net/%s/address' % dev,'r').read().strip()


def get_ip_address(dev="eth0"):
    """Retrieves the IP address via SIOCGIFADDR - only tested on Linux."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(s.fileno(),0x8915,struct.pack('256s', dev[:15]))[20:24])
    except:
        return None


def get_config(filename):
    """Parses the configuration file."""
    try:
        config = JSONStruct(json.load(open(filename, 'r')))
    except Exception, e:
        print 'Error loading configuration file %s: %s' % (filename, e)
        sys.exit(2)
    return config


def path_for(name):
    """Build relative paths to current script"""
    return os.path.join(os.path.dirname(sys.argv[0]),name)