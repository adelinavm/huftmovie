import streamlit as st
import json
import os
import hashlib

USER_FILE = "users.json"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, "r") as f:
        try:
            data = json.load(f)
            if isinstance(data, list):
                # If file is an empty list, return empty dict for backward compatibility
                return {}
            return data
        except Exception:
            return {}

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f)

def register_user(username, password):
    users = load_users()
    if username in users:
        return False, "Username sudah terdaftar."
    users[username] = hash_password(password)
    save_users(users)
    return True, "Registrasi berhasil!"

def authenticate_user(username, password):
    users = load_users()
    if username in users and users[username] == hash_password(password):
        return True
    return False
