from playground.network.packet import PacketType
from playground.network.packet.fieldtypes import UINT16, STRING, BUFFER, BOOL, ListFieldType
from playground.network.packet.fieldtypes.attributes import Optional
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


def basicUnitTest():
    #test1: serialize and deserialize CourseIDPacket
    packet1 = CourseIDPacket()
    packet1.cid = b"EN.601.644"
    packet1Bytes = packet1.__serialize__()
    print("Packet1 Bytes:")
    print(packet1Bytes)
    packet1a = CourseIDPacket.Deserialize(packet1Bytes)
    if packet1 == packet1a:
        print("test1: succeed")
    else:
        print("test1: fail")

    #test2: serialize and deserialize CourseNamePacket
    packet2 = CourseNamePacket()
    packet2.cid = b"EN.601.644"
    packet2.cname = "network security"
    packet2.enrollmentlimit = 60
    packet2Bytes = packet2.__serialize__()
    packet2a = CourseNamePacket.Deserialize(packet2Bytes)
    if packet2 == packet2a:
        print("test2: succeed")
    else:
        print("test2: fail")

    #test3: serialize and deserialize RegisterPacket
    packet3 = RegisterPacket()
    packet3.sid = b"ABC123"
    packet3.cid = b"EN.601.644"
    packet3.waitlist = True
    packet3Bytes = packet3.__serialize__()
    packet3a = RegisterPacket.Deserialize(packet3Bytes)
    if packet3 == packet3a:
        print("test3: succeed")
    else:
        print("test3: fail")

    #test4: serialize and deserialize RegisterResultPacket
    packet4 = RegisterResultPacket()
    packet4.sid = b"ABC123"
    packet4.cid = b"EN.601.644"
    packet4.result = "enrolled"
    packet4Bytes = packet4.__serialize__()
    packet4a = RegisterResultPacket.Deserialize(packet4Bytes)
    if packet4 == packet4a:
        print("test4: succeed")
    else:
        print("test4: fail")

    #test5: do not set optional value and serialize CourseNamePacket
    packet5 = CourseNamePacket()
    packet5.cid = b"EN.601.644"
    packet5.cname = "network security"
    packet5Bytes = packet5.__serialize__()
    packet5a = CourseNamePacket.Deserialize(packet5Bytes)
    if packet5 == packet5a:
        print("test5: succeed")
    else:
        print("test5: fail")

    #test6: do not set a vaue and serialize a packet
    #There is supposed to be an error. So if there is an error, we'll print "succeed".
    packet6 = CourseIDPacket()
    try: packet6Bytes = packet6.__serialize__()
    except: print("test6: succeed")
    else: print("test6: fail")

    #test7: set a negative value to an unsigned int
    # There is supposed to be an error. So if there is an error, we'll print "succeed".
    packet7 = CourseNamePacket()
    packet7.cid = b"EN.601.644"
    packet7.cname = "network security"
    try: packet7.enrollmentlimit = -1
    except: print("test7: succeed")
    else: print("test7: fail")

    #test8: use Deserializer to deal with packets
    packetBytes = packet1Bytes + packet2Bytes + packet3Bytes
    d = PacketType.Deserializer()
    d.update(packetBytes)
    print("test8:")
    for p in d.nextPackets():
        print(p)

    #test9: use Deserializer to deal with packets
    packet9a = packet4Bytes[:10]
    packet9b = packet4Bytes[10:]
    d.update(packet9a)
    print("test9a:")
    for p in d.nextPackets():
        print(p)
    print("test9b:")
    d.update(packet9b)
    for p in d.nextPackets():
        print(p)

if __name__=="__main__":
    basicUnitTest()