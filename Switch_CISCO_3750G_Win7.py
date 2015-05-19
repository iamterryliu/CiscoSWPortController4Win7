import os
import sqlite3
import telnetlib
import re
import base64
import ConfigParser
import collections
import time

HOST = None
USERNAME = None
PASSWORD = None
DATAFile = None
WAIT = 0.2

clear = lambda: os.system('cls')


def Init():
    clear()
    cfg = ConfigParser.ConfigParser()
    cfg.read("Switch_CISCO_3750G.ini")
    global HOST
    HOST = cfg.get("Switch_CISCO_3750G", "HOST")
    global USERNAME
    USERNAME = base64.b64decode(cfg.get("Switch_CISCO_3750G", "USERNAME"))
    global PASSWORD
    PASSWORD = base64.b64decode(cfg.get("Switch_CISCO_3750G", "PASSWORD"))
    global DATAFile
    DATAFile = cfg.get("Switch_CISCO_3750G", "DATAFile")


def setVlanToPort(eth_no, vlan):
    telnet = telnetlib.Telnet(HOST)

    telnet.read_until("Username:")
    time.sleep(WAIT)
    telnet.write(USERNAME + "\n")
    telnet.read_until("Password:")
    time.sleep(WAIT)
    telnet.write(PASSWORD + "\n")
    time.sleep(WAIT)

    telnet.read_until("Switch#")
    cisco_cli = "configure terminal\n"
    time.sleep(WAIT)
    telnet.write(cisco_cli.encode("utf-8"))
    telnet.read_until("Switch(config)#")
    cisco_cli = "interface " + eth_no + "\n"
    time.sleep(WAIT)
    telnet.write(cisco_cli.encode("utf-8"))
    telnet.read_until("Switch(config-if)#")
    cisco_cli = "switchport access vlan " + vlan + "\n"
    time.sleep(WAIT)
    telnet.write(cisco_cli.encode("utf-8"))
    time.sleep(WAIT)
    telnet.write("exit\n")
    time.sleep(WAIT)
    telnet.write("exit\n")
    telnet.close()


def getVLAN_ID(port):
    telnet = telnetlib.Telnet(HOST)

    telnet.read_until("Username:")
    time.sleep(WAIT)
    telnet.write(USERNAME + "\n")
    telnet.read_until("Password:")
    time.sleep(WAIT)
    telnet.write(PASSWORD + "\n")
    time.sleep(WAIT)

    telnet.read_until("Switch#")
    cisco_cli = "show interface " + port + " status\n"
    time.sleep(WAIT)
    telnet.write(cisco_cli.encode("utf-8"))
    time.sleep(WAIT)
    telnet.write("exit" + "\n")
    result = telnet.read_all()
    telnet.close()

    strTest = re.compile(r'Gi\d+/\d+/\d+\s+\w+\W*\w+\s+\d+')
    ethInfo = strTest.findall(result)[0].split()
    return ethInfo[3]


def updateInfo(user):
    conn = sqlite3.connect(DATAFile)
    cur = conn.cursor()
    sql = "SELECT DISTINCT port FROM v_user_port_mapping where user='" + user + "';"
    for row in cur.execute(sql):
        port = row[0]
        vlan = getVLAN_ID(port)
        sql = "UPDATE port_map SET vlan=" + vlan + " WHERE port='" + port + "';"
        conn.execute(sql)
    conn.commit()
    conn.close()
    print("Updated database successfully\n\n")


def getAllUser():
    users = []
    conn = sqlite3.connect(DATAFile)
    cur = conn.cursor();
    for row in cur.execute('''SELECT DISTINCT USER FROM v_user_port_mapping'''):
        users.append(row[0])
    conn.close()
    return users


def checkNone(str_test):
    not_None = " "
    if str_test is not None:
        return str_test
    return not_None


def getVLANMapping():
    vlan_detail = {}
    conn = sqlite3.connect(DATAFile)
    cur = conn.cursor();
    sql = "SELECT * FROM vlan_mapping;"
    user_ports_row = cur.execute(sql)
    for row in user_ports_row:
        description = checkNone(row[1])
        vlan_detail[str(row[0])] = description
    conn.close()
    return vlan_detail


def getPortDetails(user):
    ports_detail = {}
    conn = sqlite3.connect(DATAFile)
    cur = conn.cursor()
    sql = "SELECT eth_no, description, port FROM v_user_port_mapping where user='" + user + "';"
    user_ports_row = cur.execute(sql)
    for row in user_ports_row:
        description = checkNone(row[1])
        ports_detail[row[0]] = description + "#####" + row[2]
    conn.close()
    return ports_detail


def isNumber(user_in_no):
    isNumber = 1
    for c_int in user_in_no:
        if (ord(c_int) <= 47 or ord(c_int) >= 58):
            isNumber = 0
    return isNumber


def main():
    Init()
    users = getAllUser()

    user_no = None
    while 1:
        print 'No\tUser'
        print '=========='
        for i in range(len(users)):
            print str(i) + "=\t" + users[i]

        print "\n(Please enter q/Q to quit)"
        user_in_no = raw_input("Choose a user ==>")

        if len(user_in_no) > 0:
            if isNumber(user_in_no):
                if int(user_in_no) + 1 <= len(users):
                    updateInfo(users[int(user_in_no)])
                    break
            else:
                exit()

    eth_no = None
    user_in_port_no = None
    while 1:
        print "User:: ", users[int(user_in_no)]
        ports_detail = getPortDetails(users[int(user_in_no)])
        print 'Port \tDescription'
        print '=============================='
        for key in ports_detail.keys():
            print key[0:], '=\t', ports_detail[key].split("#####")[0]

        print "\n(Please enter q/Q to quit)"
        user_in_port_no = raw_input("[Modify] Choose a port ==>")

        if len(user_in_port_no) > 0:
            if isNumber(user_in_port_no):
                if ports_detail.has_key(user_in_port_no):
                    eth_no = ports_detail[user_in_port_no].split("#####")[1]
                    break
            else:
                exit()

    user_in_vlan_no = None
    while 1:
        print "User:: ", users[int(user_in_no)], "\t Port::", user_in_port_no
        vlan_detail = collections.OrderedDict(sorted(getVLANMapping().items()))
        print 'VLAN \tDescription'
        print '=============================='
        for key in vlan_detail.keys():
            print key, '=\t', vlan_detail[key]

        print "\n(Please enter q/Q to quit)"
        user_in_vlan_no = raw_input("[Setup] Choose a vlan id ==>")

        if len(user_in_vlan_no) > 0:
            if isNumber(user_in_vlan_no):
                if vlan_detail.has_key(user_in_vlan_no):
                    break
            else:
                exit()

    print "Setup " + eth_no + " to vlan " + user_in_vlan_no + "."
    setVlanToPort(eth_no, user_in_vlan_no)
    updateInfo(users[int(user_in_no)])
    ports_detail = getPortDetails(users[int(user_in_no)])
    print "Has completed the setting."
    print "User:: ", users[int(user_in_no)]
    print 'Port \tDescription'
    print '=============================='
    for key in ports_detail.keys():
        print key[0:], '=\t', ports_detail[key].split("#####")[0]
    print "\nIf you have any questions, please notify Terry Liu."
    print "Thx, bye bye ~~~"


if __name__ == '__main__':
    main()