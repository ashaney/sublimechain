"""
SublimeChain Memory Manager

Provides persistent AI memory using Mem0 for enhanced context awareness,
learning from past interactions, and intelligent pattern recognition.
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
import re

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from mem0 import MemoryClient
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    logger.warning("Mem0 not available. Install with: pip install mem0ai")


class SublimeMemory:
    """Enhanced memory management for SublimeChain with context-aware storage and retrieval"""
    
    def __init__(self, user_id: str = "default_user"):
        self.user_id = user_id
        self.memory = None
        self.conversation_context = []
        self.tool_patterns = {}
        self.session_start = datetime.now()
        
        if MEMORY_AVAILABLE:
            try:
                # Initialize Mem0 Cloud Client (not open-source)
                self.memory = MemoryClient()
                logger.info(f"SublimeMemory initialized with cloud service for user: {user_id}")
                
            except Exception as e:
                logger.error(f"Failed to initialize Mem0 cloud client: {e}")
                self.memory = None
        else:
            logger.warning("Mem0 not available - memory features disabled")
    
    def is_available(self) -> bool:
        """Check if memory functionality is available"""
        return self.memory is not None
    
    def store_conversation(self, messages: List[Dict], context: str = None):
        """Store conversation context for future reference"""
        if not self.is_available():
            return
            
        try:
            # Create a meaningful memory entry
            conversation_summary = self._summarize_conversation(messages)
            
            memory_content = {
                "type": "conversation",
                "content": conversation_summary,
                "context": context or "general_chat",
                "timestamp": datetime.now().isoformat(),
                "message_count": len(messages)
            }
            
            # Store in Mem0 using cloud client API - pass actual conversation messages
            result = self.memory.add(
                messages=messages,  # Use the actual conversation messages
                user_id=self.user_id,
                metadata=memory_content,  # Store metadata separately
                output_format="v1.1"  # Explicitly set output format to avoid deprecation
            )
            
            # Provide clean user feedback only if memory was actually stored
            if result and self.is_available() and len(messages) > 0:
                from ui_components import ui
                ui.print("💾 [dim green]Memory stored[/dim green]")
            logger.debug(f"Stored conversation memory: {result}")
            
        except Exception as e:
            logger.error(f"Failed to store conversation: {e}")
    
    def store_tool_success(self, tool_name: str, task: str, result: str, context: Dict = None):
        """Store successful tool usage patterns for future recommendations"""
        if not self.is_available():
            return
            
        try:
            memory_content = {
                "type": "tool_success",
                "tool": tool_name,
                "task": task,
                "result_summary": result[:500],  # Truncate long results
                "context": context or {},
                "timestamp": datetime.now().isoformat()
            }
            
            # Store tool success as a proper conversation
            tool_messages = [
                {"role": "user", "content": f"I used the {tool_name} tool for: {task}"},
                {"role": "assistant", "content": f"Successfully executed {tool_name}. {result[:200]}..."}
            ]
            
            result = self.memory.add(
                messages=tool_messages,
                user_id=self.user_id,
                metadata=memory_content,
                output_format="v1.1"
            )
            
            # Track tool patterns locally too
            if tool_name not in self.tool_patterns:
                self.tool_patterns[tool_name] = []
            self.tool_patterns[tool_name].append({
                "task": task,
                "timestamp": datetime.now().isoformat(),
                "success": True
            })
            
            # Provide clean user feedback for tool pattern learning
            if result and self.is_available():
                from ui_components import ui
                ui.print(f"🧠 [dim blue]Learned {tool_name} pattern[/dim blue]")
            logger.debug(f"Stored tool success: {tool_name}")
            
        except Exception as e:
            logger.error(f"Failed to store tool success: {e}")
    
    def store_learning(self, learning: str, category: str = "general", importance: str = "medium"):
        """Store important learnings and insights"""
        if not self.is_available():
            return
            
        try:
            memory_content = {
                "type": "learning",
                "content": learning,
                "category": category,
                "importance": importance,
                "timestamp": datetime.now().isoformat()
            }
            
            # Store learning as a conversation
            learning_messages = [
                {"role": "user", "content": f"I learned something about {category}"},
                {"role": "assistant", "content": f"I'll remember: {learning}"}
            ]
            
            result = self.memory.add(
                messages=learning_messages,
                user_id=self.user_id,
                metadata=memory_content,
                output_format="v1.1"
            )
            
            # Provide clean feedback for explicit learning
            if result:
                from ui_components import ui
                ui.print(f"📚 [dim yellow]Stored learning: {category}[/dim yellow]")
            logger.debug(f"Stored learning: {category}")
            
        except Exception as e:
            logger.error(f"Failed to store learning: {e}")
    
    def recall_context(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search for relevant memories based on query"""
        if not self.is_available():
            return []
            
        try:
            # Search memories using cloud client API v2 with proper filters
            filters = {
                "user_id": self.user_id  # Simple direct filter for v2 API
            }
            
            search_results = self.memory.search(
                query=query,
                version="v2", 
                filters=filters,
                limit=max_results
            )
            
            # Handle Mem0 cloud search results format (v1.1 API with potential double-nesting)
            relevant_memories = []
            
            # Cloud API returns results in a specific format
            if isinstance(search_results, dict) and "results" in search_results:
                results = search_results["results"]
                # Handle potential double-nested structure like get_all
                if isinstance(results, dict) and "results" in results:
                    results = results["results"]
            elif isinstance(search_results, list):
                results = search_results
            else:
                logger.debug(f"Unexpected search result format: {type(search_results)}")
                return []
            
            # Process each result
            for result in results:
                if isinstance(result, dict):
                    # Cloud API results contain: id, memory, hash, created_at, metadata, score
                    # The 'memory' field contains the extracted memory text
                    memory_text = result.get("memory", "")
                    relevance = result.get("score", 0.8)  # Use provided score or default
                    metadata = result.get("metadata", {})
                    created_at = result.get("created_at", "")
                    
                    relevant_memories.append({
                        "content": memory_text,  # Use the extracted memory text
                        "relevance": relevance,
                        "metadata": metadata,
                        "created_at": created_at,
                        "id": result.get("id", "")
                    })
            
            logger.debug(f"Found {len(relevant_memories)} relevant memories for: {query}")
            return relevant_memories
            
        except Exception as e:
            logger.error(f"Failed to recall context: {e}")
            return []
    
    def search_memories_by_type(self, memory_type: str, max_results: int = 10) -> List[Dict]:
        """Search for memories by specific type (conversation, tool_success, learning, etc)"""
        if not self.is_available():
            return []
            
        try:
            # Get all memories and filter by type
            all_memories_response = self.memory.get_all(
                user_id=self.user_id,
                version="v2",
                output_format="v1.1",
                page=1, 
                page_size=50
            )
            
            # Extract memories from paginated response
            if isinstance(all_memories_response, dict) and "results" in all_memories_response:
                results = all_memories_response["results"]
                if isinstance(results, dict) and "results" in results:
                    all_memories = results["results"]
                else:
                    all_memories = results if isinstance(results, list) else []
            else:
                all_memories = all_memories_response if isinstance(all_memories_response, list) else []
            
            # Filter by type
            filtered_memories = []
            for memory in all_memories:
                if isinstance(memory, dict):
                    metadata = memory.get("metadata", {})
                    if metadata.get("type") == memory_type:
                        filtered_memories.append({
                            "content": memory.get("memory", ""),
                            "metadata": metadata,
                            "created_at": memory.get("created_at", ""),
                            "id": memory.get("id", "")
                        })
            
            return filtered_memories[:max_results]
            
        except Exception as e:
            logger.error(f"Failed to search memories by type: {e}")
            return []
    
    def search_memories_by_date_range(self, start_date: datetime, end_date: datetime, max_results: int = 10) -> List[Dict]:
        """Search for memories within a specific date range"""
        if not self.is_available():
            return []
            
        try:
            # Get all memories first (Mem0 doesn't have native date filtering)
            all_memories_response = self.memory.get_all(
                user_id=self.user_id,
                version="v2",
                output_format="v1.1",
                page=1, 
                page_size=100  # Get more for date filtering
            )
            
            # Extract memories from paginated response
            if isinstance(all_memories_response, dict) and "results" in all_memories_response:
                results = all_memories_response["results"]
                if isinstance(results, dict) and "results" in results:
                    all_memories = results["results"]
                else:
                    all_memories = results if isinstance(results, list) else []
            else:
                all_memories = all_memories_response if isinstance(all_memories_response, list) else []
            
            # Filter by date range
            filtered_memories = []
            for memory in all_memories:
                if isinstance(memory, dict):
                    created_at_str = memory.get("created_at", "")
                    if created_at_str:
                        try:
                            # Parse the datetime string (format: 2025-06-17T03:14:02.321149-07:00)
                            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                            if start_date <= created_at <= end_date:
                                filtered_memories.append({
                                    "content": memory.get("memory", ""),
                                    "metadata": memory.get("metadata", {}),
                                    "created_at": created_at_str,
                                    "id": memory.get("id", "")
                                })
                        except Exception as e:
                            logger.debug(f"Failed to parse date {created_at_str}: {e}")
            
            # Sort by date (newest first)
            filtered_memories.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return filtered_memories[:max_results]
            
        except Exception as e:
            logger.error(f"Failed to search memories by date: {e}")
            return []
    
    def smart_recall(self, query: str, max_results: int = 5) -> List[Dict]:
        """Enhanced recall with intelligent query processing"""
        if not self.is_available():
            return []
        
        # Analyze the query type and use appropriate strategy
        query_lower = query.lower()
        
        # Temporal queries (yesterday, last week, etc.)
        if any(term in query_lower for term in ["yesterday", "today", "last week", "last month", "this week"]):
            return self._handle_temporal_query(query, max_results)
        
        # Personal info queries
        elif any(term in query_lower for term in ["about me", "know about me", "who am i", "my info", "my details"]):
            return self._handle_personal_info_query(max_results)
        
        # Activity queries (what did I do, where did I go)
        elif any(term in query_lower for term in ["what did i", "where did i", "what have i", "activities", "events"]):
            return self._handle_activity_query(query, max_results)
        
        # Tool/work queries
        elif any(term in query_lower for term in ["tools", "work", "projects", "code", "development"]):
            return self._handle_work_query(query, max_results)
        
        # Default to regular context search
        else:
            return self.recall_context(query, max_results)
    
    def _handle_temporal_query(self, query: str, max_results: int) -> List[Dict]:
        """Handle time-based queries like 'yesterday', 'last week'"""
        now = datetime.now()
        
        if "yesterday" in query.lower():
            start_date = now - timedelta(days=1)
            end_date = now
        elif "last week" in query.lower():
            start_date = now - timedelta(weeks=1)
            end_date = now
        elif "last month" in query.lower():
            start_date = now - timedelta(days=30)
            end_date = now
        elif "today" in query.lower():
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        else:
            # Default to last 7 days
            start_date = now - timedelta(days=7)
            end_date = now
        
        return self.search_memories_by_date_range(start_date, end_date, max_results)
    
    def _handle_personal_info_query(self, max_results: int) -> List[Dict]:
        """Handle personal information queries"""
        # Use multiple targeted searches for better results
        all_memories = []
        search_terms = ["name", "occupation", "work", "developer", "CPA", "programming", "hobby", "interests", "preferences"]
        
        for term in search_terms:
            try:
                term_memories = self.recall_context(term, max_results=3)
                all_memories.extend(term_memories)
            except:
                continue
        
        # Deduplicate memories by content
        unique_memories = []
        seen_content = set()
        for memory in all_memories:
            content = memory.get("content", "")
            if content and content not in seen_content:
                unique_memories.append(memory)
                seen_content.add(content)
        
        return unique_memories[:max_results]
    
    def _handle_activity_query(self, query: str, max_results: int) -> List[Dict]:
        """Handle activity-based queries"""
        # Look for tool usage and conversation memories
        tool_memories = self.search_memories_by_type("tool_success", max_results // 2)
        conversation_memories = self.search_memories_by_type("conversation", max_results // 2)
        
        # Combine and sort by relevance/date
        all_memories = tool_memories + conversation_memories
        all_memories.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return all_memories[:max_results]
    
    def _handle_work_query(self, query: str, max_results: int) -> List[Dict]:
        """Handle work/development related queries"""
        # First try specific tool pattern recall
        work_memories = self.search_memories_by_type("tool_success", max_results)
        
        # Also search for programming-related conversations
        programming_terms = ["code", "programming", "development", "python", "typescript", "react", "bun"]
        for term in programming_terms:
            if term in query.lower():
                term_memories = self.recall_context(term, max_results=3)
                work_memories.extend(term_memories)
        
        # Deduplicate and return
        unique_memories = []
        seen_ids = set()
        for memory in work_memories:
            memory_id = memory.get("id", "")
            if memory_id and memory_id not in seen_ids:
                unique_memories.append(memory)
                seen_ids.add(memory_id)
        
        return unique_memories[:max_results]
    
    def explicit_remember(self, content: str, category: str = "explicit", tags: List[str] = None, importance: str = "medium") -> bool:
        """Explicitly store a memory with enhanced metadata"""
        if not self.is_available():
            return False
            
        try:
            memory_content = {
                "type": "explicit_memory",
                "content": content,
                "category": category,
                "tags": tags or [],
                "importance": importance,
                "timestamp": datetime.now().isoformat(),
                "user_created": True
            }
            
            # Store as a conversation for better retrieval
            memory_messages = [
                {"role": "user", "content": f"Please remember this: {content}"},
                {"role": "assistant", "content": f"I'll remember: {content} (Category: {category})"}
            ]
            
            result = self.memory.add(
                messages=memory_messages,
                user_id=self.user_id,
                metadata=memory_content,
                output_format="v1.1"
            )
            
            # Provide user feedback
            if result:
                from ui_components import ui
                ui.print(f"📝 [green]Memory stored in category '{category}'[/green]")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to explicitly store memory: {e}")
            return False
    
    def forget_memory(self, memory_id: str) -> bool:
        """Delete a specific memory by ID"""
        if not self.is_available():
            return False
            
        try:
            # Mem0 cloud client delete functionality
            result = self.memory.delete(memory_id=memory_id)
            
            if result:
                from ui_components import ui
                ui.print(f"🗑️ [yellow]Memory deleted[/yellow]")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete memory: {e}")
            return False
    
    def clear_all_memories(self) -> bool:
        """Delete all memories for this user using batch delete API"""
        if not self.is_available():
            return False
            
        try:
            # First, get all memory IDs
            all_memories_response = self.memory.get_all(
                user_id=self.user_id,
                version="v2",
                output_format="v1.1",
                page=1, 
                page_size=1000  # Get all memories
            )
            
            # Extract memories from paginated response
            if isinstance(all_memories_response, dict) and "results" in all_memories_response:
                results = all_memories_response["results"]
                if isinstance(results, dict) and "results" in results:
                    all_memories = results["results"]
                else:
                    all_memories = results if isinstance(results, list) else []
            else:
                all_memories = all_memories_response if isinstance(all_memories_response, list) else []
            
            if not all_memories:
                logger.info("No memories found to delete")
                return True
            
            # Extract memory IDs
            memory_ids = []
            for memory in all_memories:
                if isinstance(memory, dict) and "id" in memory:
                    memory_ids.append(memory["id"])
            
            if not memory_ids:
                logger.info("No valid memory IDs found")
                return True
            
            # Use batch delete API (max 1000 per request)
            logger.info(f"Batch deleting {len(memory_ids)} memories...")
            
            # Format memory IDs correctly for batch delete
            delete_memories = [{"memory_id": mid} for mid in memory_ids]
            
            # Process in batches of 1000
            success_count = 0
            for i in range(0, len(delete_memories), 1000):
                batch = delete_memories[i:i+1000]
                try:
                    result = self.memory.batch_delete(batch)
                    if result:
                        success_count += len(batch)
                        logger.info(f"Deleted batch of {len(batch)} memories")
                    else:
                        logger.error(f"Failed to delete batch of {len(batch)} memories")
                except Exception as e:
                    logger.error(f"Error deleting batch: {e}")
                    
            if success_count == len(delete_memories):
                logger.info(f"Successfully deleted all {len(memory_ids)} memories")
                return True
            else:
                logger.error(f"Only deleted {success_count}/{len(memory_ids)} memories")
                return False
            
        except Exception as e:
            logger.error(f"Failed to clear all memories: {e}")
            return False
    
    def clear_memories_by_type(self, memory_type: str) -> bool:
        """Delete all memories of a specific type (e.g., 'conversation', 'tool_success')"""
        if not self.is_available():
            return False
            
        try:
            # Get memories of specific type
            memories = self.search_memories_by_type(memory_type, max_results=1000)
            
            if not memories:
                logger.info(f"No memories of type '{memory_type}' found")
                return True
            
            # Extract memory IDs
            memory_ids = [m.get("id") for m in memories if m.get("id")]
            
            if not memory_ids:
                logger.info(f"No valid memory IDs found for type '{memory_type}'")
                return True
            
            # Use batch delete API (max 1000 per request)
            logger.info(f"Batch deleting {len(memory_ids)} memories of type '{memory_type}'...")
            
            # Format memory IDs correctly for batch delete
            delete_memories = [{"memory_id": mid} for mid in memory_ids]
            
            # Process in batches of 1000
            success_count = 0
            for i in range(0, len(delete_memories), 1000):
                batch = delete_memories[i:i+1000]
                try:
                    result = self.memory.batch_delete(batch)
                    if result:
                        success_count += len(batch)
                        logger.info(f"Deleted batch of {len(batch)} memories")
                    else:
                        logger.error(f"Failed to delete batch of {len(batch)} memories")
                except Exception as e:
                    logger.error(f"Error deleting batch: {e}")
                    
            if success_count == len(delete_memories):
                logger.info(f"Successfully deleted all {len(memory_ids)} memories of type '{memory_type}'")
                return True
            else:
                logger.error(f"Only deleted {success_count}/{len(memory_ids)} memories of type '{memory_type}'")
                return False
            
        except Exception as e:
            logger.error(f"Failed to clear memories by type: {e}")
            return False
    
    def clear_old_memories(self, days_old: int = 30) -> bool:
        """Delete memories older than specified days"""
        if not self.is_available():
            return False
            
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            # Get all memories and filter by date
            all_memories_response = self.memory.get_all(
                user_id=self.user_id,
                version="v2",
                output_format="v1.1",
                page=1, 
                page_size=1000
            )
            
            # Extract memories from paginated response
            if isinstance(all_memories_response, dict) and "results" in all_memories_response:
                results = all_memories_response["results"]
                if isinstance(results, dict) and "results" in results:
                    all_memories = results["results"]
                else:
                    all_memories = results if isinstance(results, list) else []
            else:
                all_memories = all_memories_response if isinstance(all_memories_response, list) else []
            
            # Filter old memories
            old_memory_ids = []
            for memory in all_memories:
                if isinstance(memory, dict):
                    created_at_str = memory.get("created_at", "")
                    try:
                        # Parse the created_at timestamp
                        if created_at_str:
                            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                            if created_at < cutoff_date:
                                old_memory_ids.append(memory.get("id"))
                    except Exception as e:
                        logger.debug(f"Failed to parse date {created_at_str}: {e}")
                        continue
            
            if not old_memory_ids:
                logger.info(f"No memories older than {days_old} days found")
                return True
            
            # Use batch delete API (max 1000 per request)
            logger.info(f"Batch deleting {len(old_memory_ids)} memories older than {days_old} days...")
            
            # Format memory IDs correctly for batch delete
            delete_memories = [{"memory_id": mid} for mid in old_memory_ids]
            
            # Process in batches of 1000
            success_count = 0
            for i in range(0, len(delete_memories), 1000):
                batch = delete_memories[i:i+1000]
                try:
                    result = self.memory.batch_delete(batch)
                    if result:
                        success_count += len(batch)
                        logger.info(f"Deleted batch of {len(batch)} memories")
                    else:
                        logger.error(f"Failed to delete batch of {len(batch)} memories")
                except Exception as e:
                    logger.error(f"Error deleting batch: {e}")
                    
            if success_count == len(delete_memories):
                logger.info(f"Successfully deleted all {len(old_memory_ids)} old memories")
                return True
            else:
                logger.error(f"Only deleted {success_count}/{len(old_memory_ids)} old memories")
                return False
            
        except Exception as e:
            logger.error(f"Failed to clear old memories: {e}")
            return False
    
    def recall_tool_patterns(self, tool_name: str) -> List[Dict]:
        """Get patterns for successful tool usage"""
        if not self.is_available():
            return []
            
        try:
            query = f"tool usage patterns for {tool_name}"
            memories = self.recall_context(query, max_results=3)
            
            # Filter for tool-specific memories
            tool_memories = [
                m for m in memories 
                if m.get("metadata", {}).get("type") == "tool_success" and 
                   m.get("metadata", {}).get("tool") == tool_name
            ]
            
            return tool_memories
            
        except Exception as e:
            logger.error(f"Failed to recall tool patterns: {e}")
            return []
    
    def get_conversation_context(self, limit: int = 10) -> str:
        """Get recent conversation context for enhanced responses"""
        if not self.is_available():
            return ""
            
        try:
            memories = self.recall_context("recent conversation", max_results=limit)
            
            context_parts = []
            for memory in memories:
                if memory.get("metadata", {}).get("type") == "conversation":
                    context_parts.append(memory["content"])
            
            return "\n".join(context_parts[:5])  # Limit context size
            
        except Exception as e:
            logger.error(f"Failed to get conversation context: {e}")
            return ""
    
    def get_memory_stats(self) -> Dict:
        """Get statistics about stored memories"""
        if not self.is_available():
            return {"status": "unavailable", "total_memories": 0}
            
        try:
            # Get all memories for the user using cloud client API with v1.1 format
            all_memories_response = self.memory.get_all(
                user_id=self.user_id,
                version="v2",
                output_format="v1.1",
                page=1, 
                page_size=50
            )
            
            # Extract memories from paginated response (handle double-nested structure)
            if isinstance(all_memories_response, dict) and "results" in all_memories_response:
                results = all_memories_response["results"]
                # Handle double-nested results structure from v1.1 API
                if isinstance(results, dict) and "results" in results:
                    all_memories = results["results"]
                else:
                    all_memories = results if isinstance(results, list) else []
            else:
                all_memories = all_memories_response if isinstance(all_memories_response, list) else []
            
            # Handle case where get_all returns a string or unexpected format
            if isinstance(all_memories, str):
                all_memories = []
            elif all_memories is None:
                all_memories = []
            elif not isinstance(all_memories, list):
                all_memories = []
            
            stats = {
                "status": "active",
                "total_memories": len(all_memories),
                "session_start": self.session_start.isoformat(),
                "tool_patterns": len(self.tool_patterns),
                "user_id": self.user_id
            }
            
            # Count by type
            memory_types = {}
            for memory in all_memories:
                if isinstance(memory, dict):
                    memory_type = memory.get("metadata", {}).get("type", "unknown")
                    memory_types[memory_type] = memory_types.get(memory_type, 0) + 1
            
            stats["memory_types"] = memory_types
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {"status": "error", "error": str(e)}
    
    def _summarize_conversation(self, messages: List[Dict]) -> str:
        """Create a concise summary of conversation messages"""
        if not messages:
            return "Empty conversation"
            
        # Extract key information from messages
        user_messages = [m["content"] for m in messages if m.get("role") == "user"]
        assistant_messages = [m["content"] for m in messages if m.get("role") == "assistant"]
        
        summary_parts = []
        
        if user_messages:
            last_user_msg = user_messages[-1][:200]  # First 200 chars
            summary_parts.append(f"User asked: {last_user_msg}")
        
        if assistant_messages:
            last_assistant_msg = assistant_messages[-1][:200]
            summary_parts.append(f"Assistant responded: {last_assistant_msg}")
        
        return " | ".join(summary_parts)


# Global memory instance
_global_memory = None

def get_memory_manager(user_id: str = "default_user") -> SublimeMemory:
    """Get or create the global memory manager instance"""
    global _global_memory
    if _global_memory is None or _global_memory.user_id != user_id:
        _global_memory = SublimeMemory(user_id)
    return _global_memory


# Convenience functions for easy integration
def remember(content: str, category: str = "general"):
    """Quick function to store a learning"""
    memory = get_memory_manager()
    memory.store_learning(content, category)

def recall(query: str, max_results: int = 5) -> List[Dict]:
    """Quick function to search memories"""
    memory = get_memory_manager()
    return memory.recall_context(query, max_results)

def remember_success(tool_name: str, task: str, result: str):
    """Quick function to remember successful tool usage"""
    memory = get_memory_manager()
    memory.store_tool_success(tool_name, task, result)