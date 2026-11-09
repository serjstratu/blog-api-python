from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token
)


password = "MyStrongPassword123!"

# Hash
hashed = hash_password(password)

print("Hashed:", hashed)

# Verify
print("Valid password:", verify_password(password, hashed))
print("Invalid password:", verify_password("wrong", hashed))

# JWT
token = create_access_token("1")

print("Token:", token)

# Decode
payload = decode_access_token(token)

print("Payload:", payload)