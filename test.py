import hashlib, binascii

def hash_string(password):
    password = password.encode('UTF-8')
    password = hashlib.pbkdf2_hmac('sha512', b'password', b'salt', 100000)  # TODO(salt)
    password = binascii.hexlify(password)
    return password

print(hash_string('cc'))
