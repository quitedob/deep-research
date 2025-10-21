# -*- coding: utf-8 -*-
"""
Research Planner for Deep Research Platform
Generates intelligent research steps and working plans
"""

import re
from typing import List, Optional, Dict, Any
from datetime import datetime


class ResearchPlanner:
    """
    Research planner that generates intelligent research steps and working plans
    based on research queries and domain knowledge.
    """

    def __init__(self):
        self.research_templates = self._load_research_templates()
        self.domain_keywords = self._load_domain_keywords()

    async def generate_research_steps(
        self,
        research_query: str,
        max_steps: int = 5,
        domain: Optional[str] = None
    ) -> List[str]:
        """
        Generate research steps based on the query

        Args:
            research_query: Main research question or topic
            max_steps: Maximum number of steps to generate
            domain: Specific domain (e.g., "technology", "business", "science")

        Returns:
            List of research steps
        """
        # Analyze the query to determine research type
        research_type = self._analyze_research_type(research_query)

        # Get appropriate template
        template = self.research_templates.get(research_type, self.research_templates["general"])

        # Generate steps
        steps = []

        # Initial exploration step
        steps.append(self._generate_initial_exploration_step(research_query))

        # Domain-specific analysis steps
        if research_type == "comparative":
            steps.extend(self._generate_comparative_steps(research_query, max_steps - 2))
        elif research_type == "analytical":
            steps.extend(self._generate_analytical_steps(research_query, max_steps - 2))
        elif research_type == "exploratory":
            steps.extend(self._generate_exploratory_steps(research_query, max_steps - 2))
        else:
            steps.extend(self._generate_general_steps(research_query, max_steps - 2))

        # Synthesis and conclusion step
        steps.append(self._generate_synthesis_step(research_query))

        return steps[:max_steps]

    def _analyze_research_type(self, query: str) -> str:
        """Analyze the research query to determine the type"""
        query_lower = query.lower()

        # Comparative research indicators
        comparative_keywords = [
            "compare", "versus", "vs", "difference", "better", "alternative",
            "evaluation", "ranking", "assessment", "pros and cons"
        ]

        # Analytical research indicators
        analytical_keywords = [
            "analyze", "analysis", "examine", "investigate", "evaluate",
            "impact", "effect", "influence", "relationship", "correlation"
        ]

        # Exploratory research indicators
        exploratory_keywords = [
            "explore", "understand", "overview", "survey", "review",
            "introduction", "background", "basics", "fundamentals"
        ]

        # Check for comparative research
        if any(keyword in query_lower for keyword in comparative_keywords):
            return "comparative"

        # Check for analytical research
        if any(keyword in query_lower for keyword in analytical_keywords):
            return "analytical"

        # Check for exploratory research
        if any(keyword in query_lower for keyword in exploratory_keywords):
            return "exploratory"

        return "general"

    def _generate_initial_exploration_step(self, query: str) -> str:
        """Generate initial exploration step"""
        return f"Conduct initial research on {query} to understand the basic concepts, definitions, and current state of knowledge"

    def _generate_comparative_steps(self, query: str, num_steps: int) -> List[str]:
        """Generate steps for comparative research"""
        steps = []

        if num_steps >= 1:
            steps.append(f"Identify key comparison criteria for {query}")

        if num_steps >= 2:
            steps.append(f"Research and analyze Option A in the {query} comparison")

        if num_steps >= 3:
            steps.append(f"Research and analyze Option B in the {query} comparison")

        if num_steps >= 4:
            steps.append(f"Compare the options based on identified criteria for {query}")

        return steps

    def _generate_analytical_steps(self, query: str, num_steps: int) -> List[str]:
        """Generate steps for analytical research"""
        steps = []

        if num_steps >= 1:
            steps.append(f"Identify key variables and factors affecting {query}")

        if num_steps >= 2:
            steps.append(f"Gather data and evidence on the impact of {query}")

        if num_steps >= 3:
            steps.append(f"Analyze the relationships and patterns related to {query}")

        if num_steps >= 4:
            steps.append(f"Evaluate the significance and implications of findings about {query}")

        return steps

    def _generate_exploratory_steps(self, query: str, num_steps: int) -> List[str]:
        """Generate steps for exploratory research"""
        steps = []

        if num_steps >= 1:
            steps.append(f"Survey existing literature and research on {query}")

        if num_steps >= 2:
            steps.append(f"Identify key concepts and terminology related to {query}")

        if num_steps >= 3:
            steps.append(f"Explore different perspectives and approaches to {query}")

        if num_steps >= 4:
            steps.append(f"Summarize current understanding and identify knowledge gaps about {query}")

        return steps

    def _generate_general_steps(self, query: str, num_steps: int) -> List[str]:
        """Generate general research steps"""
        steps = []

        for i in range(min(num_steps, 3)):
            steps.append(f"Research aspect {i+1} of {query} to build comprehensive understanding")

        return steps

    def _generate_synthesis_step(self, query: str) -> str:
        """Generate synthesis and conclusion step"""
        return f"Synthesize all research findings and develop comprehensive conclusions about {query}"

    def generate_working_plan(
        self,
        step_description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a detailed working plan for a research step

        Args:
            step_description: Description of the research step
            context: Additional context information

        Returns:
            Detailed working plan
        """
        context = context or {}

        working_plan = f"""Working Plan for: {step_description}

Objective: {step_description}

Key Actions:
1. Define specific research questions related to this step
2. Identify appropriate information sources and search strategies
3. Systematically gather relevant information
4. Analyze and evaluate the collected information
5. Document findings and insights

Expected Deliverables:
- Comprehensive information relevant to the step objective
- Analysis and evaluation of gathered information
- Key findings and insights
- Documentation of sources and evidence

Quality Criteria:
- Information relevance and accuracy
- Depth and breadth of coverage
- Critical analysis and evaluation
- Clear documentation and organization
"""

        if context.get("previous_findings"):
            working_plan += f"""

Previous Context:
{context['previous_findings']}

Building upon previous research findings, ensure continuity and coherence in the research process.
"""

        if context.get("specific_requirements"):
            working_plan += f"""

Specific Requirements:
{context['specific_requirements']}

Ensure all specific requirements are addressed in the research process.
"""

        return working_plan

    def evaluate_research_progress(
        self,
        plan: Any,  # Plan object
        current_step: int,
        findings: List[str],
        evidence_count: int
    ) -> Dict[str, Any]:
        """
        Evaluate research progress and provide recommendations

        Args:
            plan: Current research plan
            current_step: Current step index
            findings: List of research findings
            evidence_count: Number of evidence items collected

        Returns:
            Progress evaluation and recommendations
        """
        total_steps = len(plan.subtasks) if hasattr(plan, 'subtasks') else 5
        progress_percentage = (current_step / total_steps) * 100

        evaluation = {
            "progress_percentage": progress_percentage,
            "current_step": current_step,
            "total_steps": total_steps,
            "findings_count": len(findings),
            "evidence_count": evidence_count
        }

        # Assess research quality
        if evidence_count == 0:
            evaluation["quality_score"] = "Poor"
            evaluation["recommendation"] = "Need to gather more evidence and conduct deeper research"
        elif evidence_count < 3:
            evaluation["quality_score"] = "Fair"
            evaluation["recommendation"] = "Consider gathering additional evidence to strengthen findings"
        elif evidence_count < 6:
            evaluation["quality_score"] = "Good"
            evaluation["recommendation"] = "Research is progressing well, continue with current approach"
        else:
            evaluation["quality_score"] = "Excellent"
            evaluation["recommendation"] = "Strong evidence base, ready for synthesis and conclusion"

        # Check if ready for next step
        if len(findings) > 0 and evidence_count >= 2:
            evaluation["ready_for_next_step"] = True
        else:
            evaluation["ready_for_next_step"] = False

        return evaluation

    def _load_research_templates(self) -> Dict[str, Any]:
        """Load research templates for different types"""
        return {
            "comparative": {
                "description": "For comparing different options, approaches, or alternatives",
                "structure": ["criteria_identification", "option_a_research", "option_b_research", "comparison_analysis", "recommendation"]
            },
            "analytical": {
                "description": "For analyzing impacts, relationships, or causal factors",
                "structure": ["variable_identification", "data_collection", "relationship_analysis", "impact_evaluation", "conclusion"]
            },
            "exploratory": {
                "description": "For exploring new topics or understanding complex subjects",
                "structure": ["literature_survey", "concept_definition", "perspective_analysis", "synthesis", "gap_identification"]
            },
            "general": {
                "description": "General research approach for various topics",
                "structure": ["initial_exploration", "in_depth_research", "analysis", "synthesis", "conclusion"]
            }
        }

    def _load_domain_keywords(self) -> Dict[str, List[str]]:
        """Load domain-specific keywords"""
        return {
            "technology": ["AI", "machine learning", "software", "algorithm", "data", "programming", "development"],
            "business": ["market", "strategy", "management", "finance", "marketing", "sales", "operations"],
            "science": ["research", "experiment", "hypothesis", "data", "analysis", "methodology", "results"],
            "healthcare": ["medical", "health", "treatment", "diagnosis", "patient", "clinical", "research"],
            "education": ["learning", "teaching", "student", "curriculum", "pedagogy", "assessment", "institution"]
        }