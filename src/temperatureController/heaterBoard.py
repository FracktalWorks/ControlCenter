from .serialProtocol import SerialProtocol

class HeaterBoard:
    def __init__(self, port="COM19"): #TBD take port as input from frontend
        self.serial_model = SerialProtocol(port="COM19", baudrate=115200, timeout=1)

    def setHeaterPowers(self,ch1,ch2,ch3,ch4,ch5,ch6,ch7,ch8):
        command = f"8,{ch1},{ch2},{ch3},{ch4},{ch5},{ch6},{ch7},{ch8}"
        self.serial_model.send_command(command)

    def stopHeaters(self):
        command = "8,1,1,1,1,1,1,1,1"
        self.serial_model.send_command(command)
        print("Heater stopped")

    def enableWatchdog(self, event):
        command = f"E"
        self.serial_model.send_command(command)

    def enableWatchdog(self, event):
        command = f"D"
        self.serial_model.send_command(command)

