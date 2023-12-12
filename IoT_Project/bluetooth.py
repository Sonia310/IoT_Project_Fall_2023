def detect_bluetooth_devices():
	global bluetooth_device_count
	
	while True:
		try:
			nearby_devices = bluetooth.discover_devices()
			bluetooth_devices_count = len(nearby_devices)
		except Exception as e:
			print(f"Error discovering devices: {e}")
