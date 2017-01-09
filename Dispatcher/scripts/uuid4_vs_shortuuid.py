import shortuuid
import uuid

s1, s2 = set(), set()
for i in range(200000):
    s1.add(shortuuid.ShortUUID().random(length=6))
    s2.add(str(uuid.uuid4().fields[-1])[:6])
print(("shortuuid: ", len(s1)))
print(("uuid4: ", len(s2)))

