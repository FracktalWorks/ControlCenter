import socket
import json

def check_connection(host, port):
    request = {
        "sid": 0,
        "cmd": "get_working_status",
    }
    status_map = {
        0: "Waiting",
        1: "Marking",
        2: "Previewing",
        3: "Already working"
    }
    try:
        json_string = json.dumps(request)
        with socket.create_connection((host, port), timeout=2) as sock:
            sock.sendall(json_string.encode())
            ret = sock.recv(1024)
            if ret:
                ret_str = ret.decode('GB2312')
                ret_json = json.loads(ret_str)
                connection_status = ret_json.get("ret")
                status_text = status_map.get(connection_status, "Unknown")
                print(f"Connection status: {status_text}")
                return status_text
            else:
                print("No response received.")
                return None
    except (socket.timeout, socket.error, json.JSONDecodeError) as e:
        print(f"Connection to {host}:{port} failed: {e}")
        return None

if __name__ == "__main__":
    HOST = "localhost"
    PORT = 50000
    status = check_connection(HOST, PORT)
    print(f"Host and port status: {status}")