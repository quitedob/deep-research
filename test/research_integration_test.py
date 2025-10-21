#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Research Integration Tests
Tests the complete research workflow integration
"""

import asyncio
import pytest
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.plan.plan import Plan, SubTask, PlanStatus, SubTaskStatus
from core.plan.plan_notebook import PlanNotebook
from core.plan.planner import ResearchPlanner
from core.research.multi_agent_orchestrator import MultiAgentOrchestrator
from core.research.evidence_chain import EvidenceChainAnalyzer
from core.research.agents.research_agent import ResearchAgent
from core.research.agents.evidence_agent import EvidenceAgent
from core.research.agents.synthesis_agent import SynthesisAgent

class TestResearchIntegration:
    """Comprehensive research workflow integration tests"""

    @pytest.fixture
    async def setup_research_system(self):
        """Setup the complete research system for testing"""

        # Initialize components
        self.plan_notebook = PlanNotebook()
        self.planner = ResearchPlanner()
        self.orchestrator = MultiAgentOrchestrator()
        self.evidence_analyzer = EvidenceChainAnalyzer()

        # Initialize agents
        self.research_agent = ResearchAgent("test_research_agent")
        self.evidence_agent = EvidenceAgent("test_evidence_agent")
        self.synthesis_agent = SynthesisAgent("test_synthesis_agent")

        # Register agents with orchestrator
        await self.orchestrator.register_agent(self.research_agent)
        await self.orchestrator.register_agent(self.evidence_agent)
        await self.orchestrator.register_agent(self.synthesis_agent)

        yield {
            'plan_notebook': self.plan_notebook,
            'planner': self.planner,
            'orchestrator': self.orchestrator,
            'evidence_analyzer': self.evidence_analyzer,
            'agents': {
                'research': self.research_agent,
                'evidence': self.evidence_agent,
                'synthesis': self.synthesis_agent
            }
        }

    @pytest.mark.asyncio
    async def test_complete_research_workflow(self, setup_research_system):
        """Test the complete research workflow from planning to synthesis"""

        system = setup_research_system

        # Step 1: Create research plan
        plan_data = {
            "title": "AI Ethics Research",
            "description": "Comprehensive analysis of AI ethics principles and frameworks",
            "domain": "technology",
            "research_type": "analytical",
            "research_query": "What are the main ethical considerations in AI development?"
        }

        plan = await system['planner'].create_research_plan(
            title=plan_data['title'],
            description=plan_data['description'],
            domain=plan_data['domain'],
            research_type=plan_data['research_type'],
            research_query=plan_data['research_query']
        )

        assert plan is not None
        assert plan.status == PlanStatus.CREATED
        assert len(plan.subtasks) > 0

        # Step 2: Add plan to notebook
        await system['plan_notebook'].add_plan(plan)

        # Step 3: Execute research orchestration
        orchestration_result = await system['orchestrator'].execute_research_workflow(
            plan_id=plan.id,
            execution_strategy="sequential"
        )

        assert orchestration_result is not None
        assert orchestration_result.get('status') in ['completed', 'in_progress']

        # Step 4: Analyze evidence chains
        if orchestration_result.get('evidence_data'):
            evidence_analysis = await system['evidence_analyzer'].analyze_evidence_chain(
                evidence_items=orchestration_result['evidence_data'],
                research_query=plan_data['research_query']
            )

            assert evidence_analysis is not None
            assert 'confidence_level' in evidence_analysis
            assert 'quality_score' in evidence_analysis

        # Step 5: Generate synthesis
        synthesis_result = await system['agents']['synthesis'].synthesize_research(
            plan_id=plan.id,
            evidence_data=orchestration_result.get('evidence_data', []),
            research_findings=orchestration_result.get('findings', [])
        )

        assert synthesis_result is not None
        assert 'content' in synthesis_result
        assert 'key_insights' in synthesis_result

        print(f"✅ Complete research workflow test passed for plan: {plan.id}")

    @pytest.mark.asyncio
    async def test_multi_agent_coordination(self, setup_research_system):
        """Test multi-agent coordination and communication"""

        system = setup_research_system

        # Create a complex research task
        plan = await system['planner'].create_research_plan(
            title="Climate Change Impact Analysis",
            description="Multi-dimensional analysis of climate change effects",
            domain="environment",
            research_type="comparative",
            research_query="What are the primary impacts of climate change on biodiversity?"
        )

        # Test agent task assignment
        task_assignments = await system['orchestrator'].assign_tasks_to_agents(
            plan_id=plan.id,
            available_agents=list(system['agents'].values())
        )

        assert len(task_assignments) > 0

        # Test parallel execution
        parallel_result = await system['orchestrator'].execute_parallel_workflow(
            plan_id=plan.id,
            task_assignments=task_assignments
        )

        assert parallel_result is not None
        assert 'completed_tasks' in parallel_result
        assert 'failed_tasks' in parallel_result

        print(f"✅ Multi-agent coordination test passed for {len(task_assignments)} agents")

    @pytest.mark.asyncio
    async def test_evidence_chain_quality_assessment(self, setup_research_system):
        """Test evidence chain quality assessment and analysis"""

        system = setup_research_system

        # Create sample evidence items
        evidence_items = [
            {
                "id": "evidence_1",
                "content": "Scientific study shows 70% of species are affected by climate change",
                "source": "Nature Journal",
                "evidence_type": "academic",
                "confidence_score": 0.9,
                "relevance_score": 0.85
            },
            {
                "id": "evidence_2",
                "content": "Government report on biodiversity loss patterns",
                "source": "Environmental Protection Agency",
                "evidence_type": "government",
                "confidence_score": 0.95,
                "relevance_score": 0.9
            },
            {
                "id": "evidence_3",
                "content": "Field observations of species migration",
                "source": "Research blog",
                "evidence_type": "observational",
                "confidence_score": 0.7,
                "relevance_score": 0.8
            }
        ]

        # Test evidence quality assessment
        quality_assessment = await system['evidence_analyzer'].assess_evidence_quality(
            evidence_items=evidence_items
        )

        assert quality_assessment is not None
        assert 'overall_quality' in quality_assessment
        assert 'quality_by_type' in quality_assessment

        # Test evidence relationship analysis
        relationship_analysis = await system['evidence_analyzer'].analyze_evidence_relationships(
            evidence_items=evidence_items
        )

        assert relationship_analysis is not None
        assert 'relationships' in relationship_analysis
        assert 'confidence_map' in relationship_analysis

        print(f"✅ Evidence chain quality assessment test passed")

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, setup_research_system):
        """Test error handling and recovery mechanisms"""

        system = setup_research_system

        # Create a plan that might fail
        plan = await system['planner'].create_research_plan(
            title="Test Error Handling",
            description="Plan designed to test error scenarios",
            domain="test",
            research_type="exploratory",
            research_query="Invalid query for testing error handling"
        )

        # Test graceful error handling
        try:
            result = await system['orchestrator'].execute_research_workflow(
                plan_id=plan.id,
                execution_strategy="sequential",
                error_handling_strategy="graceful"
            )

            # Should not crash, should return error information
            assert result is not None
            assert 'status' in result

        except Exception as e:
            # Should not reach here for graceful handling
            pytest.fail(f"Graceful error handling failed: {e}")

        # Test agent recovery mechanisms
        recovery_result = await system['orchestrator'].handle_agent_failure(
            agent_id=system['agents']['research'].id,
            failure_type="timeout",
            recovery_strategy="restart"
        )

        assert recovery_result is not None
        assert 'recovery_status' in recovery_result

        print(f"✅ Error handling and recovery test passed")

    @pytest.mark.asyncio
    async def test_performance_monitoring(self, setup_research_system):
        """Test performance monitoring and metrics collection"""

        system = setup_research_system

        # Start performance monitoring
        monitoring_session = await system['orchestrator'].start_performance_monitoring()

        # Execute a research workflow
        plan = await system['planner'].create_research_plan(
            title="Performance Test Plan",
            description="Plan for testing performance monitoring",
            domain="test",
            research_type="analytical",
            research_query="How well does the system perform under test conditions?"
        )

        # Execute workflow with monitoring
        result = await system['orchestrator'].execute_research_workflow(
            plan_id=plan.id,
            execution_strategy="sequential",
            monitoring_session=monitoring_session
        )

        # Stop monitoring and get metrics
        metrics = await system['orchestrator'].stop_performance_monitoring(monitoring_session)

        assert metrics is not None
        assert 'execution_time' in metrics
        assert 'agent_performance' in metrics
        assert 'resource_usage' in metrics
        assert 'error_rate' in metrics

        # Validate metrics structure
        for agent_id, agent_metrics in metrics['agent_performance'].items():
            assert 'tasks_completed' in agent_metrics
            assert 'average_task_time' in agent_metrics
            assert 'success_rate' in agent_metrics

        print(f"✅ Performance monitoring test passed")

    def test_plan_notebook_functionality(self, setup_research_system):
        """Test PlanNotebook CRUD operations and functionality"""

        system = setup_research_system

        # Test plan creation
        plan = Plan(
            id="test_plan_1",
            title="Test Plan",
            description="A test plan for unit testing",
            status=PlanStatus.CREATED
        )

        # Test adding plan
        asyncio.run(system['plan_notebook'].add_plan(plan))

        # Test retrieving plan
        retrieved_plan = asyncio.run(system['plan_notebook'].get_plan("test_plan_1"))
        assert retrieved_plan is not None
        assert retrieved_plan.id == "test_plan_1"
        assert retrieved_plan.title == "Test Plan"

        # Test listing plans
        plans = asyncio.run(system['plan_notebook'].list_plans())
        assert len(plans) >= 1
        assert any(p.id == "test_plan_1" for p in plans)

        # Test updating plan
        plan.description = "Updated test plan description"
        asyncio.run(system['plan_notebook'].update_plan(plan))

        updated_plan = asyncio.run(system['plan_notebook'].get_plan("test_plan_1"))
        assert updated_plan.description == "Updated test plan description"

        # Test deleting plan
        asyncio.run(system['plan_notebook'].delete_plan("test_plan_1"))

        deleted_plan = asyncio.run(system['plan_notebook'].get_plan("test_plan_1"))
        assert deleted_plan is None

        print(f"✅ PlanNotebook functionality test passed")

    @pytest.mark.asyncio
    async def test_agent_capabilities_and_communication(self, setup_research_system):
        """Test individual agent capabilities and inter-agent communication"""

        system = setup_research_system

        # Test research agent capabilities
        research_task = {
            "type": "literature_review",
            "query": "test query for research",
            "parameters": {"depth": "comprehensive"}
        }

        research_result = await system['agents']['research'].execute_task(research_task)
        assert research_result is not None
        assert 'status' in research_result
        assert 'result' in research_result

        # Test evidence agent capabilities
        evidence_task = {
            "type": "evidence_collection",
            "sources": ["test_source_1", "test_source_2"],
            "criteria": {"relevance": "high", "quality": "academic"}
        }

        evidence_result = await system['agents']['evidence'].execute_task(evidence_task)
        assert evidence_result is not None
        assert 'evidence_items' in evidence_result

        # Test synthesis agent capabilities
        synthesis_task = {
            "type": "research_synthesis",
            "evidence": evidence_result.get('evidence_items', []),
            "research_findings": research_result.get('result', {}),
            "synthesis_type": "comprehensive"
        }

        synthesis_result = await system['agents']['synthesis'].execute_task(synthesis_task)
        assert synthesis_result is not None
        assert 'synthesis_content' in synthesis_result
        assert 'key_insights' in synthesis_result

        # Test inter-agent communication
        communication_result = await system['orchestrator'].facilitate_agent_communication(
            sender_id=system['agents']['research'].id,
            receiver_id=system['agents']['evidence'].id,
            message={
                "type": "evidence_request",
                "content": "Please collect evidence for the following research findings",
                "data": research_result.get('result', {})
            }
        )

        assert communication_result is not None
        assert 'status' in communication_result

        print(f"✅ Agent capabilities and communication test passed")

# Integration test runner
async def run_integration_tests():
    """Run all integration tests"""

    print("=" * 60)
    print("DEEP RESEARCH PLATFORM - INTEGRATION TESTS")
    print("=" * 60)

    test_instance = TestResearchIntegration()

    tests = [
        ("PlanNotebook Functionality", test_instance.test_plan_notebook_functionality),
        ("Complete Research Workflow", test_instance.test_complete_research_workflow),
        ("Multi-Agent Coordination", test_instance.test_multi_agent_coordination),
        ("Evidence Chain Quality Assessment", test_instance.test_evidence_chain_quality_assessment),
        ("Error Handling and Recovery", test_instance.test_error_handling_and_recovery),
        ("Performance Monitoring", test_instance.test_performance_monitoring),
        ("Agent Capabilities and Communication", test_instance.test_agent_capabilities_and_communication)
    ]

    passed_tests = 0
    total_tests = len(tests)

    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Running test: {test_name}")

            # Setup for each test
            setup = await test_instance.setup_research_system()

            # Run the test
            if asyncio.iscoroutinefunction(test_func):
                await test_func(setup)
            else:
                test_func(setup)

            print(f"✅ PASSED: {test_name}")
            passed_tests += 1

        except Exception as e:
            print(f"❌ FAILED: {test_name} - {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"INTEGRATION TEST RESULTS: {passed_tests}/{total_tests} tests passed")
    print("=" * 60)

    if passed_tests == total_tests:
        print("🎉 ALL INTEGRATION TESTS PASSED!")
        return True
    else:
        print("💥 SOME TESTS FAILED - CHECK THE LOGS ABOVE")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_integration_tests())
    sys.exit(0 if success else 1)