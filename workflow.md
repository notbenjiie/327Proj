The repository must also include:

• an explanation of how the system connects to and retrieves data from the relevants ources: 

the system connects via dataniz's data sharing feature which allows two broker accounts to share topics to one another and have any data generated on each respected account, show up in the individuals neondb database. dataniz -> neondb connection is intergrated into dataniz so that's self explanatory, just used the connection link from neondb to connect to dataniz.
 
• how distributed query processing was implemented

We used a P2P coordinator model. When a server receives a query, it acts as a coordinator: it pulls local data from the Neon DB and simultaneously opens a TCP socket to the partner server to request their data. Both datasets are then aggregated into a Linked List for a unified final calculation.

• how query completeness was determined

query completeness was determined on whether or not the question was actually entered properly as well as the response came back from server and then outputted to client. Completeness is handled through fault tolerant aggregation. The system attempts to contact all nodes (local + partner) and if a partner server is unreachable, the system catches the timeout and falls back to the replicated shared database in Neon, ensuring the query results are as complete as possible even during a network failure.

• and how DataNiz metadata and data sharing were used.

Using metadata: analyzing the payload JSON files from neondb allowed us to code for which features we needed for each specific query. For example the dishwasher only looked at the water sensor's output for both House's and then averaged them, ignoring the ammeter outputted data that can be found in the same payload. Ownership was determined using MQTT Topic Metadata. By parsing the email addresses within the topic field of the JSON payloads, the system logically separated data into "House A" and "House B." This metadata allowed both houses to share a single database table while still enabling house level electricity and moisture/water analysis.
