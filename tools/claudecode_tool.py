"""
Claude Code Tool for SublimeChain

Integrates Claude Code SDK for advanced coding capabilities with memory-enhanced
pattern recognition and context-aware code generation.
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
import logging

from tools.base import BaseTool

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Try to import claude-code-sdk (this will be a placeholder for now)
    # In reality, you'd install: npm install @anthropic/claude-code
    # And use it via subprocess or a Python wrapper
    CLAUDE_CODE_AVAILABLE = True
except ImportError:
    CLAUDE_CODE_AVAILABLE = False
    logger.warning("Claude Code SDK not available. Install with: npm install @anthropic/claude-code")

# Import memory manager for enhanced context
try:
    from memory_manager import get_memory_manager, remember_success
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False


class ClaudeCodeTool(BaseTool):
    """Advanced coding assistant using Claude Code SDK with memory integration"""
    
    name = "claudecode"
    description = """
    Advanced AI coding assistant powered by Claude Code SDK with memory-enhanced capabilities.
    
    This tool provides sophisticated code analysis, generation, refactoring, and debugging
    with context awareness from past successful patterns and solutions.
    
    Use this tool for:
    - Complex code generation and refactoring
    - Multi-file project analysis and modifications
    - Debugging assistance with context from past solutions
    - Code review and optimization suggestions
    - Git workflow integration and automation
    - Architecture recommendations based on learned patterns
    - "Generate a Python API endpoint with authentication"
    - "Refactor this class to follow SOLID principles" 
    - "Debug this error with context from similar past issues"
    - "Review this code for security vulnerabilities"
    """
    
    input_schema = {
        "type": "object",
        "properties": {
            "task": {
                "type": "string",
                "description": "The coding task to perform (e.g., 'generate REST API', 'refactor class', 'debug error')"
            },
            "code": {
                "type": "string", 
                "description": "Existing code to work with (optional)",
                "default": ""
            },
            "files": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of file paths to analyze or modify (optional)",
                "default": []
            },
            "context": {
                "type": "string",
                "description": "Additional context about the project, requirements, or constraints",
                "default": ""
            },
            "memory_search": {
                "type": "boolean",
                "description": "Whether to search memory for similar past solutions",
                "default": True
            }
        },
        "required": ["task"]
    }
    
    def __init__(self):
        self.memory = get_memory_manager() if MEMORY_AVAILABLE else None
        self.coding_patterns = {}
        
    def execute(self, **kwargs) -> str:
        """Execute Claude Code with memory-enhanced context"""
        task = kwargs.get("task", "")
        code = kwargs.get("code", "")
        files = kwargs.get("files", [])
        context = kwargs.get("context", "")
        memory_search = kwargs.get("memory_search", True)
        
        try:
            # Get relevant memories if available
            memory_context = ""
            if self.memory and memory_search:
                memory_context = self._get_relevant_memories(task)
            
            # Prepare the enhanced prompt with memory context
            enhanced_context = self._prepare_context(task, code, files, context, memory_context)
            
            # Execute coding task (placeholder implementation)
            result = self._execute_coding_task(task, enhanced_context)
            
            # Store successful pattern in memory
            if self.memory and result and not result.startswith("Error:"):
                try:
                    # Try to get existing event loop
                    loop = asyncio.get_running_loop()
                    # We're in an async context, this shouldn't be called from sync context
                    pass
                except RuntimeError:
                    # No running event loop, create a new one
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(remember_success("claudecode", task, result))
                    finally:
                        loop.close()
            
            return result
            
        except Exception as e:
            error_msg = f"Error executing Claude Code task: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def _get_relevant_memories(self, task: str) -> str:
        """Get relevant coding patterns from memory"""
        if not self.memory or not self.memory.is_available():
            return ""
            
        try:
            # Search for similar coding tasks
            try:
                # Try to get existing event loop
                loop = asyncio.get_running_loop()
                # We're in an async context, this shouldn't be called from sync context
                return ""
            except RuntimeError:
                # No running event loop, create a new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    memories = loop.run_until_complete(
                        self.memory.recall_context(f"coding task: {task}", max_results=3)
                    )
                finally:
                    loop.close()
            
            if not memories:
                return ""
            
            memory_parts = []
            for memory in memories:
                if memory.get("metadata", {}).get("type") == "tool_success":
                    tool = memory.get("metadata", {}).get("tool", "")
                    if tool in ["claudecode", "coding", "development"]:
                        memory_parts.append(f"Previous solution: {memory['content'][:200]}")
            
            return "\n".join(memory_parts) if memory_parts else ""
            
        except Exception as e:
            logger.error(f"Failed to get relevant memories: {e}")
            return ""
    
    def _prepare_context(self, task: str, code: str, files: List[str], context: str, memory_context: str) -> str:
        """Prepare enhanced context for Claude Code"""
        context_parts = [f"Task: {task}"]
        
        if code:
            context_parts.append(f"Existing Code:\n{code}")
        
        if files:
            context_parts.append(f"Files to work with: {', '.join(files)}")
        
        if context:
            context_parts.append(f"Additional Context: {context}")
        
        if memory_context:
            context_parts.append(f"Relevant Past Solutions:\n{memory_context}")
        
        return "\n\n".join(context_parts)
    
    def _execute_coding_task(self, task: str, context: str) -> str:
        """Execute the actual coding task using Claude Code SDK"""
        
        # For now, this is a placeholder implementation
        # In reality, you would use the Claude Code SDK here
        if not CLAUDE_CODE_AVAILABLE:
            return self._placeholder_coding_response(task, context)
        
        try:
            # This would be the actual Claude Code SDK call:
            # result = claude_code_sdk.run(
            #     task=task,
            #     context=context,
            #     model="claude-sonnet-4-20250514",
            #     tools_enabled=True
            # )
            # return result
            
            # Placeholder for now
            return self._placeholder_coding_response(task, context)
            
        except Exception as e:
            return f"Error: Failed to execute Claude Code SDK: {str(e)}"
    
    def _placeholder_coding_response(self, task: str, context: str) -> str:
        """Placeholder response when Claude Code SDK is not available"""
        
        # Analyze the task and provide intelligent responses
        task_lower = task.lower()
        
        if "api" in task_lower and "endpoint" in task_lower:
            return self._generate_api_template(task, context)
        elif "debug" in task_lower or "error" in task_lower:
            return self._debug_assistance(task, context)
        elif "refactor" in task_lower:
            return self._refactor_suggestions(task, context)
        elif "test" in task_lower:
            return self._test_generation(task, context)
        else:
            return self._general_coding_response(task, context)
    
    def _generate_api_template(self, task: str, context: str) -> str:
        """Generate API endpoint template"""
        return f"""
# API Endpoint Template for: {task}

Based on your request and context, here's a suggested implementation:

```python
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer
from pydantic import BaseModel
import logging

app = FastAPI()
security = HTTPBearer()

class RequestModel(BaseModel):
    # Define your request model here
    pass

class ResponseModel(BaseModel):
    # Define your response model here
    success: bool
    data: dict

@app.post("/api/endpoint", response_model=ResponseModel)
async def your_endpoint(
    request_data: RequestModel,
    token: str = Depends(security)
):
    try:
        # Validate token
        # Process request_data
        # Return response
        return ResponseModel(success=True, data={{"message": "Success"}})
    except Exception as e:
        logging.error(f"Endpoint error: {{e}}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

Key considerations:
- Authentication with HTTPBearer
- Proper error handling and logging
- Type validation with Pydantic models
- RESTful response structure

Context considered: {context[:200] if context else 'No additional context'}
"""
    
    def _debug_assistance(self, task: str, context: str) -> str:
        """Provide debugging assistance"""
        return f"""
# Debug Assistance for: {task}

Common debugging approach:

## 1. Error Analysis
- Check the error message and stack trace
- Identify the failing line and function
- Look for common patterns (null references, type mismatches, etc.)

## 2. Debugging Steps
```python
# Add logging for better visibility
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add debug prints at key points
logger.debug(f"Variable state: {{variable_name}}")

# Use try-catch for error isolation
try:
    # problematic code here
    pass
except Exception as e:
    logger.error(f"Error details: {{e}}")
    logger.error(f"Error type: {{type(e)}}")
    import traceback
    traceback.print_exc()
```

## 3. Common Solutions
- Validate input data types and null checks
- Check API endpoints and network connectivity
- Verify environment variables and configurations
- Review recent code changes

Context: {context[:200] if context else 'No additional context provided'}

Next steps: Share the specific error message and code snippet for targeted assistance.
"""
    
    def _refactor_suggestions(self, task: str, context: str) -> str:
        """Provide refactoring suggestions"""
        return f"""
# Refactoring Suggestions for: {task}

## SOLID Principles Checklist:

### Single Responsibility Principle
- Each class/function should have one reason to change
- Split large classes into focused components

### Open/Closed Principle  
- Extend behavior via inheritance/composition, not modification
- Use interfaces and abstract base classes

### Liskov Substitution Principle
- Derived classes should be substitutable for base classes
- Ensure consistent behavior contracts

### Interface Segregation Principle
- Create focused, minimal interfaces
- Avoid forcing clients to depend on unused methods

### Dependency Inversion Principle
- Depend on abstractions, not concretions
- Use dependency injection

## Common Refactoring Patterns:

```python
# Before: Large monolithic class
class DataProcessor:
    def read_file(self): pass
    def validate_data(self): pass
    def transform_data(self): pass
    def save_results(self): pass

# After: Separated concerns
class FileReader:
    def read(self, path): pass

class DataValidator:
    def validate(self, data): pass

class DataTransformer:
    def transform(self, data): pass

class ResultSaver:
    def save(self, results): pass

class DataProcessor:
    def __init__(self, reader, validator, transformer, saver):
        self.reader = reader
        self.validator = validator
        self.transformer = transformer
        self.saver = saver
```

Context considered: {context[:200] if context else 'No additional context'}
"""
    
    def _test_generation(self, task: str, context: str) -> str:
        """Generate test templates"""
        return f"""
# Test Generation for: {task}

## Unit Test Template

```python
import pytest
from unittest.mock import Mock, patch
from your_module import YourClass

class TestYourClass:
    
    def setup_method(self):
        \"\"\"Setup test fixtures before each test method.\"\"\"
        self.instance = YourClass()
    
    def test_happy_path(self):
        \"\"\"Test the main success scenario\"\"\"
        # Arrange
        input_data = {{"key": "value"}}
        expected_result = "expected_output"
        
        # Act
        result = self.instance.your_method(input_data)
        
        # Assert
        assert result == expected_result
    
    def test_edge_cases(self):
        \"\"\"Test edge cases and boundary conditions\"\"\"
        # Test empty input
        assert self.instance.your_method({{}}) is not None
        
        # Test invalid input
        with pytest.raises(ValueError):
            self.instance.your_method(None)
    
    @patch('your_module.external_dependency')
    def test_with_mocks(self, mock_dependency):
        \"\"\"Test with mocked dependencies\"\"\"
        # Arrange
        mock_dependency.return_value = "mocked_response"
        
        # Act
        result = self.instance.method_with_dependency()
        
        # Assert
        assert result == "expected_result"
        mock_dependency.assert_called_once()

## Integration Test Template

```python
import pytest
from fastapi.testclient import TestClient
from your_app import app

client = TestClient(app)

def test_api_endpoint():
    response = client.post(
        "/api/endpoint",
        json={{"test": "data"}},
        headers={{"Authorization": "Bearer test-token"}}
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
```

Run tests with: `pytest tests/ -v --cov=your_module`

Context: {context[:200] if context else 'No additional context'}
"""
    
    def _general_coding_response(self, task: str, context: str) -> str:
        """General coding assistance"""
        return f"""
# Coding Assistant Response for: {task}

I understand you need help with: {task}

## Analysis:
Based on your request, this appears to be a {self._categorize_task(task)} task.

## Recommended Approach:
1. **Planning Phase**: Break down the requirements into smaller components
2. **Design Phase**: Consider architecture patterns and data structures
3. **Implementation Phase**: Start with core functionality, then add features
4. **Testing Phase**: Write tests for critical functionality
5. **Documentation Phase**: Add clear comments and documentation

## Code Structure Suggestion:
```python
# Main implementation file
class YourSolution:
    def __init__(self):
        # Initialize components
        pass
    
    def main_method(self):
        # Core functionality
        try:
            # Implementation logic
            result = self._process_logic()
            return result
        except Exception as e:
            # Error handling
            self._handle_error(e)
            raise
    
    def _process_logic(self):
        # Helper method for core logic
        pass
    
    def _handle_error(self, error):
        # Error handling logic
        logging.error(f"Error occurred: {{error}}")
```

## Next Steps:
Please provide more specific details about:
- Input/output requirements
- Technology stack preferences
- Performance constraints
- Integration requirements

Context considered: {context[:200] if context else 'No specific context provided'}

Note: This is a placeholder response. For full functionality, install Claude Code SDK.
"""
    
    def _categorize_task(self, task: str) -> str:
        """Categorize the coding task type"""
        task_lower = task.lower()
        
        if any(word in task_lower for word in ["api", "endpoint", "rest", "graphql"]):
            return "API development"
        elif any(word in task_lower for word in ["database", "sql", "query", "orm"]):
            return "database"
        elif any(word in task_lower for word in ["ui", "frontend", "react", "vue", "html"]):
            return "frontend development"
        elif any(word in task_lower for word in ["test", "unit", "integration", "pytest"]):
            return "testing"
        elif any(word in task_lower for word in ["deploy", "docker", "kubernetes", "ci/cd"]):
            return "deployment/DevOps"
        elif any(word in task_lower for word in ["data", "analysis", "pandas", "numpy"]):
            return "data processing"
        elif any(word in task_lower for word in ["machine learning", "ml", "ai", "model"]):
            return "machine learning"
        else:
            return "general programming"