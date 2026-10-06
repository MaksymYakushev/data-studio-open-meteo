from google.cloud import bigquery

client = bigquery.Client()

print("Connected to BigQuery!")
print(f"Project: {client.project}")