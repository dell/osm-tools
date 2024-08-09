Overview:
The NVMe drive LED control script is designed to visually identify any failed or predicted to fail E3.S NVMe drives on Dell PowerEdge R670 and R770 CSP Edition servers.

Prerequisite:
Dell PowerEdge R670 or R770 CSP Edition with Open Server Manager (OSM).
Host OS running a Linux based distro.
nvme-cli and ipmitool packages installed.
root user or sudo access.

Details:
The script is intended to be run on a Linux based Host OS installed on the Dell PowerEdge R670 / R770 CSP Edition servers. The script iterates through every installed NVMe drive in the system (nvme list) and checks for its health using nvme smart-log. Critical warnings are mapped to a state and the status LED would be set to indicate the state as below:

|-------------------------------|-------------------|----------------------|
| nvme-cli Critical Warning Bit | State             | Status LED           |
|-------------------------------|-------------------|----------------------|
| pmr_ro                        | Failed            | Blinking Amber       |
|-------------------------------|-------------------|----------------------|
| vmbu_failed                   | Failed            | Blinking Amber       |
|-------------------------------|-------------------|----------------------|
| reliability_degraded          | Failed            | Blinking Amber       |
|-------------------------------|-------------------|----------------------|
| ro                            | Failed            | Blinking Amber       |
|-------------------------------|-------------------|----------------------|
| available_spare               | Predicted Failure | Blinking Blue/ Amber |
|-------------------------------|-------------------|----------------------|
| temp_threshold                | Healthy           | N/A                  |
|-------------------------------|-------------------|----------------------|

Typical Usage:
sudo ./nvmeLedControl.py
Dell recommends to run this script periodically through an infrastructure like cron so any failed drives can be identified visually during a service dispatch.
Note that the status LED will be reset when the drive is pulled out. It will not be set again even if the fault persists until the script gets a chance to run again. So removing a failed drive and putting the same drive back in will give a false status that would suggest the drive is healthy.

Alternate usage for drive identification:
The script can also be used to ‘identify’ a particular drive that would blink the Status LED blue. Bus number and segment number are required to use the identify option. The identify status is a user requested status and prioritized over a fault/ predicted fault state. bus/ segment number are considered decimal inputs unless prefixed with ‘0x’ in which case they are interpreted as hexadecimal.

The identify status LED will get cleared if the drive is plugged out or if the clear option is used for the drive.

sudo ./nvmeLedControl.py --help
usage: nvmeLedControl.py [-h] [--segment SEGMENT] [--bus BUS] [--identify | --clear] [--device DEVICE] 

optional arguments:
  -h, --help            show this help message and exit
  --segment SEGMENT, -s SEGMENT
                        Segment group number (use nvme show-topology to find)
  --bus BUS, -b BUS     Bus number (use nvme show-topology to find)
  --device DEV, -d DEV  NVMe device (nvmeX, use nvme list to find)
  --identify, -i        Identify command
  --clear, -c           Clear command
