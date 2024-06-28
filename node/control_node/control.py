#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import boto3
import paramiko
import time
import os
import json

FNULL = open(os.devnull, 'w')

#your credentials:
AWS_ACCESS_KEY_ID =  
AWS_SECRET_ACCESS_KEY = 
KEY_NAME = 
SECURITY_GROUP_ID = 
SECURITY_GROUP_NAME = 


def start_ec2(ec2_name, img_id):
    ec2_client = boto3.client("ec2", region_name = "us-east-1", aws_access_key_id =AWS_ACCESS_KEY_ID, 
                            aws_secret_access_key = AWS_SECRET_ACCESS_KEY)
    instance=ec2_client.run_instances(ImageId=img_id, MinCount=1, MaxCount=1, 
                                      InstanceType=ec2_name, KeyName=KEY_NAME,
                                      SecurityGroupIds = [SECURITY_GROUP_ID], SecurityGroups = [SECURITY_GROUP_NAME])
    return (instance["Instances"][0]["InstanceId"])

def get_info(ssh_out):
    numbers = ssh_out.split()
    # return cpu energy, dram energy and runtime
    return float(numbers[0]), float(numbers[1]), float(numbers[2])

def terminate_ec2(inst,ec2):
    instance = ec2.Instance(inst)
    instance.terminate()

def setting_aws_credential(ssh):
    commands = [
    'sudo pip3 install --upgrade awscli',
    f'sudo aws configure set aws_access_key_id {AWS_ACCESS_KEY_ID} ',
    f'sudo aws configure set aws_secret_access_key {AWS_SECRET_ACCESS_KEY} ',
    'sudo aws configure set default.region "us-east-1" ']
    # Execute each command and print the output
    for command in commands:
        stdin, stdout, stderr = ssh.exec_command(command)
        exit_status_1 = stdout.channel.recv_exit_status()


def remove(ssh, app):
    commands = ['sudo docker rmi '+app]
    for command in commands:
        stdin, stdout, stderr = ssh.exec_command(command)
        exit_status_1 = stdout.channel.recv_exit_status()

def ssh_connect_with_retry_with_run(ssh, ip_address, retries,app,keypath):
    if retries > 3:
        return False
    privkey = paramiko.RSAKey.from_private_key_file(keypath)
    interval = 5
    try:
        retries += 1
        ssh.connect(hostname=ip_address, timeout=7200, username='ubuntu', pkey=privkey)
    except Exception as e:
        print(e)
        time.sleep(interval)
        print('Retrying SSH connection to {}'.format(ip_address))
        ssh_connect_with_retry_with_run(ssh, ip_address, retries,app,keypath)
    print("Connected")
    
    print('start serverless!')
    stdin, stdout, stderr = ssh.exec_command("python3 measure.py " + app)

    exit_status_1 = stdout.channel.recv_exit_status()
    energy11, energy12,time1 = get_info(stdout.read().decode())
    print("finish 1st time")
    stdin, stdout, stderr = ssh.exec_command("python3 measure.py " + app)
    exit_status_2 = stdout.channel.recv_exit_status()
    energy21, energy22, time2 = get_info(stdout.read().decode())

    
    print("Finish execution")
    stdin, stdout, stderr = ssh.exec_command("sudo docker rmi -f "+app)
    exit_status_remove1 = stdout.channel.recv_exit_status()
    stdin, stdout, stderr = ssh.exec_command("sudo rm -r "+app+'.tar')
    exit_status_remove2 = stdout.channel.recv_exit_status()
    #cs cs energy exe exe energy
    return time1-time2, energy11-energy21, energy12-energy22, time2, energy21, energy22


if __name__ == "__main__":
    
    ImageId_with_docker='ami-029a808ad811a5224' ##
    vm_family_list=['i3.metal','m5zn.metal']##
    keypath = "/home/ubuntu/yankai_carbon.pem" ##
    for vm_family in vm_family_list:
        instance_id = start_ec2(vm_family,ImageId_with_docker)
        time.sleep(3)
        ec2 = boto3.resource('ec2', region_name='us-east-1')
        current_instance = list(ec2.instances.filter(InstanceIds=[instance_id]))
        current_instance[0].wait_until_running()
        current_instance[0].reload()
        ip_address = current_instance[0].public_ip_address
        app_list = ['dna','pagerank-1000k', 'upload-img','dynamic-100k','compression','image-recog','video','bfs-1000k','mst-1000k','thumbnailer']
        for app in app_list:
            output = []
            for i in range(6):
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                a,b,c,d,e,f = ssh_connect_with_retry_with_run(ssh, ip_address, 2, app, keypath)
                if i !=0:
                    output_each  = {"cs":a,"cs_energy_cpu":b,"cs_energy_dram": c,"exe":d,"exe_energy_cpu":e,"exe_energy_dram":f}
                    output.append(output_each)
                with open(f"./{app}_{vm_family}.json", "w") as f:
                    json.dump(output, f, indent=4)
                ssh.close()
        terminate_ec2(instance_id,ec2)
