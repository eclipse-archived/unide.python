import requests
from unide.common import Device

if __name__ == "__main__":
    # http://[host]:[port]/rest/v2/message?validate=true
    device = Device("Device-001")
    msg = device.message("0000", description="Nothing interesting")
    print(msg)
    url = "http://unide.eclipse.org/rest/v2/message?validate=true"
    r = requests.post(url, data=msg)
