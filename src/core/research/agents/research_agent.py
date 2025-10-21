# -*- coding: utf-8 -*-
"""
Research Agent for Deep Research Platform
Specialized agent for conducting comprehensive research tasks
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base_agent import BaseResearchAgent, AgentCapability, AgentTask
from ...tools.search.web_search import WebSearchTool
from ...tools.search.wikipedia_tool import WikipediaTool
from ...tools.search.arxiv_tool import ArxivTool


class ResearchAgent(BaseResearchAgent):
    """
    Specialized research agent that conducts comprehensive research using
    multiple search tools and analytical capabilities
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        search_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize research agent

        Args:
            agent_id: Unique identifier for the agent
            search_config: Configuration for search tools
        """
        # Define research capabilities
        capabilities = [
            AgentCapability(
                name="web_search",
                description="Search the web for information",
                priority=1
            ),
            AgentCapability(
                name="academic_search",
                description="Search academic papers and research",
                priority=2
            ),
            AgentCapability(
                name="wikipedia_search",
                description="Search Wikipedia for encyclopedic information",
                priority=1
            ),
            AgentCapability(
                name="research_synthesis",
                description="Synthesize research findings from multiple sources",
                priority=3
            ),
            AgentCapability(
                name="source_evaluation",
                description="Evaluate credibility and quality of sources",
                priority=2
            )
        ]

        super().__init__(
            agent_id=agent_id or f"research_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name="Research Agent",
            capabilities=capabilities,
            max_concurrent_tasks=5,
            timeout=600  # 10 minutes timeout for research tasks
        )

        # Initialize search tools
        self.search_config = search_config or {}
        self.web_search = WebSearchTool()
        self.wikipedia_search = WikipediaTool()
        self.arxiv_search = ArxivTool()

        # Research state
        self.current_research_context: Optional[Dict[str, Any]] = None
        self.search_history: List[Dict[str, Any]] = []

    async def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """
        Process a research task

        Args:
            task: Research task to process

        Returns:
            Research results
        """
        task_type = task.task_type
        parameters = task.parameters

        try:
            if task_type == "web_search":
                return await self._perform_web_search(parameters)
            elif task_type == "academic_search":
                return await self._perform_academic_search(parameters)
            elif task_type == "wikipedia_search":
                return await self._perform_wikipedia_search(parameters)
            elif task_type == "research_synthesis":
                return await self._synthesize_research(parameters)
            elif task_type == "comprehensive_research":
                return await self._perform_comprehensive_research(parameters)
            elif task_type == "source_evaluation":
                return await self._evaluate_sources(parameters)
            else:
                raise ValueError(f"Unknown task type: {task_type}")

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "task_type": task_type,
                "parameters": parameters
            }

    def get_agent_type(self) -> str:
        """Get the agent type identifier"""
        return "research_agent"

    async def _perform_web_search(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Perform web search"""
        query = parameters.get("query", "")
        max_results = parameters.get("max_results", 10)
        search_depth = parameters.get("search_depth", "basic")

        if not query:
            raise ValueError("Search query is required")

        # Perform search
        search_results = await self.web_search.search(
            query=query,
            max_results=max_results,
            search_depth=search_depth
        )

        # Process and analyze results
        processed_results = []
        for result in search_results:
            processed_result = {
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "snippet": result.get("snippet", ""),
                "relevance_score": self._calculate_relevance_score(query, result),
                "source_type": "web",
                "timestamp": datetime.now().isoformat()
            }
            processed_results.append(processed_result)

        # Store in search history
        search_record = {
            "type": "web_search",
            "query": query,
            "results_count": len(processed_results),
            "timestamp": datetime.now().isoformat()
        }
        self.search_history.append(search_record)

        return {
            "success": True,
            "query": query,
            "results": processed_results,
            "total_results": len(processed_results),
            "search_metadata": {
                "search_depth": search_depth,
                "max_requested": max_results,
                "search_time": search_record["timestamp"]
            }
        }

    async def _perform_academic_search(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Perform academic search"""
        query = parameters.get("query", "")
        max_results = parameters.get("max_results", 10)
        subject_area = parameters.get("subject_area", "all")

        if not query:
            raise ValueError("Search query is required")

        # Search academic papers
        academic_results = await self.arxiv_search.search(
            query=query,
            max_results=max_results,
            subject_area=subject_area
        )

        # Process academic results
        processed_results = []
        for paper in academic_results:
            processed_paper = {
                "title": paper.get("title", ""),
                "authors": paper.get("authors", []),
                "abstract": paper.get("abstract", ""),
                "arxiv_id": paper.get("id", ""),
                "published_date": paper.get("published", ""),
                "relevance_score": self._calculate_academic_relevance(query, paper),
                "source_type": "academic",
                "pdf_url": paper.get("pdf_url", ""),
                "timestamp": datetime.now().isoformat()
            }
            processed_results.append(processed_paper)

        # Store in search history
        search_record = {
            "type": "academic_search",
            "query": query,
            "subject_area": subject_area,
            "results_count": len(processed_results),
            "timestamp": datetime.now().isoformat()
        }
        self.search_history.append(search_record)

        return {
            "success": True,
            "query": query,
            "subject_area": subject_area,
            "results": processed_results,
            "total_results": len(processed_results),
            "search_metadata": {
                "max_requested": max_results,
                "search_time": search_record["timestamp"]
            }
        }

    async def _perform_wikipedia_search(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Perform Wikipedia search"""
        query = parameters.get("query", "")
        max_results = parameters.get("max_results", 5)
        language = parameters.get("language", "en")

        if not query:
            raise ValueError("Search query is required")

        # Search Wikipedia
        wiki_results = await self.wikipedia_search.search(
            query=query,
            max_results=max_results,
            language=language
        )

        # Process Wikipedia results
        processed_results = []
        for article in wiki_results:
            processed_article = {
                "title": article.get("title", ""),
                "summary": article.get("summary", ""),
                "url": article.get("url", ""),
                "page_id": article.get("pageid", ""),
                "relevance_score": self._calculate_wikipedia_relevance(query, article),
                "source_type": "wikipedia",
                "timestamp": datetime.now().isoformat()
            }
            processed_results.append(processed_article)

        # Store in search history
        search_record = {
            "type": "wikipedia_search",
            "query": query,
            "language": language,
            "results_count": len(processed_results),
            "timestamp": datetime.now().isoformat()
        }
        self.search_history.append(search_record)

        return {
            "success": True,
            "query": query,
            "language": language,
            "results": processed_results,
            "total_results": len(processed_results),
            "search_metadata": {
                "max_requested": max_results,
                "search_time": search_record["timestamp"]
            }
        }

    async def _perform_comprehensive_research(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive research using multiple sources"""
        query = parameters.get("query", "")
        research_depth = parameters.get("research_depth", "medium")
        include_academic = parameters.get("include_academic", True)
        include_wikipedia = parameters.get("include_wikipedia", True)
        max_sources = parameters.get("max_sources", 20)

        if not query:
            raise ValueError("Research query is required")

        all_results = []
        search_metadata = []

        # Web search (always included)
        web_max = max_sources // 2 if (include_academic or include_wikipedia) else max_sources
        web_result = await self._perform_web_search({
            "query": query,
            "max_results": web_max,
            "search_depth": research_depth
        })
        all_results.extend(web_result["results"])
        search_metadata.append(web_result["search_metadata"])

        # Academic search
        if include_academic:
            academic_max = max_sources // 3
            academic_result = await self._perform_academic_search({
                "query": query,
                "max_results": academic_max
            })
            all_results.extend(academic_result["results"])
            search_metadata.append(academic_result["search_metadata"])

        # Wikipedia search
        if include_wikipedia:
            wiki_max = min(5, max_sources - len(all_results))
            wiki_result = await self._perform_wikipedia_search({
                "query": query,
                "max_results": wiki_max
            })
            all_results.extend(wiki_result["results"])
            search_metadata.append(wiki_result["search_metadata"])

        # Sort by relevance score
        all_results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

        # Limit total results
        all_results = all_results[:max_sources]

        # Store comprehensive research in history
        research_record = {
            "type": "comprehensive_research",
            "query": query,
            "research_depth": research_depth,
            "total_sources": len(all_results),
            "timestamp": datetime.now().isoformat()
        }
        self.search_history.append(research_record)

        return {
            "success": True,
            "query": query,
            "research_depth": research_depth,
            "results": all_results,
            "total_results": len(all_results),
            "source_breakdown": {
                "web": len([r for r in all_results if r["source_type"] == "web"]),
                "academic": len([r for r in all_results if r["source_type"] == "academic"]),
                "wikipedia": len([r for r in all_results if r["source_type"] == "wikipedia"])
            },
            "search_metadata": search_metadata
        }

    async def _synthesize_research(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize research findings from multiple sources"""
        research_results = parameters.get("research_results", [])
        synthesis_type = parameters.get("synthesis_type", "summary")
        focus_areas = parameters.get("focus_areas", [])

        if not research_results:
            raise ValueError("Research results are required for synthesis")

        # Extract key information from results
        key_findings = []
        sources_by_type = {"web": [], "academic": [], "wikipedia": []}

        for result in research_results:
            # Categorize sources
            source_type = result.get("source_type", "web")
            if source_type in sources_by_type:
                sources_by_type[source_type].append(result)

            # Extract key findings
            if result.get("relevance_score", 0) > 0.6:  # High relevance threshold
                key_finding = {
                    "content": result.get("snippet") or result.get("abstract") or result.get("summary", ""),
                    "source": result.get("title", ""),
                    "source_type": source_type,
                    "relevance": result.get("relevance_score", 0),
                    "url": result.get("url", "")
                }
                key_findings.append(key_finding)

        # Generate synthesis based on type
        if synthesis_type == "summary":
            synthesis = await self._generate_summary_synthesis(key_findings, focus_areas)
        elif synthesis_type == "comparative":
            synthesis = await self._generate_comparative_synthesis(sources_by_type, focus_areas)
        elif synthesis_type == "analytical":
            synthesis = await self._generate_analytical_synthesis(key_findings, sources_by_type, focus_areas)
        else:
            synthesis = await self._generate_summary_synthesis(key_findings, focus_areas)

        return {
            "success": True,
            "synthesis_type": synthesis_type,
            "synthesis": synthesis,
            "key_findings_count": len(key_findings),
            "sources_analyzed": len(research_results),
            "source_breakdown": {
                source_type: len(sources)
                for source_type, sources in sources_by_type.items()
            },
            "focus_areas": focus_areas
        }

    async def _evaluate_sources(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate credibility and quality of sources"""
        sources = parameters.get("sources", [])
        evaluation_criteria = parameters.get("criteria", ["relevance", "credibility", "recency"])

        if not sources:
            raise ValueError("Sources are required for evaluation")

        evaluated_sources = []
        for source in sources:
            evaluation = {
                "source": source.get("title", ""),
                "url": source.get("url", ""),
                "evaluations": {}
            }

            # Relevance evaluation
            if "relevance" in evaluation_criteria:
                relevance_score = source.get("relevance_score", 0.5)
                evaluation["evaluations"]["relevance"] = {
                    "score": relevance_score,
                    "assessment": self._assess_relevance(relevance_score)
                }

            # Credibility evaluation
            if "credibility" in evaluation_criteria:
                credibility_score = self._evaluate_credibility(source)
                evaluation["evaluations"]["credibility"] = {
                    "score": credibility_score,
                    "assessment": self._assess_credibility(credibility_score)
                }

            # Recency evaluation
            if "recency" in evaluation_criteria:
                recency_score = self._evaluate_recency(source)
                evaluation["evaluations"]["recency"] = {
                    "score": recency_score,
                    "assessment": self._assess_recency(recency_score)
                }

            # Overall quality score
            evaluation["overall_score"] = sum(
                eval_data["score"] for eval_data in evaluation["evaluations"].values()
            ) / len(evaluation["evaluations"])

            evaluated_sources.append(evaluation)

        # Sort by overall quality
        evaluated_sources.sort(key=lambda x: x["overall_score"], reverse=True)

        return {
            "success": True,
            "evaluated_sources": evaluated_sources,
            "total_sources": len(sources),
            "evaluation_criteria": evaluation_criteria,
            "average_quality": sum(s["overall_score"] for s in evaluated_sources) / len(evaluated_sources)
        }

    async def _generate_summary_synthesis(self, key_findings: List[Dict[str, Any]], focus_areas: List[str]) -> str:
        """Generate summary synthesis of research findings"""
        if not key_findings:
            return "No significant findings to synthesize."

        # Group findings by similarity
        grouped_findings = self._group_similar_findings(key_findings)

        # Generate summary
        summary_parts = []
        summary_parts.append(f"Based on analysis of {len(key_findings)} high-relevance sources:")

        for i, group in enumerate(grouped_findings[:5]):  # Top 5 groups
            group_summary = f"\n{i+1}. Key Finding: {group['theme']}"
            group_summary += f"\n   Supported by {len(group['findings'])} sources"
            for finding in group['findings'][:2]:  # Top 2 findings in each group
                group_summary += f"\n   - {finding['content'][:150]}..."
            summary_parts.append(group_summary)

        if focus_areas:
            summary_parts.append(f"\nSpecial focus on: {', '.join(focus_areas)}")

        return "".join(summary_parts)

    async def _generate_comparative_synthesis(self, sources_by_type: Dict[str, List], focus_areas: List[str]) -> str:
        """Generate comparative synthesis across different source types"""
        synthesis_parts = []
        synthesis_parts.append("Comparative Analysis Across Source Types:")

        for source_type, sources in sources_by_type.items():
            if sources:
                synthesis_parts.append(f"\n{source_type.title()} Sources ({len(sources)} sources):")

                # Calculate average relevance for this source type
                avg_relevance = sum(s.get("relevance_score", 0) for s in sources) / len(sources)
                synthesis_parts.append(f"  Average Relevance: {avg_relevance:.2f}")

                # Extract top themes
                themes = self._extract_themes(sources[:3])  # Top 3 sources
                for theme in themes:
                    synthesis_parts.append(f"  - {theme}")

        return "".join(synthesis_parts)

    async def _generate_analytical_synthesis(self, key_findings: List[Dict[str, Any]], sources_by_type: Dict[str, List], focus_areas: List[str]) -> str:
        """Generate analytical synthesis with deeper insights"""
        synthesis_parts = []
        synthesis_parts.append("Analytical Synthesis:")

        # Source type analysis
        synthesis_parts.append("\nSource Type Distribution:")
        for source_type, sources in sources_by_type.items():
            if sources:
                percentage = (len(sources) / sum(len(s) for s in sources_by_type.values())) * 100
                synthesis_parts.append(f"  {source_type.title()}: {len(sources)} sources ({percentage:.1f}%)")

        # Quality assessment
        high_quality_sources = sum(
            1 for finding in key_findings
            if finding.get("relevance", 0) > 0.8
        )
        synthesis_parts.append(f"\nQuality Assessment:")
        synthesis_parts.append(f"  High-quality sources: {high_quality_sources}/{len(key_findings)}")
        synthesis_parts.append(f"  Overall research quality: {(high_quality_sources/len(key_findings))*100:.1f}%")

        # Key insights
        synthesis_parts.append("\nKey Insights:")
        top_findings = sorted(key_findings, key=lambda x: x.get("relevance", 0), reverse=True)[:3]
        for i, finding in enumerate(top_findings):
            synthesis_parts.append(f"  {i+1}. {finding['content'][:200]}...")

        return "".join(synthesis_parts)

    def _calculate_relevance_score(self, query: str, result: Dict[str, Any]) -> float:
        """Calculate relevance score for web search results"""
        title = result.get("title", "").lower()
        snippet = result.get("snippet", "").lower()
        query_terms = query.lower().split()

        score = 0.0
        for term in query_terms:
            if term in title:
                score += 0.3
            if term in snippet:
                score += 0.2

        # Boost for exact phrase matches
        if query.lower() in title:
            score += 0.5
        if query.lower() in snippet:
            score += 0.3

        return min(score, 1.0)

    def _calculate_academic_relevance(self, query: str, paper: Dict[str, Any]) -> float:
        """Calculate relevance score for academic papers"""
        title = paper.get("title", "").lower()
        abstract = paper.get("abstract", "").lower()
        query_terms = query.lower().split()

        score = 0.0
        for term in query_terms:
            if term in title:
                score += 0.4  # Higher weight for title matches in academic papers
            if term in abstract:
                score += 0.2

        return min(score, 1.0)

    def _calculate_wikipedia_relevance(self, query: str, article: Dict[str, Any]) -> float:
        """Calculate relevance score for Wikipedia articles"""
        title = article.get("title", "").lower()
        summary = article.get("summary", "").lower()
        query_terms = query.lower().split()

        score = 0.0
        for term in query_terms:
            if term in title:
                score += 0.5  # High weight for title matches
            if term in summary:
                score += 0.2

        return min(score, 1.0)

    def _group_similar_findings(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group similar findings by theme"""
        # Simplified grouping - in practice this would use more sophisticated NLP
        themes = {}

        for finding in findings:
            content = finding.get("content", "")[:100]  # First 100 chars
            theme_key = content.split()[0] if content else "general"

            if theme_key not in themes:
                themes[theme_key] = {
                    "theme": theme_key.title(),
                    "findings": []
                }
            themes[theme_key]["findings"].append(finding)

        # Sort by number of findings
        return sorted(themes.values(), key=lambda x: len(x["findings"]), reverse=True)

    def _extract_themes(self, sources: List[Dict[str, Any]]) -> List[str]:
        """Extract key themes from sources"""
        themes = []
        for source in sources:
            title = source.get("title", "")
            if title:
                themes.append(title[:80] + "..." if len(title) > 80 else title)
        return themes[:3]  # Top 3 themes

    def _evaluate_credibility(self, source: Dict[str, Any]) -> float:
        """Evaluate source credibility"""
        score = 0.5  # Base score

        source_type = source.get("source_type", "")
        if source_type == "academic":
            score += 0.3
        elif source_type == "wikipedia":
            score += 0.2
        elif source_type == "web":
            # Check for credible domains
            url = source.get("url", "").lower()
            if any(domain in url for domain in ["edu", "gov", "org"]):
                score += 0.2

        return min(score, 1.0)

    def _evaluate_recency(self, source: Dict[str, Any]) -> float:
        """Evaluate source recency"""
        # Simplified recency evaluation
        return 0.7  # Default score

    def _assess_relevance(self, score: float) -> str:
        """Assess relevance level"""
        if score >= 0.8:
            return "Highly Relevant"
        elif score >= 0.6:
            return "Relevant"
        elif score >= 0.4:
            return "Somewhat Relevant"
        else:
            return "Not Relevant"

    def _assess_credibility(self, score: float) -> str:
        """Assess credibility level"""
        if score >= 0.8:
            return "Highly Credible"
        elif score >= 0.6:
            return "Credible"
        elif score >= 0.4:
            return "Moderately Credible"
        else:
            return "Low Credibility"

    def _assess_recency(self, score: float) -> str:
        """Assess recency level"""
        if score >= 0.8:
            return "Very Recent"
        elif score >= 0.6:
            return "Recent"
        elif score >= 0.4:
            return "Moderately Recent"
        else:
            return "Outdated"