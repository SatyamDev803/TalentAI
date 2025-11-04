GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🚀 JOB SERVICE - COMPLETE WORKFLOW TEST${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}\n"

# ==================== STEP 1: LOGIN ====================
echo -e "${YELLOW}[STEP 1] LOGIN - Getting tokens${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

ADMIN_RESPONSE=$(curl -s -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"SecurePassword123"}')
ADMIN_TOKEN=$(echo "$ADMIN_RESPONSE" | jq -r '.access_token')
[ "$ADMIN_TOKEN" != "null" ] && echo -e "${GREEN}✅ Admin token${NC}" || (echo -e "${RED}❌ Admin login failed${NC}" && exit 1)

RECRUITER_RESPONSE=$(curl -s -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"recruiter@example.com","password":"SecurePassword123"}')
RECRUITER_TOKEN=$(echo "$RECRUITER_RESPONSE" | jq -r '.access_token')
[ "$RECRUITER_TOKEN" != "null" ] && echo -e "${GREEN}✅ Recruiter token${NC}" || (echo -e "${RED}❌ Recruiter login failed${NC}" && exit 1)

CANDIDATE_RESPONSE=$(curl -s -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"candidate@example.com","password":"SecurePassword123"}')
CANDIDATE_TOKEN=$(echo "$CANDIDATE_RESPONSE" | jq -r '.access_token')
[ "$CANDIDATE_TOKEN" != "null" ] && echo -e "${GREEN}✅ Candidate token${NC}" || (echo -e "${RED}❌ Candidate login failed${NC}" && exit 1)

# ==================== STEP 2: GET OR CREATE CATEGORY ====================
echo -e "\n${YELLOW}[STEP 2] ADMIN - Get or Create Category${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# First try to list categories
CAT_LIST=$(curl -s -X GET "http://localhost:8002/api/v1/categories?page=1&page_size=20" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
CATEGORY_ID=$(echo "$CAT_LIST" | jq -r '.categories[0].id // empty')

if [ -z "$CATEGORY_ID" ]; then
  # Create new category
  CATEGORY_RESPONSE=$(curl -s -X POST http://localhost:8002/api/v1/categories \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"name":"Engineering","description":"Software Engineering roles"}')
  CATEGORY_ID=$(echo "$CATEGORY_RESPONSE" | jq -r '.id')
  [ ! -z "$CATEGORY_ID" ] && [ "$CATEGORY_ID" != "null" ] && echo -e "${GREEN}✅ Category created: $CATEGORY_ID${NC}" || echo -e "${RED}❌ Failed to create category${NC}"
else
  echo -e "${GREEN}✅ Using existing category: $CATEGORY_ID${NC}"
fi

# ==================== STEP 3: GET OR CREATE SKILL ====================
echo -e "\n${YELLOW}[STEP 3] ADMIN - Get or Create Skill${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

SKILL_LIST=$(curl -s -X GET "http://localhost:8002/api/v1/skills?page=1&page_size=20" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
SKILL_ID=$(echo "$SKILL_LIST" | jq -r '.skills[0].id // empty')

if [ -z "$SKILL_ID" ]; then
  SKILL_RESPONSE=$(curl -s -X POST http://localhost:8002/api/v1/skills \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"name":"Python","category":"Programming Languages"}')
  SKILL_ID=$(echo "$SKILL_RESPONSE" | jq -r '.id')
  [ ! -z "$SKILL_ID" ] && [ "$SKILL_ID" != "null" ] && echo -e "${GREEN}✅ Skill created: $SKILL_ID${NC}" || echo -e "${RED}❌ Failed to create skill${NC}"
else
  echo -e "${GREEN}✅ Using existing skill: $SKILL_ID${NC}"
fi

# ==================== STEP 4: CREATE JOB ====================
echo -e "\n${YELLOW}[STEP 4] RECRUITER - Create Job${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

JOB_PAYLOAD=$(cat <<EOF
{
  "title": "Senior Python Developer",
  "description": "Experienced Python developer with FastAPI knowledge",
  "job_type": "FULL_TIME",
  "experience_level": "SENIOR",
  "category_id": "$CATEGORY_ID",
  "salary_min": 100000,
  "salary_max": 150000,
  "location": "San Francisco, CA",
  "is_remote": true
}
EOF
)

JOB_RESPONSE=$(curl -s -X POST http://localhost:8002/api/v1/jobs \
  -H "Authorization: Bearer $RECRUITER_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$JOB_PAYLOAD")

JOB_ID=$(echo "$JOB_RESPONSE" | jq -r '.id')
JOB_STATUS=$(echo "$JOB_RESPONSE" | jq -r '.status')

if [ ! -z "$JOB_ID" ] && [ "$JOB_ID" != "null" ]; then
  echo -e "${GREEN}✅ Job created: $JOB_ID (Status: $JOB_STATUS)${NC}"
else
  echo -e "${RED}❌ Failed to create job${NC}"
  echo "$JOB_RESPONSE" | jq '.'
  exit 1
fi

# ==================== STEP 5: GET JOB ====================
echo -e "\n${YELLOW}[STEP 5] RECRUITER - Get Job Details${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

GET_JOB=$(curl -s -X GET "http://localhost:8002/api/v1/jobs/$JOB_ID" \
  -H "Authorization: Bearer $RECRUITER_TOKEN")

GET_JOB_TITLE=$(echo "$GET_JOB" | jq -r '.title')
[ ! -z "$GET_JOB_TITLE" ] && [ "$GET_JOB_TITLE" != "null" ] && echo -e "${GREEN}✅ Job retrieved: $GET_JOB_TITLE${NC}" || echo -e "${RED}❌ Failed to get job${NC}"

# ==================== STEP 6: UPDATE JOB ====================
echo -e "\n${YELLOW}[STEP 6] RECRUITER - Update Job${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

UPDATE_JOB=$(curl -s -X PUT "http://localhost:8002/api/v1/jobs/$JOB_ID" \
  -H "Authorization: Bearer $RECRUITER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Senior Python Developer (Updated)","salary_max":160000}')

UPDATE_TITLE=$(echo "$UPDATE_JOB" | jq -r '.title')
if [ "$UPDATE_TITLE" = "Senior Python Developer (Updated)" ]; then
  echo -e "${GREEN}✅ Job updated${NC}"
else
  echo -e "${RED}❌ Failed to update job${NC}"
fi

# ==================== STEP 7: PUBLISH JOB ====================
echo -e "\n${YELLOW}[STEP 7] RECRUITER - Publish Job${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

PUBLISH_JOB=$(curl -s -X POST "http://localhost:8002/api/v1/jobs/$JOB_ID/publish" \
  -H "Authorization: Bearer $RECRUITER_TOKEN")

PUBLISHED_STATUS=$(echo "$PUBLISH_JOB" | jq -r '.status')
[ "$PUBLISHED_STATUS" = "PUBLISHED" ] && echo -e "${GREEN}✅ Job published${NC}" || echo -e "${RED}❌ Failed to publish job${NC}"

# ==================== STEP 8: LIST JOBS ====================
echo -e "\n${YELLOW}[STEP 8] RECRUITER - List Published Jobs${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

LIST_JOBS=$(curl -s -X GET "http://localhost:8002/api/v1/jobs?page=1&page_size=10" \
  -H "Authorization: Bearer $RECRUITER_TOKEN")

JOBS_TOTAL=$(echo "$LIST_JOBS" | jq '.total')
[ "$JOBS_TOTAL" -gt 0 ] && echo -e "${GREEN}✅ Jobs listed: $JOBS_TOTAL found${NC}" || echo -e "${RED}❌ No jobs found${NC}"

# ==================== STEP 9: APPLY FOR JOB ====================
echo -e "\n${YELLOW}[STEP 9] CANDIDATE - Apply for Job${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

APPLY_RESPONSE=$(curl -s -X POST "http://localhost:8002/api/v1/applications/jobs/$JOB_ID/apply" \
  -H "Authorization: Bearer $CANDIDATE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"cover_letter":"I am very interested in this role."}')

APP_ID=$(echo "$APPLY_RESPONSE" | jq -r '.id')
APP_STATUS=$(echo "$APPLY_RESPONSE" | jq -r '.status')

if [ ! -z "$APP_ID" ] && [ "$APP_ID" != "null" ]; then
  echo -e "${GREEN}✅ Application submitted: $APP_ID (Status: $APP_STATUS)${NC}"
else
  echo -e "${RED}❌ Failed to apply for job${NC}"
  echo "$APPLY_RESPONSE" | jq '.'
fi

# ==================== STEP 10: VIEW MY APPLICATIONS ====================
echo -e "\n${YELLOW}[STEP 10] CANDIDATE - View My Applications${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

MY_APPS=$(curl -s -X GET "http://localhost:8002/api/v1/applications?page=1&page_size=10" \
  -H "Authorization: Bearer $CANDIDATE_TOKEN")

MY_APPS_TOTAL=$(echo "$MY_APPS" | jq '.total')
[ "$MY_APPS_TOTAL" -gt 0 ] && echo -e "${GREEN}✅ My applications: $MY_APPS_TOTAL found${NC}" || echo -e "${RED}❌ No applications found${NC}"

# ==================== STEP 11: VIEW JOB APPLICATIONS ====================
echo -e "\n${YELLOW}[STEP 11] RECRUITER - View Job Applications${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

JOB_APPS=$(curl -s -X GET "http://localhost:8002/api/v1/applications/jobs/$JOB_ID/applications?page=1&page_size=10" \
  -H "Authorization: Bearer $RECRUITER_TOKEN")

JOB_APPS_TOTAL=$(echo "$JOB_APPS" | jq '.total // 0')
[ "$JOB_APPS_TOTAL" -gt 0 ] && echo -e "${GREEN}✅ Job applications: $JOB_APPS_TOTAL found${NC}" || echo -e "${RED}❌ No applications for job${NC}"

# ==================== STEP 12: UPDATE APPLICATION STATUS ====================
echo -e "\n${YELLOW}[STEP 12] RECRUITER - Update Application Status${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ! -z "$APP_ID" ] && [ "$APP_ID" != "null" ]; then
  UPDATE_APP=$(curl -s -X PUT "http://localhost:8002/api/v1/applications/$APP_ID" \
    -H "Authorization: Bearer $RECRUITER_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"status":"ACCEPTED"}')

  UPDATED_STATUS=$(echo "$UPDATE_APP" | jq -r '.status')
  [ "$UPDATED_STATUS" = "ACCEPTED" ] && echo -e "${GREEN}✅ Application accepted${NC}" || echo -e "${RED}❌ Failed to update${NC}"
else
  echo -e "${RED}❌ No application to update${NC}"
fi

# ==================== STEP 13: CLOSE JOB ====================
echo -e "\n${YELLOW}[STEP 13] RECRUITER - Close Job${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

CLOSE_JOB=$(curl -s -X POST "http://localhost:8002/api/v1/jobs/$JOB_ID/close" \
  -H "Authorization: Bearer $RECRUITER_TOKEN")

CLOSED_STATUS=$(echo "$CLOSE_JOB" | jq -r '.status')
[ "$CLOSED_STATUS" = "CLOSED" ] && echo -e "${GREEN}✅ Job closed${NC}" || echo -e "${RED}❌ Failed to close job${NC}"

# ==================== FINAL SUMMARY ====================
echo -e "\n${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🎉 WORKFLOW TEST COMPLETE!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}\n"

echo -e "${YELLOW}Summary:${NC}"
echo -e "  Category ID:    ${GREEN}$CATEGORY_ID${NC}"
echo -e "  Job ID:         ${GREEN}$JOB_ID${NC}"
echo -e "  Application ID: ${GREEN}$APP_ID${NC}\n"

