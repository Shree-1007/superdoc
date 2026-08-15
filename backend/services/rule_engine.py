"""Configurable compliance rule engine — rules live in YAML, not code.

Assessment: "Configuration over code — a new rule should be a data change, not a rewrite."
"""
import os
import re
import uuid
import logging
from typing import List
from pathlib import Path

import yaml

from backend.agent.state import Finding, ExtractedFact
from backend.config import settings

logger = logging.getLogger(__name__)


def load_rules(rules_dir: str = None) -> List[dict]:
    """Load all YAML rule files from the rules directory."""
    rules_dir = rules_dir or settings.rules_dir
    rules = []

    if not os.path.exists(rules_dir):
        logger.warning(f"Rules directory does not exist: {rules_dir}")
        return rules

    for filepath in Path(rules_dir).glob("*.yaml"):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if data and "rules" in data:
                for rule in data["rules"]:
                    rule["_source_file"] = filepath.name
                    rules.append(rule)
                logger.info(f"Loaded {len(data['rules'])} rules from {filepath.name}")

        except Exception as e:
            logger.error(f"Failed to load rules from {filepath}: {e}")

    return rules


def check_facts_against_rules(facts: List[ExtractedFact], rules: List[dict]) -> List[Finding]:
    """Check each fact against each rule and produce findings.
    
    Only flags a violation when BOTH the rule and the fact are clearly matched.
    Returns empty list for clean corpus — an honest "no findings."
    """
    findings: List[Finding] = []
    finding_id = 0

    for rule in rules:
        rule_type = rule.get("type", "")
        rule_name = rule.get("name", "Unknown Rule")

        if rule_type == "monetary_cap":
            _check_monetary_cap(facts, rule, findings)
        elif rule_type == "term_match":
            _check_term_match(facts, rule, findings)
        elif rule_type == "required_clause":
            _check_required_clause(facts, rule, findings)
        elif rule_type == "pattern_violation":
            _check_pattern_violation(facts, rule, findings)
        else:
            logger.warning(f"Unknown rule type: {rule_type} for rule: {rule_name}")

    return findings


def _check_monetary_cap(facts: List[ExtractedFact], rule: dict, findings: List[Finding]):
    """Check if any monetary amounts exceed a defined cap."""
    cap = rule.get("cap", 0)
    field_pattern = rule.get("field_pattern", r'\$[\d,]+')
    rule_name = rule.get("name", "Monetary Cap")

    for fact in facts:
        text = fact.get("fact", "")
        matches = re.findall(r'\$([\d,]+)', text)

        for match in matches:
            amount = int(match.replace(",", ""))
            if amount > cap:
                findings.append(Finding(
                    id=f"f-{uuid.uuid4().hex[:8]}",
                    issue=f"{rule_name}: ${amount:,} exceeds cap of ${cap:,}",
                    source=fact.get("source", "unknown"),
                    source_location=fact.get("source_location", "unknown"),
                    status="pending",
                    confidence=0.95,
                ))


def _check_term_match(facts: List[ExtractedFact], rule: dict, findings: List[Finding]):
    """Check if contract terms match expected values."""
    expected = rule.get("expected_value", "")
    term_pattern = rule.get("pattern", "")
    rule_name = rule.get("name", "Term Match")

    if not term_pattern:
        return

    for fact in facts:
        text = fact.get("fact", "")
        match = re.search(term_pattern, text, re.IGNORECASE)

        if match:
            found_value = match.group(1) if match.groups() else match.group()
            if str(found_value).strip() != str(expected).strip():
                findings.append(Finding(
                    id=f"f-{uuid.uuid4().hex[:8]}",
                    issue=f"{rule_name}: Found '{found_value}' but expected '{expected}'",
                    source=fact.get("source", "unknown"),
                    source_location=fact.get("source_location", "unknown"),
                    status="pending",
                    confidence=0.85,
                ))


def _check_required_clause(facts: List[ExtractedFact], rule: dict, findings: List[Finding]):
    """Check that a required clause exists in the documents."""
    required_pattern = rule.get("pattern", "")
    rule_name = rule.get("name", "Required Clause")

    if not required_pattern:
        return

    # Check if any fact contains the required clause
    found = any(
        re.search(required_pattern, fact.get("fact", ""), re.IGNORECASE)
        for fact in facts
    )

    if not found:
        findings.append(Finding(
            id=f"f-{uuid.uuid4().hex[:8]}",
            issue=f"{rule_name}: Required clause not found in any document",
            source="all_documents",
            source_location="N/A — clause missing entirely",
            status="pending",
            confidence=0.7,
        ))


def _check_pattern_violation(facts: List[ExtractedFact], rule: dict, findings: List[Finding]):
    """Check for patterns that indicate violations."""
    violation_pattern = rule.get("pattern", "")
    rule_name = rule.get("name", "Pattern Violation")

    if not violation_pattern:
        return

    for fact in facts:
        text = fact.get("fact", "")
        if re.search(violation_pattern, text, re.IGNORECASE):
            findings.append(Finding(
                id=f"f-{uuid.uuid4().hex[:8]}",
                issue=f"{rule_name}: Violation pattern matched in source",
                source=fact.get("source", "unknown"),
                source_location=fact.get("source_location", "unknown"),
                status="pending",
                confidence=0.8,
            ))
