from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import pickle

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

flow = InstalledAppFlow.from_client_secrets_file('Oauth.json', SCOPES)
creds = flow.run_local_server(port=0)

# Save the credentials for later use
with open('token.pickle', 'wb') as token:
    pickle.dump(creds, token)

print("Authentication complete. Token saved to token.pickle")
