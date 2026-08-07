# Authentication Architecture

## Current Authentication Model

**Server-Side Authentication Only**

This application uses server-side authentication via InsForge API key, not traditional user authentication. The backend handles all authentication using a server-only API key, while the frontend provides a demo user flow.

## How It Works

### Backend Authentication
- **InsForge API Key**: Server-side authentication using `INSFORGE_API_KEY`
- **No User Auth**: The backend doesn't implement user login/signup
- **API Key Storage**: Stored in `.env` file (server-only, never exposed to browser)
- **Request Authorization**: All InsForge requests use `Authorization: Bearer {api_key}` header

### Frontend Flow
- **Demo Signup**: Frontend signup form is for demo purposes only
- **No Real Auth**: User data is collected but not used for authentication
- **Flow Control**: Signup just determines user type (individual/organization) for UI routing
- **Direct Access**: Users can access features without real authentication

## Configuration

### Required Environment Variables
```bash
INSFORGE_URL=https://cgjubsx4.ap-southeast.insforge.app
INSFORGE_API_KEY=ik_6b5cf92bed17229c5f0fc266c7e2dbec
```

### How InsForge Client Works
```python
# src/insforge_client.py
class InsForgeRepository:
    def __init__(self):
        self.api_key = os.getenv("INSFORGE_API_KEY")
        self.base_url = os.getenv("INSFORGE_URL")
        
    def _request(self, method, table, **kwargs):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        # Make authenticated request to InsForge
```

## Security Considerations

### Current Implementation
- ✅ API key is server-only (never sent to browser)
- ✅ No user credentials stored in client
- ✅ All database access authenticated via server key
- ⚠️ No user authentication (anyone can use the system)

### Production Requirements
For production deployment, you would need:
1. **User Authentication**: Implement proper user login/signup
2. **Session Management**: JWT tokens or session cookies
3. **Permission System**: Role-based access control
4. **API Key Protection**: Ensure API key is never exposed
5. **Rate Limiting**: Prevent abuse of the system

## Upload Performance Issues

### Current Upload Flow
1. **Frontend**: File selected → Upload to backend
2. **Backend**: Upload to GCS → Groq transcription → AI extraction
3. **Timing**: 2-5 minutes for typical meeting recording

### Performance Bottlenecks
1. **GCS Upload**: Network dependent, can be slow
2. **Groq Transcription**: API rate limits, processing time
3. **AI Extraction**: LLM response time
4. **No Progress Tracking**: Backend doesn't provide real-time progress

### Optimizations Applied
- **5-minute timeout**: Prevents indefinite waiting
- **Better error messages**: Clear feedback on failures
- **Fallback handling**: Local storage if GCS fails
- **Simulated progress**: UI shows progress during upload

### Further Optimizations Needed
- **Real progress tracking**: Backend should provide actual upload progress
- **Chunked uploads**: Upload large files in chunks
- **Background processing**: Process transcription asynchronously
- **Caching**: Cache transcriptions for repeated uploads

## Testing Authentication

### Verify InsForge Connection
```bash
# Check backend health
curl http://localhost:8000/health

# Expected response: {"status":"ok","dry_run":true}
```

### Test Upload Flow
1. Go to http://localhost:3001
2. Click "Get Started"
3. Fill in signup form (demo only)
4. Select "Individual"
5. Upload a video file
6. Check if upload completes successfully

### Common Issues

**Upload Timeout**
- Cause: File too large or network slow
- Solution: Try smaller file, check network connection

**Server Unavailable (503/502)**
- Cause: Backend services not configured
- Solution: Check GCS, Groq, InsForge credentials in .env

**Authentication Errors**
- Cause: Invalid InsForge API key
- Solution: Verify INSFORGE_API_KEY in .env file

## Migration to Production Authentication

To implement proper user authentication:

1. **Add User Table to InsForge**
   ```sql
   CREATE TABLE users (
     id UUID PRIMARY KEY,
     email TEXT UNIQUE,
     password_hash TEXT,
     name TEXT,
     account_type TEXT,
     created_at TIMESTAMP
   )
   ```

2. **Implement Auth Endpoints**
   ```python
   @app.post("/auth/signup")
   async def signup(user_data: UserSignup):
       # Hash password, create user in InsForge
       
   @app.post("/auth/login")
   async def login(credentials: UserLogin):
       # Verify credentials, return JWT token
   ```

3. **Add JWT Middleware**
   ```python
   def verify_jwt_token(token: str):
       # Validate JWT, return user info
   ```

4. **Update Frontend**
   - Store JWT token in localStorage
   - Include token in all API requests
   - Add login/signup pages
   - Protect routes with authentication

## Current Status

**Authentication**: Demo mode (no real user auth)
**Upload**: Working with 5-minute timeout
**Backend**: Running with InsForge API key
**Frontend**: Demo signup flow for UI routing only

**Note**: This is acceptable for the buildathon demo but would need proper authentication for production use.
