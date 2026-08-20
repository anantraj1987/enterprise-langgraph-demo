
import uuid
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from config.settings import settings
from data.generate_docs import main as generate_mock_docs
from graph.graph_builder import compiled_guarded_graph
from schemas.api_schemas import Token, IncidentRequest, IncidentResponse
from security.auth import create_access_token, verify_password, get_current_user, MOCK_USER_DB
from security.rbac import require_admin_or_operator
from services.redis_service import redis_service
from services.memory_service import mem0_service
from utils.logger import logger

# Initialize FastAPI App
app = FastAPI(
    title=f"{settings.PROJECT_NAME} API",
    version=settings.VERSION,
    description="Enterprise REST API for Smart Incident Resolution powered by LangGraph, MCP, Mem0, and Redis.",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    logger.info("[API SERVER] Starting Enterprise Incident Agent REST Microservice...")
    if not settings.KB_FILE_PATH.exists():
        generate_mock_docs()


@app.on_event("shutdown")
def shutdown_event():
    logger.info("[API SERVER] Shutting down API Microservice...")
    if hasattr(mem0_service, "close"):
        mem0_service.close()


# ---------------------------------------------------------------------
# AUTHENTICATION ENDPOINTS
# ---------------------------------------------------------------------
@app.post("/api/v1/auth/login", response_model=Token, tags=["Authentication"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Obtain OAuth2 Bearer Token for API Authentication."""
    user = MOCK_USER_DB.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}
    )
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )


# ---------------------------------------------------------------------
# SECURE INCIDENT RESOLUTION AGENT ENDPOINTS
# ---------------------------------------------------------------------
@app.post("/api/v1/incidents/resolve", response_model=IncidentResponse, tags=["Incident Agent"])
async def resolve_incident(
    request: IncidentRequest,
    current_user: dict = Depends(require_admin_or_operator)
):
    """
    Authenticated Endpoint: Processes helpdesk incident requests through:
    1. Redis Cache
    2. Mem0 Long-Term User Preference Memory
    3. Guardrail Security Checks (PII, Injection Defense, Policy)
    4. LangGraph Dynamic Router + Remote MCP Tool Execution
    """
    user_name = current_user["username"]
    user_id = user_name.lower().replace(" ", "_")
    department = request.department or current_user.get("department", "Infrastructure")
    thread_id = str(uuid.uuid4())[:8]

    # 1. Check Redis Cache
    cached_payload = redis_service.get_cached_solution(request.raw_query, user_id)
    if cached_payload:
        return IncidentResponse(
            thread_id=thread_id,
            user_name=user_name,
            department=department,
            intent=cached_payload.get("intent", "General"),
            sub_category=cached_payload.get("sub_category", ""),
            guardrail_passed=True,
            sanitized_query=cached_payload.get("sanitized_query", request.raw_query),
            solution=cached_payload.get("solution", ""),
            confidence_score=cached_payload.get("confidence_score", 100),
            is_cached_response=True,
            visited_nodes=["REDIS_CACHE_HIT"]
        )

    # 2. Retrieve Mem0 User Preferences
    user_prefs = mem0_service.get_user_memories(user_id)

    # 3. Construct Graph Initial State
    initial_state = {
        "user_name": user_name,
        "user_id": user_id,
        "department": department,
        "raw_query": request.raw_query,
        "sanitized_query": "",
        "user_preferences": user_prefs,
        "guardrail_passed": True,
        "guardrail_violation_reason": "",
        "intent": "Unclassified",
        "sub_category": "",
        "retrieved_docs": [],
        "telemetry_data": {},
        "code_analysis_data": {},
        "billing_data": {},
        "solution": "",
        "confidence_score": 0,
        "is_cached_response": False,
        "retry_count": 0,
        "human_approved": False,
        "human_feedback": "",
        "visited_nodes": ["START"],
        "execution_logs": [f"API Request initiated by user {user_name}"],
    }

    config = {"configurable": {"thread_id": thread_id}}

    # 4. Invoke LangGraph Engine
    try:
        final_state = compiled_guarded_graph.invoke(initial_state, config=config)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LangGraph execution error: {str(e)}"
        )

    # 5. Save Successful Runs to Redis Cache & Mem0
    if final_state.get("guardrail_passed", True) and final_state.get("confidence_score", 0) >= settings.CONFIDENCE_THRESHOLD:
        redis_service.set_cached_solution(request.raw_query, user_id, final_state)
        mem0_service.add_user_memory(user_id, f"Query: {request.raw_query} | Resolved via REST API")

    return IncidentResponse(
        thread_id=thread_id,
        user_name=user_name,
        department=department,
        intent=final_state.get("intent", "Unclassified"),
        sub_category=final_state.get("sub_category", ""),
        guardrail_passed=final_state.get("guardrail_passed", True),
        guardrail_violation_reason=final_state.get("guardrail_violation_reason"),
        sanitized_query=final_state.get("sanitized_query", request.raw_query),
        solution=final_state.get("solution", "No solution produced."),
        confidence_score=final_state.get("confidence_score", 0),
        is_cached_response=False,
        visited_nodes=final_state.get("visited_nodes", [])
    )


@app.get("/api/v1/health", tags=["Health & System"])
async def health_check():
    """System Health Check Endpoint."""
    return {
        "status": "online",
        "redis_connected": redis_service.is_connected,
        "version": settings.VERSION
    }


if __name__ == "__main__":
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
