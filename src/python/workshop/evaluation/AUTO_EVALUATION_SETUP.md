# Auto-Evaluation Setup

Your calendar agent now has automatic evaluation enabled! Here's how it works:

## What You'll See

After each agent response, you'll see an evaluation summary like this:

```
==================================================
🔍 EVALUATING RESPONSE...
🟢 Overall Score: 4.2/5.0
📊 Details: Intent: 4.5/5 | Coherence: 4.0/5 | Tools: 95%
✅ Evaluated with 3 metrics
==================================================
```

## Score Meanings

- **🟢 Green (4.0-5.0)**: Excellent performance
- **🟡 Yellow (3.0-3.9)**: Good performance
- **🔴 Red (Below 3.0)**: Needs improvement

## Configuration

Edit your `.env` file to control auto-evaluation:

```bash
# Enable/disable auto-evaluation
ENABLE_AUTO_EVALUATION=true

# Choose which metrics to evaluate (comma-separated)
AUTO_EVAL_METRICS=intent,coherence,tools
```

### Available Metrics

- **intent**: How well the agent understood user intent (1-5 scale)
- **coherence**: How logically consistent the response is (1-5 scale)  
- **tools**: How accurately the agent used tools (0-100% scale)

## Usage Examples

### Enable Auto-Evaluation
```bash
ENABLE_AUTO_EVALUATION=true
```

### Disable Auto-Evaluation
```bash
ENABLE_AUTO_EVALUATION=false
```

### Evaluate Only Key Metrics
```bash
AUTO_EVAL_METRICS=intent,tools
```

### Evaluate All Metrics
```bash
AUTO_EVAL_METRICS=intent,coherence,tools
```

## Performance Impact

- **Latency**: Adds ~1-2 seconds after each response
- **API Calls**: Uses additional evaluation API calls
- **Cost**: Minimal additional cost for evaluation calls

## Troubleshooting

### No Evaluation Shown
1. Check that `ENABLE_AUTO_EVALUATION=true` in `.env`
2. Ensure your Azure project has proper permissions
3. Verify the model deployment name is correct

### Evaluation Errors
- Check the console for error messages
- Ensure evaluator models are available
- Verify Azure credentials are working

### Tool Evaluation Skipped
- This is normal if the agent didn't use tools
- Tool evaluation only runs when tools are actually called

## Development Tips

1. **Development Mode**: Keep auto-evaluation enabled during development
2. **Production Mode**: Consider disabling or using background evaluation
3. **Debugging**: Use evaluation scores to identify response quality issues
4. **Performance**: Disable auto-evaluation if response speed is critical

## Next Steps

- Monitor evaluation scores to identify improvement areas
- Adjust agent instructions based on evaluation feedback
- Consider implementing custom evaluators for domain-specific metrics
- Use evaluation data to track performance over time
