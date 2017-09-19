from playground.network.packet import PacketType
from playground.network.packet.fieldtypes import UINT16, STRING, BUFFER, BOOL, ListFieldType
from playground.network.packet.fieldtypes.attributes import Optional
from playground.network.common import StackingProtocol, StackingTransport, StackingProtocolFactory
import logging
import time
import asyncio
import playground




class CourseIDPacket(PacketType):
    DEFINITION_IDENTIFIER = "lab2b.yliu.CourseID"
    DEFINITION_VERSION = "1.0"
    FIELDS = [
        ("cid", BUFFER) #course ID
    ]

class CourseNamePacket(PacketType):
    DEFINITION_IDENTIFIER = "lab2b.yliu.CourseName"
    DEFINITION_VERSION = "1.0"
    FIELDS = [
        ("cid", BUFFER), #course ID
        ("cname", STRING), #course name
        ("enrollmentlimit", UINT16({Optional:True})) #course enrollment limit
    ]

class RegisterPacket(PacketType):
    DEFINITION_IDENTIFIER = "lab2b.yliu.Register"
    DEFINITION_VERSION = "1.0"
    FIELDS = [
        ("sid", BUFFER), #student id
        ("cid", BUFFER), #course id
        ("waitlist", BOOL) #T for "if the class is full, add me to waitlist", F for "do not add me to waitlist"
    ]

class RegisterResultPacket(PacketType):
    DEFINITION_IDENTIFIER = "lab2b.yliu.RegisterResult"
    DEFINITION_VERSION = "1.0"
    FIELDS = [
        ("sid", BUFFER),  # student id
        ("cid", BUFFER),  # course id
        ("result", STRING)  # enrolled, waitlist, failed
    ]

class PassThroughOneProtocol(StackingProtocol):
    def __init__(self):
        self.transport = None
    def connection_made(self,transport):
        print('Pass Through 1 connection made')
        peername = transport.get_extra_info('peername')
        print('Connection from {}'.format(peername))
        self.transport = transport
        higherTransport = StackingTransport(self.transport)
        self.higherProtocol().connection_made(higherTransport)
    def data_received(self, data):
        print('Pass Through 1 data received')
        self.higherProtocol().data_received(data)
    def connection_lost(self, exc):
        print('Pass Through 1 connection lost')
        self.transport = None
        self.higherProtocol().connection_lost()

class PassThroughTwoProtocol(StackingProtocol):
    def __init__(self):
        self.transport = None
    def connection_made(self,transport):
        print('Pass Through 2 connection made')
        peername = transport.get_extra_info('peername')
        print('Connection from {}'.format(peername))
        self.transport = transport
        higherTransport = StackingTransport(self.transport)
        self.higherProtocol().connection_made(higherTransport)
    def data_received(self, data):
        print('Pass Through 2 data received')
        self.higherProtocol().data_received(data)
    def connection_lost(self, exc):
        print('Pass Through 2 connection lost')
        self.higherProtocol().connection_lost()
        self.transport = None

class ServerProtocol(asyncio.Protocol):
    def __init__(self):
        self.transport = None
        courselist = []
        courselist.append({'cid': b'EN.601.644', 'cname': 'network security', 'enrollmentlimit': 60, 'enrolled': 60})
        courselist.append({'cid': b'EN.500.603', 'cname': 'academic ethics', 'enrollmentlimit': -1, 'enrolled': 500})
        courselist.append(
            {'cid': b'EN.601.643', 'cname': 'Security & Privacy in Computing', 'enrollmentlimit': 60, 'enrolled': 59})
        self.courselist = courselist


    def connection_made(self, transport):
        print("ServerProtocol connection_made")
        peername = transport.get_extra_info('peername')
        print('Connection from {}'.format(peername))
        self.transport = transport
        self._deserializer = PacketType.Deserializer()
        self.state = 0

    def data_received(self, data):
        self._deserializer.update(data)
        for p in self._deserializer.nextPackets():
            if isinstance(p,CourseIDPacket):
                if self.state != 0:
                    time.sleep(3)
                    print('Wrong state! Close the client socket')
                    self.transport.close()
                else:
                    self.state = 1
                    print('Packet1 received:')
                    print(p)
                    packet2 = CourseNamePacket()
                    packet2.cid = p.cid
                    findcourse=0
                    for c in self.courselist :
                        if c['cid'] == p.cid :
                            packet2.cname = c['cname']
                            if c['enrollmentlimit'] > 0:
                                packet2.enrollmentlimit = c['enrollmentlimit']
                            findcourse=1
                            break
                    if findcourse == 1 :
                        packet2Bytes = packet2.__serialize__()
                        print('CourseNamePacket(Packet2) Sent')
                        self.transport.write(packet2Bytes)
                    else :
                        print('Cannot Find Course ID')
                        time.sleep(3)
                        print('Close the client socket')
                        self.transport.close()
            elif p.DEFINITION_IDENTIFIER == "lab2b.yliu.Register" :
                if self.state != 1:
                    time.sleep(3)
                    print('Wrong state! Close the client socket')
                    self.transport.close()
                else:
                    self.state = 2
                    print('Packet3 received')
                    print(p)
                    packet4 = RegisterResultPacket()
                    findcourse=0
                    for c in self.courselist :
                        findcourse = 1
                        if c['cid'] == p.cid :
                            if c['enrollmentlimit'] == -1:
                                packet4.result = 'enrolled'
                            elif c['enrolled'] < c['enrollmentlimit']:
                                packet4.result = 'enrolled'
                            elif c['enrolled'] >= c['enrollmentlimit'] and p.waitlist :
                                packet4.result = 'waitlist'
                            else:
                                packet4.result = 'failed'
                            break
                    if findcourse == 1 :
                        packet4.sid = p.sid
                        packet4.cid = p.cid
                        packet4Bytes = packet4.__serialize__()
                        print('RegisterResultPacket(Packet4) Sent')
                        self.transport.write(packet4Bytes)
                    else :
                        print('Cannot Find Course ID')
                    print('Close the client socket')
                    self.transport.close()

    def connection_lost(self, exc):
        print("ServerProtocol Connection lost")
        self.transport = None



Stack = StackingProtocolFactory(lambda: PassThroughTwoProtocol(),lambda: PassThroughOneProtocol())
ptConnector = playground.Connector(protocolStack=Stack)
playground.setConnector("passthrough",ptConnector)

loop = asyncio.get_event_loop()
loop.set_debug(enabled=True)
# Each client connection will create a new protocol instance
coro = playground.getConnector('passthrough').create_playground_server(ServerProtocol, 8888)
server = loop.run_until_complete(coro)

# Serve requests until Ctrl+C is pressed
try:
    loop.run_forever()
except KeyboardInterrupt:
    pass

# Close the server
server.close()
#loop.run_until_complete(server.wait_closed())
loop.close()
