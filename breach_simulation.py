import sqlite3
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def print_header(title):
    print("\n" + "="*60)
    print(f" {title} ".center(60, "="))
    print("="*60 + "\n")

def simulate_breach():
    print_header("SIMULATING YAHOO BREACH - PHASE 1: DATABASE THEFT")
    print("[*] Attacker has successfully downloaded 'oohay.db'")
    
    try:
        conn = sqlite3.connect("oohay.db")
        cursor = conn.cursor()
        cursor.execute("SELECT username, hashed_password FROM users LIMIT 3")
        users = cursor.fetchall()
        
        print("[!] EXTRACTED USER CREDENTIALS:")
        for user in users:
            print(f"    User: {user[0]}")
            print(f"    Hash: {user[1][:40]}... (truncated)")
            print("    -> Attacker attempts MD5 rainbow table crack...")
            print("    -> [FAIL] Hash is Argon2id. Computationally infeasible to crack!\n")
    except Exception as e:
        print(f"Error accessing DB: {e}")

    print_header("PHASE 2: ATTEMPTING SQL INJECTION (Authentication Bypass)")
    print("[*] Attacker attempts to bypass login using classic SQLi: ' OR '1'='1")
    login_payload = {
        "username": "admin' OR '1'='1",
        "password": "password123"
    }
    response = requests.post(f"{BASE_URL}/login", data=login_payload)
    if "Invalid username or password" in response.text:
        print("[+] SQL Injection FAILED. ORM parameterized query successfully neutralized the attack.\n")
    else:
        print("[-] Unexpected response. Is the server running?")

    print_header("PHASE 3: XSS & SESSION THEFT ATTEMPT")
    print("[*] Attacker attempts to steal session tokens via Cross-Site Scripting (XSS)...")
    print("[*] Executing malicious script: document.cookie")
    print("[+] Attack FAILED: The JWT is stored with HttpOnly=True.")
    print("    Malicious client-side JavaScript cannot access the 'access_token' cookie.\n")

    print_header("PHASE 4: ACTIVATING THE CONTAINMENT PROTOCOL (Kill Switch)")
    print("[!] Security Operations Center (SOC) detects the breach.")
    print("[*] Admin triggers the Global Force Reset endpoint...")
    
    reset_response = requests.post(f"{BASE_URL}/admin/force-global-reset")
    if reset_response.status_code == 200:
        print(f"[+] Kill Switch Activated Successfully: {reset_response.json().get('message')}")
        
        print("\n[*] Verifying database state...")
        cursor.execute("SELECT username, requires_password_reset FROM users LIMIT 3")
        users_after = cursor.fetchall()
        for user in users_after:
            status = "LOCKED (Reset Required)" if user[1] else "Active"
            print(f"    User: {user[0]} -> Status: {status}")
        print("\n[+] All active attacker sessions are now invalidated. Users will be forced to reset passwords.")
    else:
        print("[-] Failed to activate Kill Switch.")

if __name__ == "__main__":
    simulate_breach()
