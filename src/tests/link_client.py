##########################################################
# This RNS example demonstrates how to set up a link to  #
# a destination, and pass data back and forth over it.   #
##########################################################

import os
import sys
import time
import argparse
import RNS

# Let's define an app name. We'll use this for all
# destinations we create.
APP_NAME = 'example_utilities'
##########################################################
#### Client Part #########################################
##########################################################

# A reference to the server link
server_link = None


def get_destination_hash(destination_hexhash: str) -> bytes:
    # We need a binary representation of the destination
    # hash that was entered on the command line
    try:
        print(type(destination_hexhash))
        dest_len = (RNS.Reticulum.TRUNCATED_HASHLENGTH // 8) * 2
        if len(destination_hexhash) != dest_len:
            raise ValueError(
                f'Destination length is invalid, must be {dest_len} hexadecimal characters'
                f' ({dest_len //2 } bytes).')

    except Exception:
        RNS.log('Invalid destination entered. Check your input!\n')
        exit()
    else:
        return bytes.fromhex(destination_hexhash)


def wait_for_path(destination_hash: bytes):
    # Check if we know a path to the destination
    if not RNS.Transport.has_path(destination_hash):
        RNS.log(
            'Destination is not yet known. Requesting path and waiting for announce to arrive...')
        RNS.Transport.request_path(destination_hash)
        while not RNS.Transport.has_path(destination_hash):
            print('Waiting for path...')
            time.sleep(0.1)


def client(destination_hexhash, configpath):

    RNS.Reticulum(configpath)  # First initialise Reticulum
    destination_hash = get_destination_hash(destination_hexhash)
    wait_for_path(destination_hash)

    # Recall the server identity
    server_identity = RNS.Identity.recall(destination_hash)

    # Inform the user that we'll begin connecting
    RNS.log('Establishing link with server...')

    # When the server identity is known, we set
    # up a destination
    server_destination: RNS.Destination = RNS.Destination(server_identity, RNS.Destination.OUT,
                                                          RNS.Destination.SINGLE, APP_NAME,
                                                          'linkexample')

    set_up_link(server_destination)

    client_loop()


def set_up_link(server_destination: RNS.Destination):
    link = RNS.Link(server_destination)

    link.set_packet_callback(client_packet_received)  # callback for when a packet is received
    link.set_link_established_callback(link_established)  # callback when link is established
    link.set_link_closed_callback(link_closed)  # callback when link is closed


def client_loop():
    global server_link

    # Wait for the link to become active
    while not server_link:
        RNS.log('Waiting for server link to become active.')
        time.sleep(0.1)

    should_quit = False
    while not should_quit:
        try:
            print('> ', end=' ')
            text = input()

            # Check if we should quit the example
            if text.lower() in ['quit', 'q', 'exit']:
                should_quit = True
                server_link.teardown()
                continue

            if text != '':  # If not, send the entered text over the link
                data = text.encode('utf-8')
                if len(data) <= RNS.Link.MDU:
                    RNS.Packet(server_link, data).send()
                else:
                    RNS.log(f'Cannot send this packet, the data size of {len(data)} bytes exceeds '
                            f'the link packet MDU of {RNS.Link.MDU} bytes.')

        except Exception as e:
            RNS.log(f'Error while sending data over the link: {e}')
            should_quit = True
            server_link.teardown()


def link_established(link):
    # We store a reference to the link
    # instance for later use
    global server_link
    server_link = link
    RNS.log('Link established with server, enter some text to send, or "quit" to quit')


def link_closed(link):
    if link.teardown_reason == RNS.Link.TIMEOUT:
        RNS.log('The link timed out, exiting now.')
    elif link.teardown_reason == RNS.Link.DESTINATION_CLOSED:
        RNS.log('The link was closed by the server, exiting now.')
    else:
        RNS.log('Link closed, exiting now.')

    RNS.Reticulum.exit_handler()
    time.sleep(1.5)
    sys.exit(0)


def client_packet_received(message, packet):
    text = message.decode('utf-8')
    RNS.log(f'Received data on the link: {text}. (Packet: {packet})')
    print('> ', end=' ')
    sys.stdout.flush()


if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser(description='Simple link example')
        parser.add_argument('--config',
                            action='store',
                            default=None,
                            help='path to alternative Reticulum config directory',
                            type=str)

        parser.add_argument('destination',
                            nargs='?',
                            default=None,
                            help='hexadecimal hash of the server destination',
                            type=str)
        print('''
    ##########################################################
    #### Client Startup #####################################
    ##########################################################
            ''')
        args = parser.parse_args()

        if args.destination is None:
            print('')
            parser.print_help()
            print('')
        else:
            client(args.destination, args.config or None)

    except KeyboardInterrupt:
        print('')
        exit()