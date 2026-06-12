"""Basic smoke tests — just checks the agents exist and return without blowing up."""

import pytest
from agents.product_agent import ProductAgent
from agents.engineer_agent import EngineerAgent
from agents.qa_agent import QAAgent
from agents.negotiator_agent import NegotiatorAgent
from agents.output_agent import OutputAgent


SAMPLE_PRD = "Product: TestApp\n\nFeatures:\n1. Login\n   - Email/password auth\n"

SPRINT_CONTEXT = {
    "sprint": 1,
    "completed": [],
    "blocked": [],
    "velocity": 1.0,
}


def test_product_agent_exists():
    agent = ProductAgent()
    assert hasattr(agent, 'run')


def test_engineer_agent_exists():
    agent = EngineerAgent()
    assert hasattr(agent, 'run')


def test_qa_agent_exists():
    agent = QAAgent()
    assert hasattr(agent, 'run')


def test_negotiator_agent_exists():
    agent = NegotiatorAgent()
    assert hasattr(agent, 'run')


def test_output_agent_exists():
    agent = OutputAgent()
    assert hasattr(agent, 'run')
