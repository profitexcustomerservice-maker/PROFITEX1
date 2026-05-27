# Django Production Authentication Fix - Implementation Summary

## Overview
Fixed 403 Forbidden errors on protected API endpoints in Render production by implementing proper JWT token handling in the frontend.

## Root Cause Analysis
The application was returning 403 Forbidden errors on:
- `GET /api/auth/me/` - Current user profile
- `GET /api/notifications/` - User notifications

**Root Cause:** Frontend was making API calls using session-based authentication (Django sessions) via `credentials: 'same-origin'`, but the API endpoints required JWT Bearer tokens for authentication in production environments where sessions may not persist across requests.

## Solution Implemented

### 1. Backend Changes

#### New API Endpoint: `/api/auth/jwt/`
**File:** `accounts/views.py`
**Change:** Added `GetJWTTokenView` class
- Generates JWT tokens for authenticated users
- Accepts both GET and POST requests
- Returns access token, refresh token, user_id, and email
- Requires `IsAuthenticated` permission

**Usage:**
```bash
curl -X GET https://novaprofit.onrender.com/api/auth/jwt/ \
  -H "Cookie: sessionid=..." \
  -H "Accept: application/json"
```

Response:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user_id": 123,
  "email": "user@example.com"
}
```

#### Enhanced CORS Configuration
**File:** `novaprofit/settings.py`
**Changes:**
- Added explicit `CORS_ALLOW_HEADERS` including 'authorization'
- Added `CORS_EXPOSE_HEADERS` for proper header exposure
- Configured `CORS_ALLOW_CREDENTIALS` for both dev and production
- Maintained per-environment CORS origin whitelisting

### 2. Frontend Changes

#### TokenManager Object
**File:** `templates/base.html`
**Change:** Added TokenManager for JWT token management

Features:
- `getAccessToken()` - Retrieve access token from localStorage
- `getRefreshToken()` - Retrieve refresh token from localStorage
- `setTokens(access, refresh)` - Store tokens in localStorage
- `clearTokens()` - Clear stored tokens
- `isAuthenticated()` - Check if user has valid token

#### Enhanced apiFetch Function
**File:** `templates/base.html`
**Changes:**
- Now retrieves JWT token from localStorage
- Automatically adds `Authorization: Bearer <token>` header to all API requests
- Maintains CSRF token support for legacy requests
- Falls back gracefully if no token available

#### ensureJWTTokens Function
**File:** `templates/base.html`
**New Function:** Checks if JWT tokens exist in localStorage
- If tokens exist, resolves immediately
- If not, fetches tokens from `/api/auth/jwt/` endpoint
- Stores retrieved tokens in localStorage for future use
- Handles errors gracefully (user may not be logged in)

#### Updated Data Loading Functions
**File:** `templates/base.html`
**Changes to:**
- `loadUserData()` - Now calls `ensureJWTTokens()` before fetching `/api/auth/me/`
- `loadNotificationCount()` - Now calls `ensureJWTTokens()` before fetching `/api/notifications/`

#### Authentication Detection
**File:** `templates/base.html`
**New Code:** Adds 'authenticated' class to body element
- On page load, checks for JWT token or retrieves from server
- Sets `body.authenticated` class if user is logged in
- Allows conditional loading of authenticated content

#### fetch() → apiFetch() Conversions
Updated the following templates to use `apiFetch()` instead of raw `fetch()`:
- `templates/dashboard.html` - Dashboard data and transactions
- `templates/notifications.html` - Notification loading and marking as read
- `templates/plans.html` - Subscriptions and available plans
- `templates/tasks.html` - Task list and completed tasks
- `templates/task_detail.html` - Individual task details
- `templates/admin/base.html` - Admin apiFetch function enhanced

#### Added Authentication Checks
**File:** `templates/base.html`
**New Function:** `isUserAuthenticated()`
- Returns true if user has JWT token or 'authenticated' class
- Prevents API calls on public pages when user not logged in
- Prevents console errors on homepage for anonymous users

**Updated:** DOMContentLoaded event listener
- Only calls `loadUserData()` and `loadNotificationCount()` if authenticated
- Still calls `setActiveNavLink()` for all users
- Prevents 403 errors on public pages

## Files Modified

### Python
1. `accounts/views.py`
   - Added RefreshToken import
   - Added GetJWTTokenView class

2. `novaprofit/urls.py`
   - Imported GetJWTTokenView
   - Added `/api/auth/jwt/` endpoint

3. `novaprofit/settings.py`
   - Enhanced CORS configuration with proper headers

### HTML/JavaScript
4. `templates/base.html`
   - Added TokenManager object
   - Enhanced apiFetch() function
   - Added ensureJWTTokens() function
   - Updated loadUserData() and loadNotificationCount()
   - Added isUserAuthenticated() function
   - Added authentication detection on load
   - Updated DOMContentLoaded event listener

5. `templates/dashboard.html`
   - Changed fetch() → apiFetch() (2 instances)

6. `templates/notifications.html`
   - Changed fetch() → apiFetch() (2 instances)

7. `templates/plans.html`
   - Changed fetch() → apiFetch() (2 instances)

8. `templates/tasks.html`
   - Changed fetch() → apiFetch() (2 instances)

9. `templates/task_detail.html`
   - Changed fetch() → apiFetch() (1 instance)

10. `templates/admin/base.html`
    - Enhanced apiFetch() with JWT token support

## How It Works in Production

### Login Flow
1. User logs in via `/login/` (traditional Django form)
2. OTP verification at `/otp/verify/`
3. Django session established on successful OTP verification
4. User redirected to `/dashboard/`

### Token Acquisition (New)
1. Dashboard page loads
2. JavaScript checks if JWT tokens exist in localStorage
3. If not, calls `ensureJWTTokens()` which:
   - Fetches `/api/auth/jwt/` using session cookie
   - Stores returned tokens in localStorage
   - Sets body.authenticated class

### Subsequent API Calls
1. Any apiFetch() call automatically includes:
   - `Authorization: Bearer <access_token>` header
   - CSRF token (for non-GET requests)
2. API authenticates using JWT token from Authorization header
3. Session cookie is also sent (supports dual authentication)
4. Tokens persist in localStorage across page loads

### Token Refresh (Future Enhancement)
Currently, tokens expire after the configured lifetime (default: 60 minutes).
For production, implement:
- Monitor for 401 Unauthorized responses
- Automatically use refresh token to get new access token
- Re-send request with new token

## Production Deployment Checklist

### Environment Variables Required
- `DJANGO_SECRET_KEY` - Set in Render environment
- `ALLOWED_HOSTS` - Include domain (already configured)
- `DEBUG=False` - Set for production
- Optional:
  - `CORS_ALLOWED_ORIGINS` - If restrictive CORS needed
  - `CSRF_TRUSTED_ORIGINS` - If custom domain used
  - `SIMPLE_JWT_ACCESS_TOKEN_LIFETIME_MINUTES` - Default: 60
  - `SIMPLE_JWT_REFRESH_TOKEN_LIFETIME_DAYS` - Default: 7

### Browser LocalStorage
- Ensure localStorage is enabled (required for token storage)
- Tokens stored as:
  - `jwt_access_token` - Access token
  - `jwt_refresh_token` - Refresh token

### Testing Production Authentication

#### Test 1: Login Flow
```bash
# 1. Navigate to https://novaprofit.onrender.com/login/
# 2. Enter credentials
# 3. Verify OTP (check email or debug output)
# 4. Confirm redirect to dashboard
# 5. Verify no 403 errors in browser console
```

#### Test 2: API Endpoints
```bash
# Using curl (after login, with session cookie):
curl -X GET https://novaprofit.onrender.com/api/auth/me/ \
  -H "Cookie: sessionid=<your_session_id>" \
  -H "Authorization: Bearer <your_access_token>"

# Should return 200 with user data
```

#### Test 3: Dashboard Loading
```bash
# 1. Login successfully
# 2. Go to Dashboard
# 3. Open browser DevTools → Console
# 4. Verify no 403 errors
# 5. Verify user data loads:
#    - Wallet balance displays
#    - Notification count shows
#    - Recent transactions visible
```

#### Test 4: Notifications
```bash
# 1. Navigate to /notifications/
# 2. Verify notification list loads
# 3. Try marking notifications as read
# 4. Verify no 403 errors
```

#### Test 5: Anonymous User
```bash
# 1. Visit homepage without logging in
# 2. Verify no console errors
# 3. Verify page loads normally
# 4. Verify API calls not made for authenticated endpoints
```

## Known Behaviors

### localStorage Persistence
- Tokens persist in localStorage even after page refresh
- User remains "authenticated" until tokens expire or localStorage is cleared
- Logging out should clear localStorage tokens

### Dual Authentication
- API supports both Session and JWT authentication
- Session cookie + JWT token can both be present
- API validates JWT first, falls back to session

### Error Handling
- If `/api/auth/jwt/` returns 401, user is not authenticated
- If API returns 403, check:
  1. Access token is valid in localStorage
  2. Token hasn't expired
  3. User has required permissions for endpoint
  4. CORS is properly configured

## Future Enhancements

1. **Automatic Token Refresh**
   - Monitor 401 responses
   - Use refresh token to get new access token
   - Retry original request

2. **Token Expiration Handling**
   - Show "Session expired" notification when token expires
   - Force logout and redirect to login

3. **Security Improvements**
   - Use httpOnly cookies for token storage (if removing localStorage)
   - Implement CSRF protection for SPA
   - Add token rotation

4. **Error Recovery**
   - Automatic retry with exponential backoff
   - User-friendly error messages

## Troubleshooting

### Issue: Still Getting 403 Errors

**Check:**
1. Is localStorage enabled in browser?
2. Are tokens being stored? (Check DevTools → Application → Storage)
3. Is the Authorization header present in network requests? (DevTools → Network)
4. Is the JWT token valid? (Decode at jwt.io)
5. Has the token expired? (Check exp claim in token)

**Solution:**
- Clear localStorage and log out completely
- Log in again to get fresh tokens
- Check Render logs for API errors

### Issue: Tokens Not Storing

**Check:**
1. Browser's localStorage is not disabled
2. TokenManager.setTokens() is being called
3. `/api/auth/jwt/` endpoint returns tokens

**Solution:**
- Check `/api/auth/jwt/` response in Network tab
- Verify endpoint returns both access and refresh tokens
- Check browser console for JavaScript errors

### Issue: API Returns 401 Unauthorized

**Meaning:** Token is invalid or expired

**Check:**
1. Token expiration time (check 'exp' claim in token)
2. Correct token format in Authorization header
3. Token matches the one issued by server

**Solution:**
- Implement token refresh logic (coming soon)
- Or log out and log back in to get new tokens

## Support

For issues with the authentication fix:
1. Check browser DevTools Console for JavaScript errors
2. Check browser DevTools Network tab for API responses
3. Check Render application logs for server-side errors
4. Verify all environment variables are set
5. Verify CORS settings match your domain

---

**Implementation Date:** May 26, 2026
**Status:** Complete and ready for production testing
