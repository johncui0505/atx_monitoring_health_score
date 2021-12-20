#!/bin/python3

import json
import sys, getopt

PATH = "roles/monitor_health/files/"

def getTopologyHealth():
    with open(PATH + "health_topology.json") as json_file:
        raw_data = json.load(json_file)
    return len(raw_data['results'][0]['imdata'])

def getTenantHealth():
    with open(PATH + "health_tenant.json") as json_file:
        raw_data = json.load(json_file)
    return len(raw_data['results'][0]['imdata'])

def main():
    if getTopologyHealth() > 0 or getTenantHealth() > 0:
        print("true", end='')
    else:
        print("false", end='')

if __name__ == "__main__":
    main()