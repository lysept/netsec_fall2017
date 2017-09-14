from playground.network.packet import PacketType
from playground.network.packet.fieldtypes import UINT16, STRING, BUFFER, BOOL, ListFieldType
from playground.network.packet.fieldtypes.attributes import Optional

import asyncio
from playground.asyncio_lib.testing import TestLoopEx
from playground.network.testing import MockTransportToStorageStream
from playground.network.testing import MockTransportToProtocol




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

class ServerProtocol(asyncio.Protocol):
    def __init__(self):
        self.transport = None
        courselist = []
        courselist.append({'cid': b'EN.601.644', 'cname': 'network security', 'enrollmentlimit': 60, 'enrolled': 60})
        courselist.append({'cid': b'EN.500.603', 'cname': 'academic ethics', 'enrollmentlimit': -1, 'enrolled': 500})
        courselist.append(
            {'cid': b'EN.601.643', 'cname': 'Security & Privacy in Computing', 'enrollmentlimit': 60, 'enrolled': 59})
        self.courselist = courselist
        self.state = 0 #init state, waiting for packet1

    def connection_made(self, transport):
        self.transport = transport
        self._deserializer = PacketType.Deserializer()

    def data_received(self, data):
        self._deserializer.update(data)
        for p in self._deserializer.nextPackets():
            if isinstance(p,CourseIDPacket):
                if self.state != 0 :
                    print('Server: Wrong state')
                    print('Server: Close the client socket')
                    self.transport.close()
                self.state = 1
                print('Server: Packet1 received:')
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
                    print('Server: CourseNamePacket(Packet2) Sent')
                    self.transport.write(packet2Bytes)
                else :
                    print('Server: Cannot Find Course ID')
                    print('Server: Close the client socket')
                    self.transport.close()
            elif isinstance(p,RegisterPacket):
                if self.state !=1 :
                    print('Server: Wrong state')
                    print('Server: Close the client socket')
                    self.transport.close()
                self.state = 2
                print('Server: Packet3 received')
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
                    print('Server: RegisterResultPacket(Packet4) Sent')
                    self.transport.write(packet4Bytes)
                else :
                    print('Server: Cannot Find Course ID')
                print('Server: Close the client socket')
                self.transport.close()

    def connection_lost(self, exc):
        self.transport = None


class ClientProtocol(asyncio.Protocol):
    def __init__(self):
        self.transport = None

    def connection_made(self,transport):
        self._deserializer = PacketType.Deserializer()
        self.transport = transport


    def sendpkt1(self, sid, cid, waitlist):
        self.sid = sid
        self.cid = cid
        self.waitlist = waitlist
        packet1 = CourseIDPacket()
        packet1.cid = self.cid
        packet1Bytes = packet1.__serialize__()
        print('Client: Packet1(CourseIDPacket) sent')
        self.transport.write(packet1Bytes)



    def data_received(self, data):
        self._deserializer.update(data)
        for p in self._deserializer.nextPackets():
            if isinstance(p,CourseNamePacket) :
                print('Client: Packet2(CourseNamePacket) received')
                print(p)
                print('Client: CourseName: {!r}'.format(p.cname))
                packet3 = RegisterPacket()
                packet3.sid = self.sid
                packet3.cid = self.cid
                packet3.waitlist = self.waitlist
                packet3Bytes = packet3.__serialize__()
                print('Client: Packet3(RegisterPacket) sent')
                self.transport.write(packet3Bytes)
            elif isinstance(p,RegisterResultPacket):
                print('Client: Packet4(RegisterResultPacket) received')
                print(p)
                print('Client: Registration status: {!r}'.format(p.result))

    def connection_lost(self, exc):
        print('Client: The server closed the connection')
        self.transport = None



def basicUnitTest():
        asyncio.set_event_loop(TestLoopEx())
        client = ClientProtocol()
        server = ServerProtocol()
        transportToServer = MockTransportToProtocol(myProtocol = client)
        transportToClient = MockTransportToProtocol(myProtocol = server)
        transportToServer.setRemoteTransport(transportToClient)
        transportToClient.setRemoteTransport(transportToServer)
        client.connection_made(transportToServer)
        server.connection_made(transportToClient)
        client.sendpkt1(b"ABC123",b"EN.601.644",True)





if __name__=="__main__":
    basicUnitTest()
    print("Basic Unit Test Success")