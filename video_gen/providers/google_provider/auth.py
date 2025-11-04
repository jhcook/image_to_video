"""
Google authentication helper for gcloud CLI and OAuth2 browser-based login.
"""

import os
import pickle
import sys
import subprocess
from pathlib import Path

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/cloud-platform']
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), 'client_secrets.json')
TOKEN_FILE = os.path.join(os.path.dirname(__file__), 'token.pickle')

def clear_cached_credentials():
	"""
	Clear cached OAuth credentials to force re-authentication.
	
	Returns:
		bool: True if credentials were cleared, False if none existed
	"""
	cleared = False
	if os.path.exists(TOKEN_FILE):
		os.remove(TOKEN_FILE)
		print(f"✅ Cleared cached credentials: {TOKEN_FILE}")
		cleared = True
	else:
		print(f"ℹ️  No cached credentials found at: {TOKEN_FILE}")
	return cleared

def get_gcloud_token():
	"""
	Get access token from gcloud CLI (application default credentials).
	
	Returns:
		str: Access token from gcloud
		
	Raises:
		RuntimeError: If gcloud is not installed or not authenticated
	"""
	try:
		result = subprocess.run(
			['gcloud', 'auth', 'application-default', 'print-access-token'],
			capture_output=True,
			text=True,
			check=True
		)
		token = result.stdout.strip()
		if not token:
			raise RuntimeError("gcloud returned empty token")
		return token
	except FileNotFoundError:
		raise RuntimeError(
			"gcloud CLI not found. Install it from: https://cloud.google.com/sdk/docs/install"
		)
	except subprocess.CalledProcessError as e:
		error_msg = e.stderr.strip() if e.stderr else "Unknown error"
		if "not authenticated" in error_msg.lower() or "login" in error_msg.lower():
			raise RuntimeError(
				"gcloud not authenticated. Run: gcloud auth application-default login"
			)
		raise RuntimeError(f"Failed to get gcloud token: {error_msg}")

def get_google_credentials(use_gcloud=True):
	"""
	Get Google credentials via gcloud CLI or OAuth2 browser-based login.
	
	Args:
		use_gcloud: If True (default), try gcloud first. If False, use OAuth only.
	
	Returns:
		google.auth.credentials.Credentials or str: OAuth2 credentials or gcloud token
		
	Raises:
		RuntimeError: If authentication fails
	"""
	# Try gcloud first (simpler, no setup needed)
	if use_gcloud:
		try:
			token = get_gcloud_token()
			print("✅ Using gcloud authentication")
			# Return a simple object with token attribute for compatibility
			class TokenCreds:
				def __init__(self, token):
					self.token = token
			return TokenCreds(token)
		except RuntimeError as e:
			print(f"⚠️  gcloud authentication failed: {e}")
			print("    Falling back to OAuth browser-based login...")
	
	# Fall back to OAuth browser-based login
	from google_auth_oauthlib.flow import InstalledAppFlow
	from google.auth.transport.requests import Request

	# Check if credentials file exists
	if not os.path.exists(CREDENTIALS_FILE):
		print("\n❌ OAuth credentials file not found!")
		print(f"   Expected: {CREDENTIALS_FILE}")
		print("\n📋 To set up browser-based Google login (one-time setup):")
		print("   1. Go to: https://console.cloud.google.com/apis/credentials")
		print("   2. Create OAuth 2.0 Client ID (Desktop application)")
		print("   3. Download the JSON credentials file")
		print(f"   4. Save it as: {CREDENTIALS_FILE}")
		print("\n   After setup, run this command again and your browser will open")
		print("   for authentication. Credentials will be saved for future use.")
		print("\n💡 Alternative: Use gcloud CLI (no OAuth setup needed):")
		print("   1. Install gcloud: https://cloud.google.com/sdk/docs/install")
		print("   2. Authenticate: gcloud auth application-default login")
		print("   3. Run this script again with --google-login")
		print("\n   See VEO_AUTH_GUIDE.md for detailed setup instructions.\n")
		sys.exit(1)

	print("🔐 Using OAuth browser-based authentication...")
	
	creds = None
	# Load existing token if available
	if os.path.exists(TOKEN_FILE):
		try:
			with open(TOKEN_FILE, 'rb') as token:
				creds = pickle.load(token)
			print("✅ Loaded saved credentials from previous session")
		except Exception as e:
			print(f"⚠️  Failed to load saved credentials: {e}")
			creds = None
	
	# If no valid creds, do browser login
	if not creds or not creds.valid:
		if creds and creds.expired and creds.refresh_token:
			print("🔄 Refreshing expired credentials...")
			creds.refresh(Request())
		else:
			print("🌐 Opening browser for Google authentication...")
			print("   Please sign in and authorize the application.")
			flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
			creds = flow.run_local_server(port=0)
			print("✅ Browser authentication successful!")
		# Save the credentials for next time
		with open(TOKEN_FILE, 'wb') as token:
			pickle.dump(creds, token)
		print(f"💾 Credentials saved to: {TOKEN_FILE}")
		print("   (You won't need to authenticate again until they expire)")
	
	return creds
