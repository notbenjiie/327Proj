import socket
import threading
import datetime
import pytz
import psycopg2
import json
from psycopg2.extras import RealDictCursor

#neon database connection, using benjamins database url
DATABASE_URL = "postgresql://neondb_owner:npg_JfYvui6j3aLF@ep-gentle-math-am03uc2y-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
TABLE_NAME = "Combined_datavirtual_virtual"

#data structures
class Node:
    def __init__(self, data):
        self.data = data # Format: {'house': 'A', 'val': 10.5, 'unit': 'Liters', 'time': PST_Obj}
        self.next = None

class IoTDataList:
    """Linked List for distributed data management"""
    def __init__(self):
        self.head = None

    def add(self, record):
        new_node = Node(record)
        new_node.next = self.head
        self.head = new_node

# utilities for conversions of time and metrics
def to_pst(dt_obj):
    #converts a datetime object to PST
    pst_tz = pytz.timezone('US/Pacific')
    if dt_obj.tzinfo is None:
        dt_obj = pytz.utc.localize(dt_obj)
    return dt_obj.astimezone(pst_tz)

def to_imperial(value, unit_type):
    """Converts metric units to imperial"""
    if unit_type == "Liters": 
        return value * 0.264172 # Liters to Gallons
    return value 

# database logic 
def fetch_local_db_data(device_type, hours):
    """Parses JSON payloads from Neon DB"""
    records = []
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # SQL query built as a standard string to avoid GitHub highlighting bugs
        query = "SELECT payload, time FROM \"" + TABLE_NAME + "\" WHERE time >= NOW() - INTERVAL '%s hours'"
        
        cur.execute(query, (hours,))
        raw_rows = cur.fetchall()
        
        for row in raw_rows:
            p = row['payload']
            if isinstance(p, str):
                p = json.loads(p)
            
            # identify House ID via email in the 'topic' key
            topic = p.get("topic", "")
            house_id = "A" if "bdiazengineer" in topic else "B"
            
            # extract specific sensor values based on keyword matching
            sensor_value = None
            found_type = None

            for key, val in p.items():
                if "Moisture" in key:
                    sensor_value = float(val)
                    found_type = "Fridge"
                elif "Water" in key or "YF-S201" in key:
                    sensor_value = float(val)
                    found_type = "Dishwasher"
                elif "Ammeter" in key or "ACS712" in key:
                    sensor_value = float(val)
                    found_type = "Smart Meter"

            # only add if it matches the current Query's requested device
            if found_type == device_type and sensor_value is not None:
                records.append({
                    'house_id': house_id,
                    'value': sensor_value,
                    'unit': "Liters" if found_type == "Dishwasher" else "Volts",
                    'timestamp': row['time']
                })
                
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Local DB Error: {e}")
    return records

# distributed query processing
def fetch_remote_data(query_type, teammate_ip, teammate_port):
    """Distributed communication for data completeness"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3) # Short timeout for fault tolerance demonstration
            s.connect((teammate_ip, teammate_port))
            s.send(f"REMOTE_REQ|{query_type}".encode())
            return json.loads(s.recv(8192).decode())
    except Exception as e:
        print(f"Remote fetch error: {e}")
        return []

def process_distributed_query(query_str, partner_ip, partner_port):
    data_list = IoTDataList()
    
    # map queries to device types
    if "moisture" in query_str:
        device_type, time_limit = "Fridge", 720
    elif "dishwasher" in query_str:
        device_type, time_limit = "Dishwasher", 720
    elif "electricity" in query_str:
        device_type, time_limit = "Smart Meter", 24
    else:
        return "Invalid query."

    # populate linked list with local data
    local_recs = fetch_local_db_data(device_type, time_limit)
    for r in local_recs:
        data_list.add({'house': r['house_id'], 'val': r['value'], 'unit': r['unit'], 'time': to_pst(r['timestamp'])})

    # fault tolerant distributed step
    remote_recs = fetch_remote_data(device_type, partner_ip, partner_port)
    for r in remote_recs:
        dt = datetime.datetime.strptime(r['timestamp'], "%Y-%m-%d %H:%M:%S")
        data_list.add({'house': r['house_id'], 'val': r['value'], 'unit': r['unit'], 'time': to_pst(dt)})

    # math and formatting
    nodes = list(iter_list(data_list))
    if not nodes:
        return "No data found for this query."

    if "electricity" in query_str:
        # for electricity logic
        vals_a = [n.data['val'] for n in nodes if n.data['house'] == 'A']
        vals_b = [n.data['val'] for n in nodes if n.data['house'] == 'B']
        
        # calculate averages
        avg_a = sum(vals_a) / len(vals_a) if vals_a else 0
        avg_b = sum(vals_b) / len(vals_b) if vals_b else 0
        diff = avg_a - avg_b
        winner = "House A" if avg_a > avg_b else "House B"
        
        return f"{winner} had a higher average electrical load by {abs(diff):.2f} units (PST)."

    # moisture and dishwasher averages
    vals = [to_imperial(n.data['val'], n.data['unit']) for n in nodes]
    avg = sum(vals) / len(vals)
    unit_label = "Gallons" if "dishwasher" in query_str else "Percentage"
    return f"Average {device_type} reading is {avg:.2f} {unit_label} across both houses (PST)."

def iter_list(iot_list):
    """Helper to iterate through the linked list"""
    curr = iot_list.head
    while curr:
        yield curr
        curr = curr.next

# socket handling
def handle_client(conn, addr, partner_ip, partner_port):
    try:
        data = conn.recv(1024).decode()
        if data.startswith("REMOTE_REQ"):
            parts = data.split("|")
            device = "Fridge" if "moisture" in parts[1] else "Dishwasher" if "dishwasher" in parts[1] else "Smart Meter"
            recs = fetch_local_db_data(device, 720)
            for r in recs: 
                r['timestamp'] = r['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
            conn.send(json.dumps(recs).encode())
        else:
            print(f"Processing query from {addr}: {data}")
            final_answer = process_distributed_query(data, partner_ip, partner_port)
            conn.send(final_answer.encode())
    finally:
        conn.close()

def start_server(local_port, partner_ip, partner_port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
    server.bind(('0.0.0.0', local_port))
    server.listen(5)
    print(f"IoT Server running on port {local_port}...")
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr, partner_ip, partner_port)).start()

if __name__ == "__main__":
    # Ensure this is a valid IP string, in this case it was our google cloud client instance external IP
    PARTNER_IP = "35.238.211.232" 
    start_server(5000, PARTNER_IP, 5000)
