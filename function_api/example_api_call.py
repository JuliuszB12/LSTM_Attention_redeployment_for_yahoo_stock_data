# Python 3.10
import sys
import json
import requests
import numpy as np

resourceGroupName = sys.argv[1]

x = np.load('example_test_data.npy')
data = [x[0].tolist()]
body = json.dumps(data)

url = f"https://{resourceGroupName}a1l45.azure-api.net/function/"
data = {"inputs": body}
# headers = {"Ocp-Apim-Subscription-Key": ""} # if auth enabled

response = requests.post(url, json=data)
# response = requests.post(url, json=data, headers=headers)

print(response)
print(round(json.loads(response.text)[0][0], 2))
