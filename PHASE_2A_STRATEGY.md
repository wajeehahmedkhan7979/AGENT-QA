
# PHASE 2 EXECUTION STRATEGY - AGENT-QA

## REPOSITORY ANALYSIS SUMMARY

### Codebase Structure
- **Backend**: 12 Python modules (fastapi + sqlite)
  - llm_adapter.py (5.7 KB) - Mock LLM integration
  - semantic.py (6.3 KB) - Core semantic extraction
  - db.py, storage.py, queue_adapter.py - Adapter layer
  - mock_llm.py, validator.py, preflight.py - Support services

- **Runner**: Python worker for test execution
- **Web UI**: React/TypeScript frontend
- **Infra**: Docker Compose setup
- **Sample App**: Node.js test target

### Key Findings (from IMPLEMENTATION_ANALYSIS.md)
- Demo is COMPLETE and FUNCTIONAL with deterministic behavior
- Uses mock LLM (ensures repeatability for Phase 2 validation)
- Read-only execution model (safety boundary is set)
- Clear adapter boundaries already exist
- **Test coverage**: Not explicitly detailed - AUDIT NEEDED

### Critical Gaps Identified
1. **NO STRUCTURED TESTS** for semantic extraction logic
2. **NO GOLDEN FIXTURES** for regression testing
3. **NO ADAPTER CONTRACT TESTS**
4. **NO FAILURE PATH VALIDATION**
5. **NO STRUCTURED LOGGING** (only basic print statements)
6. **UI IS TOO SIMPLE** and doesn't explain system state

---

## PHASE 2A - LOGIC VALIDATION & TEST HARDENING
### Goal: Prove core logic is deterministic and stable

### 2A.1 Semantic Model Validation
**What**: Create golden test fixtures for semantic extraction

**Action Items**:
1. [ ] Create `tests/` directory structure
   - tests/golden/
   - tests/unit/
   - tests/integration/

2. [ ] Identify deterministic test inputs
   - Use sample-app as test target
   - Capture known semantic outputs

3. [ ] Build golden fixture files
   - tests/golden/semantic/login_page.json
   - tests/golden/semantic/form_page.json
   - tests/golden/semantic/flow_navigation.json

4. [ ] Write assertion tests
   - Semantic structure validation
   - Element role classification
   - Selector stability
   - Confidence bounds

5. [ ] Add to CI/CD (if applicable)

**Deliverable**: Passing semantic regression tests

---

### 2A.2 Test Generation Determinism
**What**: Validate mock LLM adapter produces stable output

**Action Items**:
1. [ ] Audit llm_adapter.py + mock_llm.py
2. [ ] Create contract tests
   - Same input → Same output
   - Schema validation
   - Action boundary enforcement
3. [ ] Test forbidden actions detection
   - Verify POST/DELETE cannot appear in read-only scope
4. [ ] Add mock LLM tests

**Deliverable**: High-confidence that generation is deterministic

---

### 2A.3 Runner Failure Semantics
**What**: Intentionally break scenarios and validate failure paths

**Action Items**:
1. [ ] Create failing test case (intentional breakage)
2. [ ] Assert screenshots still captured
3. [ ] Assert logs still written
4. [ ] Assert report status correct
5. [ ] Assert NO silent crashes

**Deliverable**: Failure paths are tested and observed

---

## PHASE 2B - OBSERVABILITY (After 2A passes)
- Structured JSON logging
- Job timeline persistence
- API timeline endpoint

## PHASE 2C - ADAPTER HARDENING (After 2B passes)
- Explicit interfaces
- Contract tests for all adapters
- Delta doc (demo vs prod)

## PHASE 2D - UI MATURATION (After 2C passes)
- Redesigned job creation
- Job overview with timeline
- Semantic viewer
- Test case viewer
- Results page

## PHASE 2E - DOCUMENTATION (Final)
- Updated ARCHITECTURE.md
- PHASE_2_VALIDATION.md
- DEMO_RUNBOOK.md

---

## WORK PRIORITY ORDER

1. **FIRST**: Explore existing tests (if any) in backend/
2. **SECOND**: Create test structure and golden fixtures
3. **THIRD**: Build 2A.1-2A.3 tests
4. **FOURTH**: Make Phase 2A tests pass
5. **FIFTH**: Document and commit Phase 2A
6. **SIXTH**: Plan Phase 2B with findings from 2A

---

## SUCCESS CRITERIA FOR PHASE 2A
- [ ] All semantic tests pass
- [ ] All generation tests pass
- [ ] Failure paths validated
- [ ] NO TODOs in core logic
- [ ] README updated with test instructions
- [ ] Main branch clean commit
