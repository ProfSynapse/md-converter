# Architecture Summary: Google Docs Integration

**Document Version**: 1.0
**Date**: 2025-11-01
**Phase**: PACT Architecture
**Status**: Ready for Implementation

---

## Overview

This document provides an executive summary of the architecture for integrating Google Docs conversion with OAuth2 authentication into the markdown converter application. It references the detailed architecture documents and provides implementation guidance.

---

## Architecture Documents

### Complete Documentation Set

All architecture documents are located in `/Users/jrosenbaum/Documents/Code/md-converter/docs/architecture/`:

1. **01-system-architecture-google-docs.md**
   - High-level system design
   - Component architecture
   - Data flow diagrams
   - Security architecture
   - Deployment architecture
   - Scalability considerations

2. **02-oauth2-authentication-design.md**
   - OAuth2 flow specifications
   - Session management design
   - Flask-Dance integration
   - Token lifecycle management
   - Error handling
   - Security considerations

3. **03-google-docs-converter-design.md**
   - GoogleDocsConverter class design
   - Markdown-to-Docs API mapping
   - Front matter handling
   - Service client caching
   - Performance optimization

4. **04-api-endpoint-design.md**
   - Updated `/api/convert` endpoint
   - Multi-format request/response
   - Authentication endpoints
   - Backward compatibility strategy
   - Error response standards

---

## Key Architectural Decisions

### 1. OAuth2 as Primary Authentication

**Decision**: Use OAuth2 "Sign in with Google" as the primary authentication method

**Rationale**:
- Documents owned by users (not service account)
- No persistent user data storage required
- Natural quota scaling (60 writes/min per user)
- Privacy-first approach (GDPR compliant)
- Frictionless UX with Google sign-in

**Implementation**: Flask-Dance with session-based token storage (encrypted cookies)

### 2. Session-Based Token Storage

**Decision**: Store OAuth tokens in Flask session cookies instead of database

**Rationale**:
- No database dependency
- Stateless architecture
- Works with Railway's horizontal scaling
- Automatic session expiration
- Simpler deployment

**Trade-offs**: Cookie size limited to 4KB (acceptable - tokens ~1-2KB)

### 3. Multi-Format Selection UI

**Decision**: Replace dropdown with icon-based tile selection allowing multiple formats

**Rationale**:
- Modern UX pattern (2025 best practices)
- Larger touch targets (mobile-friendly)
- Visual clarity with icons
- Reduces repeated conversions
- Aligns with user expectations

**Implementation**: Tailwind CSS selectable cards with checkboxes

### 4. Backward API Compatibility

**Decision**: Support both legacy `format` parameter and new `formats` array

**Rationale**:
- No breaking changes for existing clients
- Gradual migration path
- Maintains existing functionality
- Easy rollback if needed

**Migration**: Phase out legacy parameter after 12 months

### 5. markgdoc Library for Conversion

**Decision**: Use markgdoc library for markdown-to-Docs conversion

**Rationale**:
- Rapid implementation (10-15 hours vs 25-35 hours)
- Actively maintained (updated August 2024)
- Handles common markdown elements
- Extensible for custom requirements

**Trade-offs**: GPL v3 license (acceptable for most use cases)

---

## System Architecture Overview

### High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Browser (User Agent)                      │
│  - File upload component                                     │
│  - Format selection tiles (DOCX, PDF, Google Docs)          │
│  - Authentication status badge                               │
│  - Sign in/out buttons                                       │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Flask Application (Railway)                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Application Factory                                  │  │
│  │  - OAuth2 blueprint (Flask-Dance)                     │  │
│  │  - API blueprint                                      │  │
│  │  - Auth blueprint                                     │  │
│  │  - Error handlers                                     │  │
│  │  - Security headers                                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Conversion Services                                  │  │
│  │  - MarkdownConverter (DOCX, PDF) - Existing          │  │
│  │  - GoogleDocsConverter - NEW                         │  │
│  │  - OAuth2 helpers - NEW                              │  │
│  │  - Google API service builders - NEW                 │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    External Services                         │
│  - Google OAuth2 (authentication)                           │
│  - Google Docs API v1 (document creation)                   │
│  - Google Drive API v3 (permissions, links)                 │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User uploads markdown** → File validated → Content parsed
2. **User selects formats** → Multi-select tiles (DOCX, PDF, Google Docs)
3. **If Google Docs selected** → Check authentication → Redirect if needed
4. **Conversion process**:
   - DOCX: pypandoc → Local file → Download URL
   - PDF: weasyprint → Local file → Download URL
   - Google Docs: Docs API → User's Drive → Share link
5. **Response returned** → JSON with all requested formats

---

## Implementation Roadmap

### Phase 1: Dependencies and Configuration (Week 1)

**Tasks**:
- [ ] Install Flask-Dance (`pip install Flask-Dance`)
- [ ] Install Google API libraries
- [ ] Install markgdoc (optional)
- [ ] Create Google Cloud Project
- [ ] Configure OAuth consent screen
- [ ] Create OAuth client credentials
- [ ] Set up Railway environment variables

**Deliverables**:
- Updated requirements.txt
- OAuth credentials configured
- Environment variables sealed in Railway

### Phase 2: OAuth2 Implementation (Week 2)

**Tasks**:
- [ ] Create auth blueprint (`app/auth/`)
- [ ] Register Flask-Dance Google blueprint
- [ ] Implement `/auth/status` endpoint
- [ ] Implement `/auth/logout` endpoint
- [ ] Add OAuth helpers (`app/utils/oauth_helpers.py`)
- [ ] Update session configuration
- [ ] Write unit tests

**Deliverables**:
- Working OAuth flow
- Session-based token storage
- Authentication status API

### Phase 3: Google Docs Converter (Week 2-3)

**Tasks**:
- [ ] Create GoogleDocsConverter class
- [ ] Implement markdown parsing
- [ ] Integrate markgdoc library
- [ ] Add front matter formatting
- [ ] Create Google API service builder
- [ ] Implement error handling
- [ ] Write unit tests

**Deliverables**:
- GoogleDocsConverter class
- Google API integration
- Conversion tests passing

### Phase 4: API Endpoint Updates (Week 3)

**Tasks**:
- [ ] Update `/api/convert` for multi-format
- [ ] Add authentication checks
- [ ] Implement backward compatibility
- [ ] Add Google Docs error handling
- [ ] Update response structure
- [ ] Write integration tests

**Deliverables**:
- Updated API endpoint
- Multi-format support
- Backward compatibility maintained

### Phase 5: Frontend UI (Week 3-4)

**Tasks**:
- [ ] Design format selection tiles
- [ ] Implement with Tailwind CSS
- [ ] Add authentication status display
- [ ] Create "Sign in with Google" button
- [ ] Implement JavaScript for auth checking
- [ ] Add selection counter
- [ ] Test accessibility (WCAG 2.2 AA)

**Deliverables**:
- Modern format selection UI
- Authentication integration
- Responsive design
- Accessibility compliant

### Phase 6: Testing and Deployment (Week 4-5)

**Tasks**:
- [ ] Run full test suite
- [ ] Manual end-to-end testing
- [ ] Deploy to Railway staging
- [ ] Update OAuth redirect URIs
- [ ] Test in production
- [ ] Monitor logs and metrics
- [ ] Deploy to production

**Deliverables**:
- All tests passing
- Production deployment
- Monitoring in place

---

## Technical Specifications

### New Dependencies

```txt
# OAuth2 authentication
Flask-Dance>=7.0.0

# Google API integration
google-api-python-client>=2.149.0
google-auth>=2.35.0
google-auth-oauthlib>=1.2.3

# Markdown to Google Docs conversion (optional but recommended)
markgdoc==1.0.1
```

### Environment Variables

**Required**:
```bash
SECRET_KEY=<64-char-hex-string>  # SEALED
GOOGLE_OAUTH_CLIENT_ID=<client-id>.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=<client-secret>  # SEALED
GOOGLE_CLOUD_PROJECT_ID=<project-id>
OAUTHLIB_RELAX_TOKEN_SCOPE=true
OAUTHLIB_INSECURE_TRANSPORT=false  # Production
```

**Existing** (No Changes):
```bash
FLASK_ENV=production
LOG_LEVEL=INFO
MAX_FILE_SIZE=10485760
CONVERTED_FOLDER=/tmp/converted
```

### New Files to Create

```
app/
├── auth/
│   ├── __init__.py          # Auth blueprint
│   └── routes.py            # Auth endpoints
├── converters/
│   └── google_docs_converter.py  # GoogleDocsConverter class
└── utils/
    ├── oauth_helpers.py     # OAuth utility functions
    └── google_services.py   # Google API service builders

static/
└── css/
    └── format-selection.css # Format tile styles (if not using Tailwind CDN)

templates/
└── index.html               # Updated with format selection tiles
```

### Files to Modify

```
app/
├── __init__.py              # Register OAuth blueprint
├── api/routes.py            # Update /api/convert endpoint
└── config.py                # Add OAuth configuration

requirements.txt             # Add new dependencies
```

---

## Security Checklist

### OAuth2 Security

- [ ] SECRET_KEY is strong (32+ bytes, cryptographically random)
- [ ] SECRET_KEY is stable across deployments
- [ ] SECRET_KEY is sealed in Railway
- [ ] GOOGLE_OAUTH_CLIENT_SECRET is sealed in Railway
- [ ] SESSION_COOKIE_HTTPONLY=True
- [ ] SESSION_COOKIE_SECURE=True (production)
- [ ] SESSION_COOKIE_SAMESITE='Lax'
- [ ] HTTPS enforced (automatic in Railway)

### API Security

- [ ] Input validation on all endpoints
- [ ] File type validation (.md, .markdown only)
- [ ] File size limits enforced
- [ ] UTF-8 encoding validation
- [ ] Path traversal protection
- [ ] Rate limiting for Google Docs (graceful handling)

### Privacy & Compliance

- [ ] No persistent user data storage
- [ ] Sessions expire on browser close
- [ ] OAuth tokens not logged
- [ ] User can revoke access via Google
- [ ] Clear privacy policy
- [ ] GDPR compliant (session-only storage)

---

## Performance Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| OAuth login | < 1s | Google redirect |
| DOCX conversion | < 3s | Existing performance |
| PDF conversion | < 5s | Existing performance |
| Google Docs | < 4s | API latency + formatting |
| Multi-format (all 3) | < 8s | Sequential (can parallelize) |

### Optimization Opportunities

**Service Client Caching**:
- Cache Google API clients per token
- Reduces initialization time from 200-300ms to ~0ms

**Parallel Conversion** (Future Enhancement):
- Convert to all formats in parallel
- Reduce total time from 12s to 5s (60% improvement)

---

## Monitoring and Observability

### Key Metrics

**Authentication**:
- OAuth login attempts
- OAuth success/failure rate
- Active authenticated users
- Token refresh rate

**Conversions**:
- Conversions per format
- Google Docs conversion rate
- Average conversion time
- Error rates by format

**Performance**:
- API response times
- Google API latency
- Session size
- Rate limit approaching events

### Logging Strategy

**OAuth Events**:
```python
logger.info("OAuth login initiated")
logger.info("OAuth callback successful")
logger.warning("OAuth token expired, refreshing")
logger.error("OAuth authentication failed")
```

**Conversion Events**:
```python
logger.info("Google Docs conversion started: job_id=...")
logger.info("Document created: doc_id=...")
logger.warning("Rate limit approaching")
logger.error("Google API error", exc_info=True)
```

### Health Check

```bash
curl https://your-app.railway.app/health

{
  "status": "healthy",
  "features": {
    "docx_conversion": true,
    "pdf_conversion": true,
    "google_docs_conversion": true,
    "oauth_configured": true
  }
}
```

---

## Testing Strategy

### Unit Tests

**Components to Test**:
- OAuth flow state management
- Token refresh logic
- Multi-format parameter parsing
- GoogleDocsConverter methods
- API request construction

**Coverage Target**: 80%+

### Integration Tests

**Scenarios**:
- OAuth flow end-to-end
- Multi-format conversion (authenticated)
- Google Docs without auth (should fail)
- Backward compatibility (legacy parameters)
- Error handling (rate limit, auth failure)

### Manual Testing

**Test Plan**:
1. Sign in with Google → Verify session created
2. Select Google Docs format → Convert → Verify document in Drive
3. Select all formats → Convert → Verify all outputs
4. Sign out → Verify Google Docs disabled
5. Test responsive UI on mobile
6. Test keyboard navigation
7. Test screen reader compatibility

---

## Deployment Checklist

### Pre-Deployment

- [ ] All tests passing
- [ ] Code reviewed
- [ ] Security audit completed
- [ ] Environment variables configured
- [ ] OAuth redirect URIs updated
- [ ] Secrets sealed in Railway

### Deployment

- [ ] Deploy to Railway staging
- [ ] Test OAuth flow in staging
- [ ] Verify conversions work
- [ ] Check logs for errors
- [ ] Deploy to production
- [ ] Update OAuth redirect URIs (production)
- [ ] Test production deployment

### Post-Deployment

- [ ] Monitor logs for errors
- [ ] Track conversion success rate
- [ ] Monitor Google API quota usage
- [ ] Collect user feedback
- [ ] Plan service account implementation (optional Phase 2)

---

## Risk Mitigation

### Identified Risks

| Risk | Mitigation |
|------|-----------|
| OAuth verification delay (4-6 weeks) | Use test users during development |
| User revokes OAuth mid-session | Graceful error handling, clear messaging |
| Google API rate limits | Per-user quotas, retry logic, user feedback |
| Token expiration during conversion | Automatic refresh before API calls |
| SECRET_KEY regeneration | Sealed Railway variable, documentation |

---

## Success Criteria

### Functional

- [ ] Users can sign in with Google
- [ ] Markdown converts to Google Docs with proper formatting
- [ ] Documents created in user's Drive
- [ ] Multi-format selection works
- [ ] Existing DOCX/PDF conversions unchanged

### Non-Functional

- [ ] OAuth login < 5 seconds
- [ ] Google Docs conversion < 4 seconds
- [ ] Session cookies < 4KB
- [ ] Zero persistent user data
- [ ] WCAG 2.2 AA compliant
- [ ] Mobile responsive

### Business

- [ ] No additional infrastructure costs
- [ ] Scales with user growth
- [ ] Privacy compliant (GDPR)
- [ ] No Google verification required initially

---

## Next Steps

### Immediate Actions

1. **Review architecture documents** with development team
2. **Set up Google Cloud Project** and OAuth credentials
3. **Configure Railway environment** variables
4. **Begin Phase 1 implementation** (dependencies and configuration)

### Implementation Order

Follow the phased roadmap in this document:
1. Dependencies and Configuration (Week 1)
2. OAuth2 Implementation (Week 2)
3. Google Docs Converter (Week 2-3)
4. API Endpoint Updates (Week 3)
5. Frontend UI (Week 3-4)
6. Testing and Deployment (Week 4-5)

### Support Resources

**Architecture Documents**:
- System Architecture: `01-system-architecture-google-docs.md`
- OAuth2 Design: `02-oauth2-authentication-design.md`
- Converter Design: `03-google-docs-converter-design.md`
- API Design: `04-api-endpoint-design.md`

**Preparation Documents** (in `docs/preparation/`):
- OAuth2 Implementation Guide
- Markdown to Docs Conversion
- Python Libraries
- Deployment Configuration
- UI Format Selection Patterns

---

## Contact and Questions

For questions about this architecture:
1. Review detailed architecture documents listed above
2. Check preparation documentation in `docs/preparation/`
3. Consult existing implementation in `docs/BACKEND_IMPLEMENTATION_SUMMARY.md`

---

**Architecture Phase Status**: COMPLETE
**Ready for Code Phase**: YES
**Estimated Implementation Time**: 4-5 weeks
**Next Phase**: Delegate to appropriate PACT specialists (backend, frontend) for implementation
