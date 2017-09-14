from playground.network.packet import PacketType
from playground.network.packet.fieldtypes import UINT16, STRING, BUFFER, BOOL, ListFieldType
from playground.network.packet.fieldtypes.attributes import Optional
import playground
import asyncio
import time

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

class ClientProtocol(asyncio.Protocol):
    def __init__(self,sid,cid,waitlist,loop):
        self.sid = sid
        self.cid = cid
        self.waitlist = waitlist
        self.loop = loop
        self.transport = None

    def connection_made(self,transport):
        self._deserializer = PacketType.Deserializer()

        packet1 = CourseIDPacket()
        packet1.cid = self.cid
        packet1Bytes = packet1.__serialize__()
        self.transport = transport
        time.sleep(3)
        transport.write(packet1Bytes)
        print('Packet1(CourseIDPacket) sent')

    def data_received(self, data):

        self._deserializer.update(data)

        for p in self._deserializer.nextPackets():

            if p.DEFINITION_IDENTIFIER == "lab2b.yliu.CourseName" :
                print('Packet2(CourseNamePacket) received')
                print(p)
                print('CourseName: {!r}'.format(p.cname))
                packet3 = RegisterPacket()
                packet3.sid = self.sid
                packet3.cid = self.cid
                packet3.waitlist = self.waitlist
                packet3Bytes = packet3.__serialize__()
                self.transport.write(packet3Bytes)
                print('Packet3(RegisterPacket) sent')
            elif p.DEFINITION_IDENTIFIER == "lab2b.yliu.RegisterResult" :
                print('Packet4(RegisterResultPacket) received')
                print(p)
                print('Registration status: {!r}'.format(p.result))

    def connection_lost(self, exc):
        self.transport = None
        print('The server closed the connection')
        print('Stop the event loop')
        self.loop.stop()

loop = asyncio.get_event_loop()
sid = b"ABC123"
cid = b"EN.601.643"
waitlist = False
coro = playground.getConnector().create_playground_connection(lambda: ClientProtocol(sid,cid,waitlist,loop),'20174.1.1.1',8888)
loop.run_until_complete(coro)
loop.run_forever()
loop.close()
