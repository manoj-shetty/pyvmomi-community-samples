#!/usr/bin/env python
from pyVmomi import vim
from pyVmomi import vmodl
from tools import tasks
from pyVim.connect import SmartConnectNoSSL, Disconnect
import atexit
import argparse
import getpass


def get_args():
    parser = argparse.ArgumentParser(
        description='Arguments for talking to vCenter')

    parser.add_argument('-s', '--host',
                        required=True,
                        action='store',
                        help='vSpehre service to connect to')

    parser.add_argument('-o', '--port',
                        type=int,
                        default=443,
                        action='store',
                        help='Port to connect on')

    parser.add_argument('-u', '--user',
                        required=True,
                        action='store',
                        help='User name to use')

    parser.add_argument('-p', '--password',
                        required=False,
                        action='store',
                        help='Password to use')

    parser.add_argument('-v', '--vm-name',
                        required=False,
                        action='store',
                        help='name of the vm')

    parser.add_argument('--uuid',
                        required=False,
                        action='store',
                        help='vmuuid of vm')

    parser.add_argument('--port_number',
                        required=True,
                        action='store',
                        help='port group to connect on')

    args = parser.parse_args()

    if not args.password:
        args.password = getpass.getpass(
            prompt='Enter password')

    return args


def get_obj(content, vimtype, name):
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
    return obj


def add_serial_port(si, vm, port_number):
    """
    :param si: Service Instance
    :param vm: Virtual Machine Object
    :param port_number: Serial port number
    """
    spec = vim.vm.ConfigSpec()
    spec.deviceChange = []
    serial_spec = vim.vm.device.VirtualDeviceSpec()
    serial_spec.operation = 'add'
    serial_port = vim.vm.device.VirtualSerialPort()
    serial_port.yieldOnPoll = True
    backing = serial_port.URIBackingInfo()
    backing.serviceURI = ('telnet://:' + port_number)
    backing.direction = 'server'
    serial_port.backing = backing
    serial_spec.device = serial_port
    spec.deviceChange.append(serial_spec)
    vm.ReconfigVM_Task(spec=spec)
    print("Serial PORT added")


def main():
    args = get_args()

    # connect this thing
    serviceInstance = SmartConnectNoSSL(
            host=args.host,
            user=args.user,
            pwd=args.password,
            port=args.port)
    # disconnect this thing
    atexit.register(Disconnect, serviceInstance)

    vm = None
    if args.uuid:
        search_index = serviceInstance.content.searchIndex
        vm = search_index.FindByUuid(None, args.uuid, True)
    elif args.vm_name:
        content = serviceInstance.RetrieveContent()
        vm = get_obj(content, [vim.VirtualMachine], args.vm_name)

    if vm:
        add_serial_port(serviceInstance, vm, args.port_number)
    else:
        print("VM not found")

# start this thing
if __name__ == "__main__":
    main()
