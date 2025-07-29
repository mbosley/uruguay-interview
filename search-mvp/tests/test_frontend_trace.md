# Testing Frontend Trace Display

## Quick Test Steps

1. **Check API Server is Running**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Test with Mock Agent**
   ```bash
   curl -X POST http://localhost:8000/research \
     -H "Content-Type: application/json" \
     -d '{"question": "Test healthcare", "use_mock": true}'
   ```
   
   Note the job_id returned.

3. **Test WebSocket Directly**
   ```bash
   # Install websocat if needed: brew install websocat
   websocat ws://localhost:8000/research/{JOB_ID}/stream
   ```

## What to Look for in Browser Console

When you ask a question in the UI, you should see:

1. **Initial Connection:**
   - 🚀 Starting research for: [your question]
   - 📋 Got job ID: [job id]
   - 🔌 Creating WebSocket for job: [job id]
   - 🔗 Connecting to WebSocket: ws://localhost:8000/research/[job id]/stream
   - ✅ WebSocket connected successfully

2. **Raw WebSocket Messages:**
   - 📥 RAW WebSocket data received: [raw JSON string]
   - ✅ Parsed WebSocket message: [parsed object]

3. **Event Processing:**
   - 📨 WebSocket Event: {type: "iteration_start", iteration: 1, ...}
   - 🔄 Setting current iteration: 1
   - 💭 Adding thinking step: {...}
   - 🔧 Adding tool call: {...}
   - ✅ Tool result received: {...}

4. **Trace Building:**
   - 📊 updateCurrentTrace called: {...}
   - 🎯 Target iteration: 1
   - ✅ Added step to trace: {iteration: 1, stepType: "thinking", totalSteps: 1}

5. **Display Rendering:**
   - 🎨 Rendering live trace: [array of traces]
   - 🖼️ TraceDisplay rendering: {isActive: true, tracesCount: 3, totalSteps: 10}

## Common Issues

### No WebSocket Connection Logs
- API server might not be running
- CORS issues (check browser Network tab)
- Wrong WebSocket URL

### Events Received but No Trace Display
- Check if `isResearching` is true
- Check if `currentTrace` has data
- Look for "Rendering live trace" logs

### Trace Cleared Too Early
- Look for when `isResearching` becomes false
- Check if multiple events are clearing the trace