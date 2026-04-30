# CECS 327 Project Assignment 8 - Distributed End-to-End IoT System

## Samuel Umoren, Benjiman Diaz

## Project Overview
This project combines:
- the TCP client/server from Assignment 6
- the NeonDB and DataNiz setup from Assignment 7
- shared IoT data between two separate student environments

Each teammate represents a different smart house with their own:
- DataNiz account
- virtual IoT devices
- NeonDB database

## Supported Queries
The client only accepts these 3 queries:

1. What is the average moisture inside our kitchen fridges in the past hours, week and month?
2. What is the average water consumption per cycle across our smart dishwashers in the past hour, week and month?
3. Which house consumed more electricity in the past 24 hours, and by how much?

Any other input is rejected.

## How the System Works
DataNiz devices generate sensor data and send it through shared broker topics into NeonDB.  
The TCP client sends a valid query to the TCP server.  
The server checks the local database, decides if the data is complete, and if needed retrieves missing historical data from the teammate’s database.

## Sharing Model
DataNiz sharing is forward-only:
- each student keeps all of their own historical data
- shared teammate data only appears after sharing starts
- older peer data is not automatically copied

## Metadata Usage
Metadata is used to:
- tell House A from House B
- identify device and sensor type
- separate local vs shared data
- preserve ownership during query processing
- more in depth in the 'workflow.md'

## How to Run
note: make sure you have the RDP files from VM instances of both server and client downloaded and opened. Those can be found in config.md. 

1. Clone the repo in both server and client

   git clone https://github.com/notbenjiie/327Proj.git
3. Install dependencies on both
   
   -python --version ## to ensure you have python installed on the system, if not install it. 

   -pip install psycopg2-binary

   -pip install pytz
   
4. Start the server by using the following command
   
   -python server.py
6. Start the client by using the following command
   
   -python client.py
   
   You will then be prompted to enter the IP address, enter the server's IP, in our case it is
   >34.72.118.154
7. Enter one of the supported queries
   1. What is the average moisture inside our kitchen fridges in the past hours, week and month?
   2. What is the average water consumption per cycle across our smart dishwashers in the past hour, week and month?
   3. Which house consumed more electricity in the past 24 hours, and by how much?

## Notes
- Results should be formatted in PST
- Imperial units are used when needed
- The system is designed for a distributed partial-replication setup, not a fully centralized one
