import datetime
from socket import *

from sportorg.utils.time import time_to_hhmmss

"""
Format of WDB data package
 - length is 1772 bytes
 1) 36b text block at the beginning
       2      4132500 0 0      3974600\n
 bib - finish_time - disqual_status - 0 - start_time

 2) binary part
 bytes 128-131 - card number
 bytes 136-139 - qty of punches
 bytes 144-147 - start in card
 bytes 152-155 - finish in card

 starting from b172: 8b blocks * 200
    - byte 1     control number
    - bytes 4-7  punch time

"""


def int_to_time(value):
    """ convert value from 1/100 s to time """
    today = datetime.datetime.now()
    ret = datetime.datetime(
        today.year,
        today.month,
        today.day,
        value // 360000 % 24,
        (value % 360000) // 6000,
        (value % 6000) // 100,
        (value % 100) * 10000,
    )

    return ret


host = 'localhost'
port = 1212
addr = (host, port)


udp_socket = socket(AF_INET, SOCK_DGRAM)
udp_socket.bind(addr)

# main loop
while True:

    print('wait data...')

    # recvfrom - receiving of data
    conn, addr = udp_socket.recvfrom(1772)
    print('client addr: ', addr)
    print('data: ', conn)

    # string = ''
    # for i in conn:
    #     string += str( hex(i)) + '-'
    # print(string)

    text_array = bytes(conn[0:34]).decode().split()
    bib = text_array[0]
    result = int_to_time(int(text_array[1]))
    status = text_array[2]
    start = int_to_time(int(text_array[4]))
    byteorder = 'little'

    punch_qty = int.from_bytes(conn[136:140], byteorder)
    card_start = int_to_time(int.from_bytes(conn[144:148], byteorder))
    card_finish = int_to_time(int.from_bytes(conn[152:156], byteorder))

    init_offset = 172
    punches = []
    for i in range(punch_qty):
        cp = int.from_bytes(
            conn[init_offset + i * 8 : init_offset + i * 8 + 1], byteorder
        )
        time = int_to_time(
            int.from_bytes(
                conn[init_offset + i * 8 + 4 : init_offset + i * 8 + 8], byteorder
            )
        )
        punches.append((cp, time_to_hhmmss(time)))

    print('bib=' + bib + ' result=' + time_to_hhmmss(result) + ' punches=')
    print(punches)

    # sendto - responce
    udp_socket.sendto(b'message received by the server', addr)

# udp_socket.close()
