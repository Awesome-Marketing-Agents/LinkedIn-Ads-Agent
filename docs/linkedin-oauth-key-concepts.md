# LinkedIn 3-legged OAuth: Key Developer Concepts

1. **OAuth Flow Steps**
   - Register your app in the LinkedIn Developer Portal.
   - Redirect users to LinkedIn for consent.
   - Handle the authorization code returned to your redirect URI.
   - Exchange the code for an access token.
   - Use the access token for API calls on behalf of the user.

2. **Redirect URI**
   - Must be registered in your LinkedIn app settings.
   - Must match exactly and use HTTPS.

3. **Scopes**
   - Request only the permissions your app truly needs.
   - Users must consent to all requested scopes.

4. **Security**
   - Keep your client secret safe and never expose it in URLs or public code.

5. **State Parameter**
   - Use a unique state value to prevent CSRF attacks.
   - Always validate the state value on return.

6. **Token Expiry**
   - Access tokens are short-lived (typically 60 days).
   - Be prepared to refresh tokens by repeating the flow.

7. **Error Handling**
   - Handle errors for invalid/mismatched client IDs, redirect URIs, scopes, and expired/invalid codes.

8. **User Consent**
   - Users must explicitly approve your app’s requested access.

9. **HTTPS Only**
   - All redirect URIs and API calls must use HTTPS for security.

10. **Testing**
    - Use tools like Postman for initial testing.
    - Implement the flow securely in your production app.

---

## What are Authorized Redirect URLs?

Authorized redirect URLs are the specific web addresses (URLs) you register in your LinkedIn app settings. After a user approves or denies your app’s access request during the OAuth process, LinkedIn will redirect the user to one of these URLs with an authorization code or error message.

### Why are they important?
- They ensure only trusted, pre-approved URLs can receive sensitive authorization codes.
- They prevent attackers from intercepting tokens by redirecting to malicious sites.

### Example
Suppose your app runs at https://myapp.com. When setting up OAuth, you register this redirect URL in your LinkedIn Developer Portal:

    https://myapp.com/auth/linkedin/callback

During the OAuth flow, you send users to LinkedIn for login and consent. After they approve, LinkedIn redirects them to:

    https://myapp.com/auth/linkedin/callback?code=AUTH_CODE&state=xyz

If you try to use a different redirect URL (e.g., https://evil.com/callback), LinkedIn will block it because it’s not registered as an authorized redirect URL.

**Tip:**
- Always use HTTPS.
- The redirect URL in your OAuth request must match exactly what you registered in the LinkedIn app settings.
