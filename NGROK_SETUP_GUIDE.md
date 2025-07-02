# Angel One API OAuth Setup Guide - AUTO-NGROK ENABLED! 🚀

## ✅ AUTOMATIC SOLUTION IMPLEMENTED!

**Your Django app now automatically starts ngrok and handles all URL configuration!**

### 🎉 Just Run One Command:

```powershell
python manage.py runserver
```

**OR double-click:** `start_trading_platform.bat`

### 🤖 What Happens Automatically:

1. ✅ Django server starts on localhost:8000
2. ✅ Ngrok tunnel automatically starts
3. ✅ Public HTTPS URL created (like `https://abc123.ngrok.io`)
4. ✅ Django settings updated with public callback URL
5. ✅ Angel One API calls now work from anywhere!

### 📋 Your Angel One Portal Configuration:

- **API Key:** `xhMChjlS`
- **Secret Key:** `78e4798a-f35b-481f-9804-ff78557f99ed`
- **Redirect URL:** Will be displayed when you start the server

---

## Problem SOLVED ✅
Angel One API portal shows "Please enter valid url" when you try to use:
`http://localhost:8000/api/angel/auth/callback/`

This happens because most OAuth providers don't accept localhost URLs.

## ⚠️ IMPORTANT: Session Limit Fix

**If you get "Your account is limited to 1 simultaneous ngrok agent sessions" error:**

1. **Kill existing ngrok processes:**
   ```powershell
   taskkill /f /im ngrok.exe
   ```

2. **Then start fresh:**
   ```powershell
   ngrok http 8000
   ```

3. **Free accounts only allow 1 tunnel at a time!**

---

## 🚀 AUTOMATIC Solution: Auto-Ngrok Integration

### Method 1: Automated Setup (Recommended)

1. **Make sure Django server is running:**
   ```powershell
   python manage.py runserver
   ```

2. **Double-click `start_ngrok.bat`** or run:
   ```powershell
   python setup_ngrok.py
   ```

3. **Copy the generated callback URL** (will look like):
   ```
   https://abc123.ngrok.io/api/angel/auth/callback/
   ```

4. **Use this URL in Angel One portal** instead of localhost

### Method 2: Manual ngrok Setup

1. **Install ngrok:**
   ```powershell
   winget install ngrok.ngrok
   ```

2. **Get auth token:**
   - Go to https://ngrok.com
   - Sign up/login
   - Copy your auth token from dashboard

3. **Configure ngrok:**
   ```powershell
   ngrok config add-authtoken YOUR_TOKEN_HERE
   ```

4. **Start tunnel:**
   ```powershell
   ngrok http 8000
   ```

5. **Copy the HTTPS URL** and append `/api/angel/auth/callback/`

### Method 3: Web Interface

Visit: http://localhost:8000/api/angel/ngrok-setup/
This will automatically set up ngrok and show you the URL.

## Angel One Portal Setup

1. Go to https://smartapi.angelbroking.com/
2. Login with your Angel One credentials
3. Go to your app settings
4. Replace the redirect URL with the ngrok HTTPS URL
5. Save changes

## Testing

After setup:
1. Visit http://localhost:8000/api/angel/setup/ for complete instructions
2. Test the OAuth flow with your new public URL
3. The callback will work properly now

## Troubleshooting

- **"Please enter valid url"**: Make sure you're using HTTPS URL from ngrok
- **Tunnel not working**: Check if auth token is configured correctly
- **Server not running**: Start Django with `python manage.py runserver`

## Alternative Methods

If ngrok doesn't work:
- Visit http://localhost:8000/api/angel/url-config/ for other URL options
- Use cloud deployment (Heroku, Railway, etc.)
- Edit hosts file to create custom domain

## Files Created

- `setup_ngrok.py` - Python script for ngrok setup
- `start_ngrok.bat` - Windows batch file for easy setup
- This guide: `NGROK_SETUP_GUIDE.md`

The ngrok tunnel creates a secure bridge between your localhost and a public URL that Angel One will accept for OAuth callbacks.
