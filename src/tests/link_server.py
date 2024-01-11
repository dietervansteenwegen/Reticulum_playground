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

latest_client_link = None  # A reference to the latest client link that connected


def init_server(configpath):
    reticulum = RNS.Reticulum(configpath)
    # server_identity = RNS.Identity()  # Randomly create a new identity for our link example
    server_identity = RNS.Identity.from_file('identity_file')
    # server_identity.to_file('identity_file')
    # We create a destination that clients can connect to. We
    # want clients to create links to this destination, so we
    # need to create a 'single' destination type.
    server_destination = RNS.Destination(server_identity, RNS.Destination.IN,
                                         RNS.Destination.SINGLE, APP_NAME, 'linkexample')

    # We configure a function that will get called every time
    # a new client creates a link to this destination.
    server_destination.set_link_established_callback(client_connected)

    # Let's Wait for client requests or user input
    server_loop(server_destination)


def server_loop(destination):
    # Let the user know that everything is ready
    RNS.log(f'Link example running with hash {RNS.prettyhexrep(destination.hash)}, '
            'waiting for a connection.')

    RNS.log('Hit enter to manually send an announce (Ctrl-C to quit)')

    # We enter a loop that runs until the users exits.
    while True:
        _ = input()
        destination.announce()
        RNS.log(f'Sent announce from {RNS.prettyhexrep(destination.hash)}')


def client_connected(link):
    # When a client establishes a link to our server
    # destination, this function will be called with
    # a reference to the link.
    global latest_client_link

    RNS.log('Client connected')
    link.set_link_closed_callback(client_disconnected)
    link.set_packet_callback(server_packet_received)
    latest_client_link = link


def client_disconnected(link):
    RNS.log('Client disconnected')


def server_packet_received(message, packet):
    global latest_client_link

    # When data is received over any active link,
    # it will all be directed to the last client
    # that connected.
    RNS.log(f'Received data on the link: {message.decode("utf-8")}')

    reply = f'I received  [{message.decode("utf-8")}] over the link {latest_client_link}.'
    RNS.Packet(latest_client_link, reply.encode('utf-8')).send()


if __name__ == '__main__':
    print("""
    ##########################################################
    #### Server Startup #####################################
    ##########################################################
    """)
    try:
        parser = argparse.ArgumentParser(description='Simple link example')

        parser.add_argument('--config',
                            action='store',
                            default=None,
                            help='path to alternative Reticulum config directory',
                            type=str)

        args = parser.parse_args()

        init_server(args.config)

    except KeyboardInterrupt:
        print('CTRL + C from keyboard, exiting.')
        exit()
