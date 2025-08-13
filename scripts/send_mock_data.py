
from azure.eventhub import EventHubProducerClient, EventData
import json, time, random

CONNECTION_STR = "Endpoint=sb://$eventHubNamespace.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=your-key"  # Get from Portal
EVENT_HUB_NAME = "$eventHubName"

producer = EventHubProducerClient.from_connection_string(CONNECTION_STR, eventhub_name=EVENT_HUB_NAME)
for i in range(100):
    event_data = EventData(json.dumps({"productID": random.randint(1, 10), "quantity": random.randint(1, 5), "price": random.uniform(10, 100), "timestamp": time.time()}))
    producer.send_batch([event_data])
    time.sleep(1)
producer.close()
