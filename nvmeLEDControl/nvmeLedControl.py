#!/usr/bin/python3

#
# Copyright © 2024-2025 Dell Inc. or its subsidiaries. All Rights Reserved.
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the Dell, Inc. nor the
#      names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL Dell, Inc. BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

# This script, `nvmeLedControl.py`, is used for blinking the LED of a NVMe drive using IPMI commands.
# Without any arguments, it will iterate over the nvme drives available
# and blink the corresponding led based on the status.
# For a faulty drive, blink amber and for predictive failure, blink blue amber.
# Also takes the (segment and bus number) or (device name) as arguments ((--segment/-s and --bus/-b) or --device/-d)
# along with the identify or clear command (--identify/-i or --clear/-c).
# When --identify is sent to a drive which is faulty or in predictive failure,
# the user input takes precedence and led blinks blue.
# Segment and bus number can be hexadecimal or decimal values.


import json
import subprocess
from collections import namedtuple
import re
import argparse
import sys

def nvme_blink(deviceName, segment, bus, dr_state_data_hex_value, dr_state):
    bay_hex_value, slot_hex_value = get_bay_slot(segment,bus)
    critical_warning_attr = get_critical_warning_attr(deviceName)
    if (dr_state_data_hex_value is None and dr_state is None):
        if critical_warning_attr in ["pmr_ro", "vmbu_failed", "reliability_degraded", "ro"]:
            dr_state = "CritWarning: "+critical_warning_attr+" | State: Fault | StatusLED: blink amber"
            drive_state_data = 0x20
        elif critical_warning_attr in ["available_spare"]:
            dr_state = "CritWarning: "+critical_warning_attr+" | State: Predictive Failure | StatusLED: blink blue amber"
            drive_state_data = 0x40
        else:
            dr_state = 'None'
            drive_state_data = 0x00

        hex_value = format(drive_state_data, 'x')
        dr_state_data_hex_value = '0x' + format(int(hex_value, 16), '02x')
        if dr_state_data_hex_value != '0x00':
            bl_output = blink_led(bay_hex_value,slot_hex_value,dr_state_data_hex_value)
            if bl_output != None:
                print('Drive ' + deviceName + ': bay ' + bay_hex_value + ', slot ' + slot_hex_value + '. ' + dr_state)
    else:
        hex_value = format(dr_state_data_hex_value, 'x')
        dr_state_data_hex_value = '0x' + format(int(hex_value, 16), '02x')
        bl_output = blink_led(bay_hex_value,slot_hex_value,dr_state_data_hex_value)
        if bl_output != None:
            print('Drive ' + deviceName + ': bay ' + bay_hex_value + ', slot ' + slot_hex_value  + '. CritWarning: '+critical_warning_attr+' | ' + dr_state)

def exec_command(command):
    output = subprocess.check_output(command).decode('utf-8')
    return json.loads(output)

def exec_ipmi_command(command):
    try:
        output = subprocess.check_output(command).decode('utf-8')
        return output
    except subprocess.CalledProcessError as e:
        print(f"Check if the arguments passed are correct")
        exit(1)

def get_bay_slot(segment, bus):
    # Convert segment and bus values to hex
    seg_hex_value = '0x' + format(int(segment, 16), '02x')
    bus_hex_value = '0x' + format(int(bus, 16), '02x')

    # Run the 0x37 command to get the bay and slot id for the bus and segment passed
    get_bay_slot_cmd = ['ipmitool', 'raw', '0x30', '0xd5', '0x01', '0x37', '0x06', '0x00', '0x00', '0x00', bus_hex_value, seg_hex_value]
    output_str = exec_ipmi_command(get_bay_slot_cmd)
    values = output_str.split()
    # Assign the values for bay_id and slot_id
    bayid, slotid = ('00', '00') if len(values) < 8 else (values[7], values[8])
    bay_hex_value = '0x' + format(int(bayid, 16), '02x')
    slot_hex_value = '0x' + format(int(slotid, 16), '02x')
    return bay_hex_value, slot_hex_value

def get_critical_warning_attr(deviceName):
    # Command to get the nvme smart-log data
    smart_log_cmd = ['nvme', 'smart-log', '-H', f"/dev/{deviceName}", '-o', 'json']
    smartLogData = exec_command(smart_log_cmd)

    critical_warning_attr = ' - '
    critical_warning_attributes = smartLogData["critical_warning"]
    for attribute, value in critical_warning_attributes.items():
        if value == 1:
            critical_warning_attr = attribute
    return critical_warning_attr

def blink_led(bay_hex_value, slot_hex_value, dr_state_data_hex_value):
    blink_led_cmd = ['ipmitool', 'raw', '0x30', '0xd5', '0x00', '0x34', '0x0e', '0x00', '0x00', '0x00', '0x0e', '0x00', bay_hex_value, slot_hex_value, dr_state_data_hex_value, '0x00', '0x00', '0x00','0x00', '0x00', '0x00','0x00', '0x00', '0x00']
    output_str = exec_ipmi_command(blink_led_cmd)
    pass
    return output_str

def get_device_name(segment_number, bus_number):
    # Format the values as '0000:00'
    segment_value = segment_number.zfill(4)
    bus_value = bus_number.zfill(2)
    formatted_value = f"{segment_value}:{bus_value}"
    # Command to get the nvme topo data
    show_topo_cmd = ['nvme', 'show-topo', '-o', 'json']
    data = exec_command(show_topo_cmd)
    # Get device name based on segment_number:bus_number
    for subsystem in data[0]['Subsystems']:
        for namespace in subsystem['Namespaces']:
            try:
                for path in namespace['Paths']:
                    if 'Address' in path and path['Address'].startswith(formatted_value):
                        deviceName = path['Name']
                        return deviceName
            except KeyError:
                pass
            try:
                for path in namespace['Controller']:
                    if 'Address' in path and path['Address'].startswith(formatted_value):
                        deviceName = path['Name']
                        return deviceName
            except KeyError:
                pass

def get_hex_value(input_value):
    if input_value.startswith('0x'):
        return_val = int(input_value, 16)
    else:
        return_val = int(input_value)
    ret_hex_value = hex(return_val)[2:]
    return ret_hex_value

# Code flow starts here. Process the arguments if any, else continue
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--segment', '-s', type=str, help='Segment group number')
    parser.add_argument('--bus', '-b', type=str, help='Bus number')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--identify', '-i', action='store_true', help='Identify command')
    group.add_argument('--clear', '-c', action='store_true', help='Clear command')
    parser.add_argument('--device', '-d', type=str, help='Device Name')
    args = parser.parse_args()
    if (args.segment or args.bus) and not (args.segment and args.bus):
        print('Both segment and bus number are required')
        exit(1)
    if (args.segment is not None and args.bus is not None) or (args.device is not None):
        if not (args.identify or args.clear):
            print('--identify/-i or --clear/-c is required')
            exit(1)
        if args.identify:
            dr_state = 'State: Identify | StatusLED: blink blue'
            drive_state_data = 0x08
        else:
            dr_state = 'State: Clear | StatusLED: clear'
            drive_state_data = 0x00
        if (args.segment is not None and args.bus is not None):
            seg_hex_value = get_hex_value(args.segment)
            bus_hex_value = get_hex_value(args.bus)
            deviceName = get_device_name(seg_hex_value, bus_hex_value)
            nvme_blink(deviceName, seg_hex_value, bus_hex_value, drive_state_data, dr_state)
            sys.exit()
        else:
            pass
    else:
        drive_state_data = None
        dr_state = None
        pass

# Command to get the nvme topo data
show_topo_cmd = ['nvme', 'show-topo', '-o', 'json']
data = exec_command(show_topo_cmd)

for subsystem in data[0]['Subsystems']:
    for namespace in subsystem['Namespaces']:
        try:
            for path in namespace['Paths']:
                deviceName = path['Name']
                if args.device is not None and deviceName != args.device:
                    continue
                segment = path['Address'].split(':')[0]
                bus = path['Address'].split(':')[1]
                nvme_blink(deviceName, segment, bus, drive_state_data, dr_state)

        except KeyError:
            pass
        try:
            for controller in namespace['Controller']:
                deviceName = controller['Name']
                if args.device is not None and deviceName != args.device:
                    continue
                segment = controller['Address'].split(':')[0]
                bus = controller['Address'].split(':')[1]
                nvme_blink(deviceName, segment, bus, drive_state_data, dr_state)

        except KeyError:
            pass