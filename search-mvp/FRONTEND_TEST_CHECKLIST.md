# Frontend Test Checklist

## Prerequisites
Ensure all services are running:
1. Terminal 1: `python unified_logger.py`
2. Terminal 2: `python api_server.py`
3. Terminal 3: `npm start` (in uruguay-research-ui directory)

## Browser Test Steps

### 1. Initial Load
- [ ] Open http://localhost:3000
- [ ] Verify the chat interface loads
- [ ] Check browser console for errors (F12)

### 2. Submit a Research Question
- [ ] Type: "What do citizens say about healthcare?"
- [ ] Click Send or press Enter
- [ ] **Expected**: Loading spinner appears immediately

### 3. Monitor Browser Console
Look for these logs in order:
- [ ] `🚀 Starting research for: What do citizens say about healthcare?`
- [ ] `📋 Got job ID: [some-uuid]` (should appear within 1 second)
- [ ] `🔌 Creating WebSocket for job: [some-uuid]`
- [ ] `✅ WebSocket connected successfully`
- [ ] `📨 WebSocket Event:` messages for:
  - [ ] iteration_start
  - [ ] thinking
  - [ ] tool_call
  - [ ] tool_result
  - [ ] response_end
  - [ ] result

### 4. Check UI Updates
- [ ] Reasoning trace appears and updates in real-time
- [ ] Each iteration shows thinking and tool calls
- [ ] Final response appears in the chat
- [ ] Loading spinner disappears
- [ ] Response includes the full analysis text

### 5. Check for Errors
- [ ] No "No currentAssistantMessage to update" warning
- [ ] No WebSocket disconnection errors before completion
- [ ] Final message displays properly

## Debugging Commands

If something goes wrong, check:

1. **View unified logs:**
   ```bash
   python view_unified_logs.py | tail -100
   ```

2. **Run automated test:**
   ```bash
   python test_frontend_flow.py
   ```

3. **Check specific events:**
   ```bash
   python view_unified_logs.py | grep -E "(WebSocket Event|Got job ID|Final result)"
   ```

## Success Criteria
✅ API responds with job_id in <1 second
✅ WebSocket connects immediately after
✅ Real-time events display in trace
✅ Final result appears in chat UI
✅ No console errors or warnings