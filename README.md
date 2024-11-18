# <img src="https://github.com/LukeJYK/SC24_eco-life/raw/main/ecolife_logo.png" alt="ECOLIFE Logo" width="150" align="left"> ECOLIFE: Carbon-Aware Serverless Function Scheduling for Sustainable Computing (SC'24)


Paper is published at 2024 ACM/IEEE The International Conference for High Performance Computing, Networking, Storage, and Analysis (SC'24)
Link to paper: https://arxiv.org/pdf/2409.02085



## Table of Contents
- [Description](#description)
- [Dependencies](#dependencies)
- [Directory](#directory)
- [Setup](#setup)
- [Content](#content)
- [Run EcoLife](#run-ecolife)
- [Cite](#cite)

## Description
EcoLife is an innovative framework that leverages multi-generation hardware to co-optimize carbon footprint and service time within the serverless environment. EcoLife extends Particle Swarm Optimization (PSO) to adapt to the variations in serverless computing for making keep-alive and execution decisions. Our experimental results show that EcoLife effectively reduces carbon emissions while maintaining high performance for function execution.


## Dependencies 
EcoLife can be executed with Python 3.8, and requires Python packages, including boto3, fire, numpy, awscli, json, paramiko for execution. The energy profling code must be executed on a bare-metal machine to use RAPL (More info: https://www.ibm.com/topics/bare-metal-dedicated-servers). Other data information can be found in the later section.

## Directory
```
│SC24_eco-life/
  ├──carbon_intensity/
  ├──data/
  ├──motivations/
  ├──node/
  ├──optimizers/
  ├──results/
  ├──selected traces/
```
1. `carbon_intensity` contains the carbon intensity for various regions, Use one of them to simulate.
2. `data` contains the profiled data for optimization. (eg. the carbon and energy data for different serverless functions)
3. `motivations`: 4 motivations in the paper.
4. `node`: Generate the profiled data. 
5. `optimizers`: different optimizers in Ecolife
6. `results`: you may need to save your results in this folder.
7. `exe_decide.py`:Execution Placement Decision Maker.
8. `function_mem.csv`: Memory consumption of different serverless functions.
9. `main.py`: You may use it to run the codebase.
10. `pso.py`: DPSO in Ecolife. 
11. `utils.py`: Help functions.
12. `selected_trace.zip`: Traces for simulation.
## Setup
### 1. Local Controller Setup
EcoLife consists of two primary environments: (1) AWS EC2 servers, where functions are executed and profiled, and (2) the user's local environment, which serves as the controller. In the controller environment, ensure all necessary packages and the AWS CLI are properly set up.
```bash
pip3 install numpy
pip3 install boto3 
pip3 install paramiko
pip3 install awscli
pip3 install fire
aws configure
```
Download AWS CLI: [https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)

### 2. AWS Test Node Setup
EcoLife leverages the AWS EC2 platform for function execution. First, configure `boto3` and `awscli` with your AWS account credentials using the `aws configure` command. Next, from the AWS Management Console, launch an EC2 instance running the 'Ubuntu Server 20.04 LTS' operating system. Once the instance is up and running, log in via SSH and execute the following commands in the terminal to install Docker and set up the AWS CLI:
 - AWS CLI install and setup: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
- Install Docker:
```bash
sudo apt-get update
sudo apt-get install docker.io
```
- Set up the measuring code in the AWS worker node, the code file is under `./node/worker_node`. Make sure you have already prepared the Serverless applications in the S3 storage buckets. (You can use your own preferred storage options)
From the EC2 dashboard now, create an image of the instance in which docker is installed and note the `AMI ID`.  The `AMI ID` will be input in the profiling code for creating more AWS EC2 instances. 

## Content

### Operational Carbon Datasets

The carbon intensity data is from Electricity Map: https://app.electricitymaps.com/map, EcoLife is using the 2023 carbon intensity data. Energy consumption of CPU and DRAM is using Likwid (https://github.com/RRZE-HPC/likwid).

### Embodied Carbon
We primarily use these 2 datasets:

- https://dataviz.boavizta.org/cloudimpact 
- https://engineering.teads.com/sustainability/carbon-footprint-estimator-for-aws-instances/

### Hardware Pairs
All the hardware pairs are from AWS, and they are all bare-metal machines.
#### Multi-generation Hardware Pairs Examples

| **Pair** | **Old/New**        | **CPU Model (Year)**                | **DRAM Model (Year)**            |
|----------|---------------------|-------------------------------------|----------------------------------|
| Pair<sub>A</sub> | **A<sub>Old</sub>** | Intel Xeon E5-2686 (2016)          | Micron-512 (2018)                |
|          | **A<sub>New</sub>** | Intel Xeon Platinum 8252C (2020)    | Samsung-192 (2019)               |
| Pair<sub>B</sub> | **B<sub>Old</sub>** | Intel Xeon Platinum 8124M (2017)   | Micron-192 (2018)                |
|          | **B<sub>New</sub>** | Intel Xeon Platinum 8252C (2020)    | Samsung-192 (2019)               |
| Pair<sub>C</sub> | **C<sub>Old</sub>** | Intel Xeon Platinum 8275L (2019)   | Samsung-192 (2019)               |
|          | **C<sub>New</sub>** | Intel Xeon Platinum 8252C (2020)    | Samsung-192 (2019)               |

**Note:** i3.metal, , c5n.metal, c5.metal, m5zn.metal

## Run EcoLife:
```bash
unzip selected_trace.zip
python3 main.py <add your desired configuration>
```

## Cite
```@bibtex
@inproceedings{jiang2024ecolife,
  title={EcoLife: Carbon-Aware Serverless Function Scheduling for Sustainable Computing},
  author={Jiang, Yankai and Roy, Rohan Basu and Li, Baolin and Tiwari, Devesh},
  booktitle={Proceedings of the International Conference for High Performance Computing, Networking, Storage, and Analysis},
  pages={1--15},
  year={2024}
}
```
#### Contact info: jiang.yank@northeastern.edu
