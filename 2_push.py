import sys
import paramiko
import os
import argparse

REMOTE_HOST = "172.16.7.1"
REMOTE_USER = "mtasbas"
REMOTE_BASE_PATH = "/truba/home/mtasbas/mirscribe-vcf/synthdata/"

def create_ssh_client():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(REMOTE_HOST, username=REMOTE_USER)
    return client

def cmd(command, print_output=True):
    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    if error:
        print(f"Error: {error}")
    if print_output:
        print(output)
    return output

def main():
    global ssh
    parser = argparse.ArgumentParser(description="Push .vcf files to a remote server via SSH and run batch jobs.")
    parser.add_argument("folder", help="Path to the local folder containing .vcf files to be pushed")
    args = parser.parse_args()

    if not os.path.isdir(args.folder):
        print(f"Error: {args.folder} is not a valid directory.")
        sys.exit(1)

    try:
        ssh = create_ssh_client()
        print("SSH connection established successfully.")

        folder_path = os.path.join(args.folder, '')
        folder_name = os.path.basename(os.path.dirname(folder_path))
        remote_path = os.path.join(REMOTE_BASE_PATH, folder_name)

        # Create remote directory
        cmd(f"mkdir -p {remote_path}")

        # Use SCP to upload .vcf files
        local_path = os.path.join(folder_path, "*.vcf")
        scp_command = f"scp {local_path} {REMOTE_USER}@{REMOTE_HOST}:{remote_path}"
        os.system(scp_command)  # Using os.system for local SCP command

        print(f"Successfully pushed .vcf files from {folder_path} to {REMOTE_HOST}:{remote_path}")

        # Change to commands directory
        cmd("cd ~/commands")

        # Generate jobs
        cmd(f"./generate_synth_jobs_and_commands.sh {folder_name}")

        # Run sbatch commands
        cmd(f"cat sbatch_commands_{folder_name}.txt | bash")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'ssh' in globals():
            ssh.close()

if __name__ == "__main__":
    main()
