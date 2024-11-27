# this file is used in the node of aws, every node should pre-install the boto3 lib
import sys
import boto3
import os
import time 
#import zipfile
#get the application
app = sys.argv[1]

if not os.path.exists('./'+app+'.tar'):
    # load your aws key
    aws_access_key_id = 
    aws_secret_access_key = 
    region_name = 'us-east-1'

    #create the client for downloading files from S3 busket
    #all the files are stored in "bench-image" busket
    client = boto3.client('s3',                                                                  
                        aws_access_key_id=aws_access_key_id, 
                        aws_secret_access_key=aws_secret_access_key,
                        region_name=region_name, endpoint_url='https://s3-accelerate.amazonaws.com')
    #download file through s3
    client.download_file('bench-image', app+'.tar', './'+app+'.tar')
    # fz =zipfile.ZipFile('./'+app+'.tar', 'r')
    # fz.extractall('./')
    # execute the docker image
    os.system('docker load -i '+ app+'.tar')
    os.system('docker run '+app)
    
else:
    os.system('docker run '+app)







