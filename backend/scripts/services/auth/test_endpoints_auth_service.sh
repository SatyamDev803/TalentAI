GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
AUTH_SERVICE_URL="${AUTH_SERVICE_URL:-http://localhost:8001}"
TEST_PASSWORD="SecurePassword123"
PASSED=0
FAILED=0

# Print header
printf "${BLUE}════════════════════════════════════════════════════════${NC}\n"
printf "${BLUE}🚀 AUTH SERVICE - COMPLETE WORKFLOW TEST${NC}\n"
printf "${BLUE}════════════════════════════════════════════════════════${NC}\n\n"
printf "${CYAN}Service URL: $AUTH_SERVICE_URL${NC}\n\n"

# ==================== STEP 1: HEALTH CHECK ====================
printf "${YELLOW}[STEP 1] Health Check${NC}\n"
printf "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

HEALTH=$(curl -s -X GET "$AUTH_SERVICE_URL/health")
STATUS=$(echo "$HEALTH" | jq -r '.status // empty')

if [ "$STATUS" = "healthy" ]; then
    printf "${GREEN}✅ Service is healthy${NC}\n"
    ((PASSED++))
else
    printf "${RED}❌ Service health check failed${NC}\n"
    ((FAILED++))
    exit 1
fi
printf "\n"

# ==================== STEP 2: REGISTER USERS ====================
printf "${YELLOW}[STEP 2] Register Users${NC}\n"
printf "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

# Register Admin
printf "Registering Admin...\n"
ADMIN_RESPONSE=$(curl -s -X POST "$AUTH_SERVICE_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"'$TEST_PASSWORD'","full_name":"Test Admin","role":"ADMIN"}')

ADMIN_TOKEN=$(echo "$ADMIN_RESPONSE" | jq -r '.access_token // empty')
ADMIN_REFRESH=$(echo "$ADMIN_RESPONSE" | jq -r '.refresh_token // empty')

if [ ! -z "$ADMIN_TOKEN" ] && [ "$ADMIN_TOKEN" != "null" ]; then
    printf "${GREEN}✅ Admin registered${NC}\n"
    ((PASSED++))
else
    printf "${RED}❌ Admin registration failed${NC}\n"
    ((FAILED++))
fi

# Register Recruiter
printf "Registering Recruiter...\n"
RECRUITER_RESPONSE=$(curl -s -X POST "$AUTH_SERVICE_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"recruiter@example.com","password":"'$TEST_PASSWORD'","full_name":"Test Recruiter","role":"RECRUITER"}')

RECRUITER_TOKEN=$(echo "$RECRUITER_RESPONSE" | jq -r '.access_token // empty')

if [ ! -z "$RECRUITER_TOKEN" ] && [ "$RECRUITER_TOKEN" != "null" ]; then
    printf "${GREEN}✅ Recruiter registered${NC}\n"
    ((PASSED++))
else
    printf "${RED}❌ Recruiter registration failed${NC}\n"
    ((FAILED++))
fi

# Register Candidate
printf "Registering Candidate...\n"
CANDIDATE_RESPONSE=$(curl -s -X POST "$AUTH_SERVICE_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"candidate@example.com","password":"'$TEST_PASSWORD'","full_name":"Test Candidate","role":"CANDIDATE"}')

CANDIDATE_TOKEN=$(echo "$CANDIDATE_RESPONSE" | jq -r '.access_token // empty')

if [ ! -z "$CANDIDATE_TOKEN" ] && [ "$CANDIDATE_TOKEN" != "null" ]; then
    printf "${GREEN}✅ Candidate registered${NC}\n"
    ((PASSED++))
else
    printf "${RED}❌ Candidate registration failed${NC}\n"
    ((FAILED++))
fi
printf "\n"

# ==================== STEP 3: LOGIN ====================
printf "${YELLOW}[STEP 3] Login Test${NC}\n"
printf "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

LOGIN_RESPONSE=$(curl -s -X POST "$AUTH_SERVICE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"'$TEST_PASSWORD'"}')

LOGIN_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token // empty')
LOGIN_REFRESH=$(echo "$LOGIN_RESPONSE" | jq -r '.refresh_token // empty')

if [ ! -z "$LOGIN_TOKEN" ] && [ "$LOGIN_TOKEN" != "null" ]; then
    printf "${GREEN}✅ Login successful${NC}\n"
    ((PASSED++))
    # Use login tokens if registration failed
    if [ -z "$ADMIN_TOKEN" ]; then
        ADMIN_TOKEN=$LOGIN_TOKEN
        ADMIN_REFRESH=$LOGIN_REFRESH
    fi
else
    printf "${RED}❌ Login failed${NC}\n"
    ((FAILED++))
fi

# Test invalid credentials
printf "Testing invalid credentials...\n"
INVALID_LOGIN=$(curl -s -X POST "$AUTH_SERVICE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"WrongPassword123"}')

INVALID_TOKEN=$(echo "$INVALID_LOGIN" | jq -r '.access_token // empty')

if [ -z "$INVALID_TOKEN" ] || [ "$INVALID_TOKEN" = "null" ]; then
    printf "${GREEN}✅ Invalid credentials rejected${NC}\n"
    ((PASSED++))
else
    printf "${RED}❌ Invalid credentials not rejected${NC}\n"
    ((FAILED++))
fi
printf "\n"

# ==================== STEP 4: GET PROFILE ====================
printf "${YELLOW}[STEP 4] Get User Profile${NC}\n"
printf "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

PROFILE=$(curl -s -X GET "$AUTH_SERVICE_URL/api/v1/users/me" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

USER_EMAIL=$(echo "$PROFILE" | jq -r '.email // empty')

if [ "$USER_EMAIL" = "admin@example.com" ]; then
    printf "${GREEN}✅ Profile retrieved${NC}\n"
    ((PASSED++))
else
    printf "${RED}❌ Profile retrieval failed${NC}\n"
    ((FAILED++))
fi
printf "\n"

# ==================== STEP 5: UPDATE PROFILE ====================
printf "${YELLOW}[STEP 5] Update Profile${NC}\n"
printf "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

UPDATE=$(curl -s -X PUT "$AUTH_SERVICE_URL/api/v1/users/me" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Updated Admin","role":"ADMIN"}')

UPDATED_NAME=$(echo "$UPDATE" | jq -r '.full_name // empty')

if [ "$UPDATED_NAME" = "Updated Admin" ]; then
    printf "${GREEN}✅ Profile updated${NC}\n"
    ((PASSED++))
else
    printf "${RED}❌ Profile update failed${NC}\n"
    ((FAILED++))
fi
printf "\n"

# ==================== STEP 6: CREATE COMPANY ====================
printf "${YELLOW}[STEP 6] Create Company${NC}\n"
printf "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

COMPANY=$(curl -s -X POST "$AUTH_SERVICE_URL/api/v1/companies" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Company","industry":"Technology","size":"medium","subscription_tier":"pro"}')

COMPANY_ID=$(echo "$COMPANY" | jq -r '.id // empty')

if [ ! -z "$COMPANY_ID" ] && [ "$COMPANY_ID" != "null" ]; then
    printf "${GREEN}✅ Company created${NC}\n"
    ((PASSED++))
else
    printf "${RED}❌ Company creation failed${NC}\n"
    ((FAILED++))
fi
printf "\n"

# ==================== STEP 7: LIST COMPANIES ====================
printf "${YELLOW}[STEP 7] List Companies${NC}\n"
printf "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

COMPANIES=$(curl -s -X GET "$AUTH_SERVICE_URL/api/v1/companies" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

if [ ! -z "$COMPANIES" ] && [ "$COMPANIES" != "null" ]; then
    printf "${GREEN}✅ Companies list retrieved${NC}\n"
    ((PASSED++))
else
    printf "${RED}❌ List failed${NC}\n"
    ((FAILED++))
fi
printf "\n"

# ==================== STEP 8: UPDATE COMPANY ====================
printf "${YELLOW}[STEP 8] Update Company${NC}\n"
printf "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

if [ ! -z "$COMPANY_ID" ] && [ "$COMPANY_ID" != "null" ]; then
    UPDATED=$(curl -s -X PUT "$AUTH_SERVICE_URL/api/v1/companies/$COMPANY_ID" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"name":"Updated Company","industry":"Finance"}')

    UPDATED_NAME=$(echo "$UPDATED" | jq -r '.name // empty')

    if [ "$UPDATED_NAME" = "Updated Company" ]; then
        printf "${GREEN}✅ Company updated${NC}\n"
        ((PASSED++))
    else
        printf "${RED}❌ Update failed${NC}\n"
        ((FAILED++))
    fi
else
    printf "${YELLOW}⚠️  Skipping (no company ID)${NC}\n"
fi
printf "\n"

# ==================== STEP 9: REFRESH TOKEN ====================
printf "${YELLOW}[STEP 9] Refresh Token${NC}\n"
printf "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

if [ ! -z "$ADMIN_REFRESH" ] && [ "$ADMIN_REFRESH" != "null" ]; then
    REFRESH=$(curl -s -X POST "$AUTH_SERVICE_URL/api/v1/auth/refresh" \
      -H "Authorization: Bearer $ADMIN_REFRESH")

    NEW_TOKEN=$(echo "$REFRESH" | jq -r '.access_token // empty')

    if [ ! -z "$NEW_TOKEN" ] && [ "$NEW_TOKEN" != "null" ]; then
        printf "${GREEN}✅ Token refreshed${NC}\n"
        ((PASSED++))
    else
        printf "${RED}❌ Refresh failed${NC}\n"
        ((FAILED++))
    fi
else
    printf "${YELLOW}⚠️  Skipping (no refresh token)${NC}\n"
fi
printf "\n"

# ==================== STEP 10: RBAC TEST ====================
printf "${YELLOW}[STEP 10] RBAC Test${NC}\n"
printf "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

if [ ! -z "$CANDIDATE_TOKEN" ] && [ "$CANDIDATE_TOKEN" != "null" ]; then
    RBAC=$(curl -s -X POST "$AUTH_SERVICE_URL/api/v1/companies" \
      -H "Authorization: Bearer $CANDIDATE_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"name":"Unauthorized","industry":"Tech"}')

    RBAC_ID=$(echo "$RBAC" | jq -r '.id // empty')

    if [ -z "$RBAC_ID" ] || [ "$RBAC_ID" = "null" ]; then
        printf "${GREEN}✅ RBAC working (candidate blocked)${NC}\n"
        ((PASSED++))
    else
        printf "${RED}❌ RBAC failed${NC}\n"
        ((FAILED++))
    fi
else
    printf "${YELLOW}⚠️  Skipping (no candidate token)${NC}\n"
fi
printf "\n"

# ==================== FINAL RESULTS ====================
printf "${BLUE}════════════════════════════════════════════════════════${NC}\n"
printf "${BLUE}📊 TEST RESULTS${NC}\n"
printf "${BLUE}════════════════════════════════════════════════════════${NC}\n\n"

TOTAL=$((PASSED + FAILED))
if [ $TOTAL -gt 0 ]; then
    PERCENTAGE=$((PASSED * 100 / TOTAL))
else
    PERCENTAGE=0
fi

printf "${GREEN}Passed: $PASSED${NC}\n"
printf "${RED}Failed: $FAILED${NC}\n"
printf "${CYAN}Total:  $TOTAL${NC}\n"
printf "Success Rate: ${PERCENTAGE}%%\n\n"

if [ $FAILED -eq 0 ]; then
    printf "${GREEN}🎉 ALL TESTS PASSED!${NC}\n"
    exit 0
else
    printf "${RED}⚠️  SOME TESTS FAILED${NC}\n"
    exit 1
fi
