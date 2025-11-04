# SSL Certificate Troubleshooting

## Overview

If you encounter SSL certificate verification errors when connecting to video generation APIs, this guide will help you diagnose and resolve the issue.

## Error Symptoms

You might see errors like:

```
SSLError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate
```

or

```
RuntimeError: SSL certificate verification failed. Cannot connect to RunwayML API.
```

## Common Causes

### 1. Corporate Firewall/Proxy

Many corporate networks use "SSL inspection" or "man-in-the-middle" proxies that intercept HTTPS connections. This breaks normal SSL certificate verification.

**Solution**: Contact your IT department to:
- Get the corporate root certificate
- Configure your system to trust it
- Or request an exception for video generation API endpoints

### 2. Missing or Outdated System CA Certificates

Python uses the `certifi` package to verify SSL certificates. If this is outdated or missing, verification fails.

**Solution**:

```bash
# Update certifi
pip install --upgrade certifi

# On macOS, also run the certificate installer
/Applications/Python\ 3.x/Install\ Certificates.command
```

Replace `3.x` with your Python version (e.g., `3.11`, `3.12`, `3.14`).

### 3. Antivirus Software Interference

Some antivirus programs (Norton, Kaspersky, Avast, etc.) intercept SSL connections for scanning, which can break certificate verification.

**Solution**:
- Check your antivirus settings
- Add exceptions for Python or the video generation APIs
- Temporarily disable SSL scanning to test

### 4. Python Installation Issues

On some systems (especially macOS), Python may not be configured to use system certificates properly.

**Solution for macOS**:

```bash
# Install certificates for your Python version
cd "/Applications/Python 3.x"
./Install Certificates.command

# Or use Homebrew Python which handles this automatically
brew install python
```

### 5. Network Issues

VPNs, proxies, or network configurations may interfere with SSL.

**Solution**:
- Try on a different network
- Disable VPN temporarily
- Check proxy settings

## Environment Variable Solutions

### Option 1: Use Custom CA Bundle

If you have a custom certificate bundle (e.g., from corporate IT):

```bash
export REQUESTS_CA_BUNDLE=/path/to/your/cacert.pem
```

Add to your `.env` file:

```bash
REQUESTS_CA_BUNDLE=/path/to/corporate-certs.pem
```

### Option 2: Use System Certificates

```bash
export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt  # Linux
export REQUESTS_CA_BUNDLE=/etc/ssl/cert.pem                   # macOS
```

### Option 3: Disable Verification (NOT RECOMMENDED)

⚠️ **Only for testing/debugging. Never use in production!**

```bash
export CURL_CA_BUNDLE=""
export REQUESTS_CA_BUNDLE=""
```

## Verification Steps

### 1. Check certifi

```bash
python -c "import certifi; print(certifi.where())"
```

This shows where Python looks for CA certificates.

### 2. Test HTTPS Connection

```bash
python -c "import requests; requests.get('https://api.openai.com')"
```

If this works but video generation fails, the issue is specific to the video API endpoints.

### 3. Check Certificate Chain

```bash
openssl s_client -connect api.dev.runwayml.com:443 -showcerts
```

This shows the certificate chain. Look for verification errors.

## Provider-Specific Notes

### RunwayML (api.dev.runwayml.com)

RunwayML uses standard SSL certificates. If you get errors:

1. Verify the domain resolves: `nslookup api.dev.runwayml.com`
2. Check connectivity: `curl -v https://api.dev.runwayml.com`
3. Update certificates as described above

### OpenAI Sora (api.openai.com)

OpenAI's certificates should be trusted by default. Issues usually indicate:
- Outdated certifi package
- Corporate proxy interference
- System certificate store issues

### Google Veo

Google's Python SDK handles certificates automatically. SSL errors are rare but may occur if:
- Google Cloud SDK is outdated: `gcloud components update`
- System certificates are corrupted

### Azure Sora

Azure uses Microsoft's certificate infrastructure. Issues may indicate:
- Azure CLI needs updating: `az upgrade`
- Corporate network interference
- Regional certificate trust issues

## Getting Help

If none of these solutions work:

1. **Check the logs**: Look in `logs/video_gen.log` for detailed error messages
2. **Test other HTTPS sites**: Verify your Python installation can connect to other HTTPS endpoints
3. **Contact IT support**: If in a corporate environment, SSL issues often require IT assistance
4. **File an issue**: Include:
   - Operating system and Python version
   - Output of `python -c "import certifi; print(certifi.where())"`
   - Full error traceback
   - Network environment (corporate, home, VPN, etc.)

## Additional Resources

- [Python Requests SSL Documentation](https://requests.readthedocs.io/en/latest/user/advanced/#ssl-cert-verification)
- [certifi Documentation](https://github.com/certifi/python-certifi)
- [macOS Python Certificate Issues](https://stackoverflow.com/questions/42098126/mac-osx-python-ssl-sslerror-ssl-certificate-verify-failed-certificate-verify)
