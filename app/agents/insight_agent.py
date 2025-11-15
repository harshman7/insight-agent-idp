"""
Orchestration logic: chooses tools, formats responses using Ollama LLM.
"""
import json
import re
import hashlib
from typing import Dict, Any, Optional, List
import requests
from app.services.rag import RAGService
from app.services.sql_tools import SQLTools
from app.services.insights import InsightsService
from app.agents.tools import get_all_tools
from app.config import settings

class InsightAgent:
    """Main agent that orchestrates RAG and SQL tools to answer questions using Ollama."""
    
    def __init__(self, rag_service: Optional[RAGService] = None, enable_cache: bool = True):
        self.rag_service = rag_service
        self.sql_tools = SQLTools()
        self.insights_service = InsightsService()
        self.tools = get_all_tools(rag_service)
        self.ollama_base_url = settings.OLLAMA_BASE_URL
        self.model_name = settings.OLLAMA_MODEL
        self.enable_cache = enable_cache
        self._response_cache: Dict[str, Dict[str, Any]] = {}
    
    def _call_ollama(self, prompt: str, system_prompt: Optional[str] = None, timeout: int = 30) -> str:
        """Call Ollama API to get LLM response."""
        try:
            url = f"{self.ollama_base_url}/api/generate"
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "system": system_prompt or "",
                "stream": False
            }
            response = requests.post(url, json=payload, timeout=timeout)
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            return f"Error calling Ollama: {str(e)}"
    
    def _get_cache_key(self, query: str, use_rag: bool, use_sql: bool) -> str:
        """Generate cache key for query."""
        cache_str = f"{query}|{use_rag}|{use_sql}"
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def _format_tool_result(self, tool_name: str, result: str, query: str) -> str:
        """Format tool result into a natural language answer."""
        try:
            if tool_name == "get_metrics":
                data = json.loads(result)
                if isinstance(data, list) and len(data) > 0:
                    if "vendor" in str(data[0]).lower():
                        # Vendor stats
                        answer = "Here are your top vendors by spend:\n\n"
                        for i, vendor in enumerate(data[:10], 1):
                            vendor_name = vendor.get("vendor", "Unknown")
                            total = vendor.get("total_spend", 0)
                            count = vendor.get("transaction_count", 0)
                            answer += f"{i}. **{vendor_name}**: ${total:,.2f} ({count} transactions)\n"
                        return answer
                    elif "category" in str(data[0]).lower():
                        # Category breakdown
                        answer = "Here's your spending breakdown by category:\n\n"
                        total_all = sum(item.get("total_spend", 0) for item in data)
                        for item in data:
                            category = item.get("category", "Uncategorized")
                            total = item.get("total_spend", 0)
                            percentage = (total / total_all * 100) if total_all > 0 else 0
                            answer += f"- **{category}**: ${total:,.2f} ({percentage:.1f}%)\n"
                        return answer
            elif tool_name == "sql_query":
                data = json.loads(result)
                if isinstance(data, list) and len(data) > 0:
                    # Format SQL results
                    if "vendor" in str(data[0]).lower() and "total_spend" in str(data[0]).lower():
                        answer = "Here are your top vendors by spend:\n\n"
                        for i, row in enumerate(data[:10], 1):
                            vendor = row.get("vendor", "Unknown")
                            total = row.get("total_spend", row.get("sum", 0))
                            answer += f"{i}. **{vendor}**: ${float(total):,.2f}\n"
                        return answer
            
            # Default: return formatted JSON
            return f"Based on the data:\n\n```json\n{result[:500]}\n```"
        except:
            return result
    
    def _build_tool_prompt(self) -> str:
        """Build a prompt describing available tools."""
        tool_descriptions = []
        for tool in self.tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")
        
        return "\n".join(tool_descriptions)
    
    def _extract_tool_calls(self, llm_response: str) -> List[Dict[str, Any]]:
        """Extract tool calls from LLM response."""
        tool_calls = []
        
        # Look for patterns like: [TOOL: tool_name] or <tool_name>input</tool_name>
        patterns = [
            r'\[TOOL:\s*(\w+)\]\s*(.*?)(?=\[TOOL:|$)',
            r'<(\w+)>(.*?)</\w+>',
            r'use_tool\(["\'](\w+)["\'],\s*["\'](.*?)["\']\)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, llm_response, re.DOTALL)
            for match in matches:
                tool_name = match.group(1).strip()
                tool_input = match.group(2).strip() if len(match.groups()) > 1 else ""
                tool_calls.append({"tool": tool_name, "input": tool_input})
        
        return tool_calls
    
    def _execute_tool(self, tool_name: str, tool_input: str) -> str:
        """Execute a tool by name."""
        for tool in self.tools:
            if tool.name == tool_name:
                try:
                    # For get_metrics, pass the input string directly to metrics_wrapper
                    # metrics_wrapper will handle JSON parsing internally
                    if tool_name == "get_metrics":
                        # Pass the input string directly - metrics_wrapper handles parsing
                        return tool.func(tool_input)
                    else:
                        return tool.func(tool_input)
                except Exception as e:
                    return f"Error executing tool {tool_name}: {str(e)}"
        
        return f"Tool {tool_name} not found"
    
    def _generate_sql_from_query(self, query: str, table_schema: Dict[str, Any]) -> Optional[str]:
        """Use LLM to generate SQL query from natural language."""
        schema_str = json.dumps(table_schema, indent=2)
        
        # Get sample data to help LLM understand the data
        try:
            sample_data = self.sql_tools.get_sample_data("transactions", limit=3)
            sample_str = json.dumps(sample_data, indent=2, default=str)
        except:
            sample_str = "No sample data available"
        
        prompt = f"""Given the following database schema, sample data, and user query, generate a SQL SELECT query.

Table Schema:
{schema_str}

Sample Data:
{sample_str}

User Query: {query}

IMPORTANT RULES:
1. Generate ONLY a valid SQL SELECT query - no explanations, no markdown
2. Do NOT use placeholder values like 'your_document_id', 'your_value', etc.
3. If filtering is not needed, do NOT include WHERE clauses
4. Use actual column names from the schema
5. For aggregations (SUM, COUNT, etc.), use GROUP BY appropriately
6. Order results when relevant (e.g., ORDER BY total_spend DESC for top items)

Examples:
- "top vendors by spend" -> SELECT vendor, SUM(amount) AS total_spend FROM transactions GROUP BY vendor ORDER BY total_spend DESC
- "total spending" -> SELECT SUM(amount) AS total FROM transactions
- "spending by category" -> SELECT category, SUM(amount) AS total FROM transactions GROUP BY category

Generate the SQL query now:
"""
        
        sql_query = self._call_ollama(prompt).strip()
        
        # Clean up the response (remove markdown code blocks if present)
        sql_query = re.sub(r'```sql\s*', '', sql_query)
        sql_query = re.sub(r'```\s*', '', sql_query)
        sql_query = sql_query.strip()
        
        # Remove common placeholder patterns
        placeholder_patterns = [
            r"WHERE\s+\w+\s*=\s*['\"]your_\w+['\"]",
            r"WHERE\s+\w+\s*=\s*['\"]\w+_id['\"]",
            r"WHERE\s+\w+\s*=\s*['\"]\?\?['\"]",
            r"WHERE\s+\w+\s*=\s*NULL",
        ]
        
        for pattern in placeholder_patterns:
            sql_query = re.sub(pattern, '', sql_query, flags=re.IGNORECASE)
        
        # Clean up extra whitespace and trailing commas/AND/OR
        sql_query = re.sub(r'\s+', ' ', sql_query)
        sql_query = re.sub(r'\s*,\s*$', '', sql_query)
        sql_query = re.sub(r'\s+(AND|OR)\s*$', '', sql_query, flags=re.IGNORECASE)
        sql_query = sql_query.strip()
        
        # Remove WHERE clause if it's empty or just whitespace
        if re.search(r'WHERE\s*$', sql_query, re.IGNORECASE):
            sql_query = re.sub(r'\s+WHERE\s*$', '', sql_query, flags=re.IGNORECASE)
        
        return sql_query if sql_query.startswith("SELECT") else None
    
    def process_query(
        self, 
        query: str, 
        use_rag: bool = True, 
        use_sql: bool = True
    ) -> Dict[str, Any]:
        """
        Process a natural language query and return an answer.
        
        Args:
            query: Natural language question
            use_rag: Whether to use RAG for document-based answers
            use_sql: Whether to use SQL for structured data queries
        
        Returns:
            Dictionary with answer, sources, and SQL query if applicable
        """
        # Check cache first
        if self.enable_cache:
            cache_key = self._get_cache_key(query, use_rag, use_sql)
            if cache_key in self._response_cache:
                return self._response_cache[cache_key]
        
        response = {
            "answer": "",
            "sources": [],
            "sql_query": None,
            "tool_calls": []
        }
        
        # Determine query type
        query_lower = query.lower()
        sql_keywords = ["total", "sum", "average", "count", "monthly", "vendor", "category", "spend", "spent", "amount"]
        needs_sql = any(keyword in query_lower for keyword in sql_keywords)
        
        # FAST PATH: Skip LLM for common queries - use pattern matching directly
        tool_calls = []
        skip_llm_synthesis = False
        
        if any(phrase in query_lower for phrase in ["top vendor", "vendor stat", "vendor by spend", "top vendors", "vendors by"]):
            # Use metrics tool directly
            tool_calls.append({
                "tool": "get_metrics",
                "input": json.dumps({"metric_type": "vendor_stats", "limit": 10})
            })
            skip_llm_synthesis = True
        elif any(phrase in query_lower for phrase in ["category", "by category", "category breakdown", "spending by category"]):
            # Use category breakdown
            tool_calls.append({
                "tool": "get_metrics",
                "input": json.dumps({"metric_type": "category_breakdown"})
            })
            skip_llm_synthesis = True
        elif needs_sql and use_sql:
            # Try to generate SQL query for other queries
            try:
                # Get table schema
                schema = self.sql_tools.get_table_schema("transactions")
                sql_query = self._generate_sql_from_query(query, schema)
                
                if sql_query:
                    response["sql_query"] = sql_query
                    tool_calls.append({"tool": "sql_query", "input": sql_query})
            except Exception as e:
                print(f"Error generating SQL: {e}")
        
        # If still no tool calls, use LLM to determine tools (SLOW PATH - only for complex queries)
        if not tool_calls:
            system_prompt = f"""You are an intelligent assistant that helps answer questions about documents and financial data.

You have access to the following tools:
{self._build_tool_prompt()}

When answering questions:
1. If the question asks about specific data (totals, counts, averages, etc.), use the sql_query or get_metrics tools.
2. If the question asks about documents or needs context, use the search_documents tool.
3. You can use multiple tools if needed.
4. Always cite your sources and explain your reasoning.

Format tool calls as: [TOOL: tool_name] tool_input
"""
            
            main_prompt = f"""User Question: {query}

Available tools:
{self._build_tool_prompt()}

Think step by step and determine which tools to use. Then provide your answer based on the tool results.
"""
            
            # LLM call to determine tools (only if fast path didn't work)
            initial_response = self._call_ollama(main_prompt, system_prompt, timeout=20)
            tool_calls = self._extract_tool_calls(initial_response)
        
        # Execute tools
        tool_results = []
        for tool_call in tool_calls:
            tool_name = tool_call["tool"]
            tool_input = tool_call["input"]
            
            result = self._execute_tool(tool_name, tool_input)
            tool_results.append({
                "tool": tool_name,
                "input": tool_input,
                "result": result
            })
            response["tool_calls"].append(tool_name)
        
        # If RAG is enabled and no tool calls were made, try RAG search
        if use_rag and self.rag_service and not tool_calls:
            try:
                rag_results = self.rag_service.search(query, k=3)
                response["sources"] = [r["document"] for r in rag_results]
                tool_results.append({
                    "tool": "search_documents",
                    "input": query,
                    "result": json.dumps([r["document"] for r in rag_results], default=str)
                })
            except Exception as e:
                print(f"Error in RAG search: {e}")
        
        # Synthesize final answer
        if skip_llm_synthesis and tool_results:
            # Fast path: format tool results directly without LLM
            tool_result = tool_results[0]
            response["answer"] = self._format_tool_result(
                tool_result["tool"], 
                tool_result["result"], 
                query
            )
        else:
            # Slow path: use LLM to synthesize (only for complex queries)
            system_prompt = f"""You are an intelligent assistant that helps answer questions about documents and financial data.

You have access to the following tools:
{self._build_tool_prompt()}

When answering questions:
1. If the question asks about specific data (totals, counts, averages, etc.), use the sql_query or get_metrics tools.
2. If the question asks about documents or needs context, use the search_documents tool.
3. You can use multiple tools if needed.
4. Always cite your sources and explain your reasoning.

Format tool calls as: [TOOL: tool_name] tool_input
"""
            
            synthesis_prompt = f"""User Question: {query}

Tool Results:
{json.dumps(tool_results, indent=2, default=str)}

Based on the tool results above, provide a clear, comprehensive answer to the user's question. Cite specific data and sources when available.
"""
            
            final_answer = self._call_ollama(synthesis_prompt, system_prompt, timeout=20)
            response["answer"] = final_answer
        
        # Extract sources from tool results
        if not response["sources"]:
            for tr in tool_results:
                if tr["tool"] == "search_documents":
                    try:
                        sources = json.loads(tr["result"])
                        response["sources"] = sources
                    except:
                        pass
        
        # Cache the response
        if self.enable_cache:
            cache_key = self._get_cache_key(query, use_rag, use_sql)
            self._response_cache[cache_key] = response
        
        return response

