"""One-time setup helpers.

    python -m scripts.bootstrap admin  <username> <password>   create the first admin user
    python -m scripts.bootstrap device <name> "<location>"      register a device, prints its API key once
"""
import sys

from app.config import get_settings
from app.security import hash_password, new_device_key
from app.storage import build_storage


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 1
    storage = build_storage(get_settings())
    cmd = argv[1]
    if cmd == "admin" and len(argv) == 4:
        if storage.get_user_by_username(argv[2]):
            print("user already exists")
            return 1
        u = storage.insert_user({"username": argv[2], "password_hash": hash_password(argv[3]), "role": "admin"})
        print(f"admin user created: id={u['user_id']} username={u['username']}")
        return 0
    if cmd == "device" and len(argv) == 4:
        key, key_hash = new_device_key()
        d = storage.insert_device({"device_name": argv[2], "location": argv[3], "status": "Active",
                                   "api_key_hash": key_hash})
        print(f"device registered: id={d['device_id']} name={d['device_name']}")
        print(f"API key (shown once, store it on the device): {key}")
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
