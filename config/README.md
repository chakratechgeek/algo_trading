# Configuration Directory

This directory contains sensitive configuration files that are **NOT** committed to git.

## Setup

1. **Copy the template:**
   ```bash
   python setup_credentials.py
   ```

2. **Edit your credentials:**
   ```bash
   # Edit config/secrets.py with your actual API keys
   ```

3. **Verify setup:**
   ```bash
   python setup_credentials.py check
   ```

## Files

- `secrets.py.template` - Template file with placeholder values
- `secrets.py` - **Your actual credentials (gitignored)**
- `__init__.py` - Python package file

## Security

- ✅ `secrets.py` is gitignored and will not be committed
- ✅ Only template files are tracked in git
- ✅ All scripts have fallback imports for compatibility

## Required Credentials

### AngelOne API
- `API_KEY` - Your AngelOne API key
- `CLIENT_CODE` - Your AngelOne client code
- `WEB_PASSWORD` - Your AngelOne web password
- `MPIN` - Your AngelOne MPIN
- `TOTP_SECRET` - Your AngelOne TOTP secret key
- `SECRET_KEY` - Your AngelOne secret key

### Additional APIs
- `NGROK_AUTH_TOKEN` - Ngrok authentication token
- `TOGETHER_API_KEY` - Together AI API key
- `DJANGO_SECRET_KEY` - Django secret key

## Migration from Old Structure

If you had `credentials.py` in the root directory:

1. Run the setup script: `python setup_credentials.py`
2. Copy values from old `credentials.py` to new `config/secrets.py`
3. Test that everything works
4. Delete the old `credentials.py` file

## Troubleshooting

If you get import errors:
1. Make sure `config/secrets.py` exists
2. Check that all required fields are filled in
3. Run: `python setup_credentials.py check`
