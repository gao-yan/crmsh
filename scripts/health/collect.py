#!/usr/bin/env python
import os
import hashlib
import platform
import crm_script
data = crm_script.get_input()

PACKAGES = ['booth', 'cluster-glue', 'corosync', 'crmsh', 'csync2', 'drbd',
            'fence-agents', 'gfs2', 'gfs2-utils', 'ha-cluster-bootstrap',
            'haproxy', 'hawk', 'libdlm', 'libqb', 'ocfs2', 'ocfs2-tools',
            'pacemaker', 'pacemaker-mgmt', 'resource-agents', 'sbd']

def rpm_info():
    return crm_script.rpmcheck(PACKAGES)

def logrotate_info():
    rc, _, _ = crm_script.call(
        'grep -r corosync.conf /etc/logrotate.d',
        shell=True)
    return {'corosync.conf': rc == 0}

def sys_info():
    sysname, nodename, release, version, machine = os.uname()
    #The first three columns measure CPU and IO utilization of the
    #last one, five, and 15 minute periods. The fourth column shows
    #the number of currently running processes and the total number of
    #processes. The last column displays the last process ID used.
    system, node, release, version, machine, processor = platform.uname()
    distname, distver, distid = platform.linux_distribution()
    hostname = os.uname()[1]

    uptime = open('/proc/uptime').read().split()
    loadavg = open('/proc/loadavg').read().split()

    return {'system': system,
            'node': node,
            'release': release,
            'version': version,
            'machine': machine,
            'processor': processor,
            'distname': distname,
            'distver': distver,
            'distid': distid,
            'user': os.getlogin(),
            'hostname': hostname,
            'uptime': uptime[0],
            'idletime': uptime[1],
            'loadavg': loadavg[2]  # 15 minute average
            }

def disk_info():
    rc, out, err = crm_script.call(['df'], shell=False)
    if rc == 0:
        disk_use = []
        for line in out.split('\n')[1:]:
            line = line.strip()
            if line:
                data = line.split()
                if len(data) >= 6:
                    disk_use.append((data[5], data[4]))
        return disk_use
    return []

# configurations out of sync

FILES = [
    '/etc/csync2/key_hagroup',
    '/etc/csync2/csync2.cfg',
    '/etc/corosync/corosync.conf',
    '/etc/sysconfig/sbd',
    '/etc/sysconfig/SuSEfirewall2',
    '/etc/sysconfig/SuSEfirewall2.d/services/cluster'
    ]


def files_info():
    ret = {}
    for f in FILES:
        if os.path.isfile(f):
            try:
                ret[f] = hashlib.sha1(open(f).read()).hexdigest()
            except IOError, e:
                ret[f] = "error: %s" % (e)
        else:
            ret[f] = ""
    return ret


try:
    data = {
        'rpm': rpm_info(),
        'logrotate': logrotate_info(),
        'system': sys_info(),
        'disk': disk_info(),
        'files': files_info()
    }
    crm_script.exit_ok(data)
except Exception, e:
    crm_script.exit_fail(str(e))
