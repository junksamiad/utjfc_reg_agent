import json

# Define the new domain name
new_domain = 'utjfc-backend-prod-3.eba-3bpsyeak.eu-north-1.elasticbeanstalk.com'
config_file = 'cloudfront-config.json'

# Load the distribution config
with open(config_file, 'r') as f:
    distribution = json.load(f)

# Extract the ETag and the main config block
etag = distribution['ETag']
config = distribution['DistributionConfig']

# Find and update the API origin domain
for origin in config['Origins']['Items']:
    if origin.get('Id') == 'API-utjfc-backend':
        print(f"Found origin 'API-utjfc-backend'. Changing domain from {origin['DomainName']} to {new_domain}")
        origin['DomainName'] = new_domain
        break
else:
    print("Error: Could not find the origin with Id 'API-utjfc-backend'")
    exit(1)

# Prepare the config for the update command
# The update command needs only the DistributionConfig, not the outer wrapper
with open('cloudfront-config-to-update.json', 'w') as f:
    json.dump(config, f, indent=4)

# We also need the ETag for the --if-match parameter
print(f"Successfully updated config. ETag for update is: {etag}") 