import sys
import paramiko

REMOTE_HOST = "172.16.7.1"
REMOTE_USER = "mtasbas"

def create_ssh_client():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(REMOTE_HOST, username=REMOTE_USER)
    return client

def cmd(command, print_output=True):
    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode().strip()
    if print_output:
        print(output)
    return output

def main():
    global ssh
    try:
        ssh = create_ssh_client()
        print("SSH connection established successfully.")

        # Your commands go here
        cmd("squeue")
        # Add more commands as needed

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'ssh' in globals():
            ssh.close()

if __name__ == "__main__":
    main()
