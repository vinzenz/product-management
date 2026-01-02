"""Persona and Specialization models for perspective switching."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Specialization(str, Enum):
    """Built-in specialization types."""

    PRODUCT_MANAGER = "product_manager"
    ENGINEER = "engineer"
    DESIGNER = "designer"
    MARKETER = "marketer"
    USER_RESEARCHER = "user_researcher"
    QA_ENGINEER = "qa_engineer"
    ARCHITECT = "architect"
    CUSTOM = "custom"


@dataclass
class Persona:
    """A persona representing a specific perspective or role."""

    id: str
    name: str
    specialization: Specialization
    description: str = ""
    expertise: list[str] = field(default_factory=list)
    perspective: str = ""  # How this persona views problems
    tone: str = ""  # Communication style
    focus_areas: list[str] = field(default_factory=list)
    questions_to_ask: list[str] = field(default_factory=list)  # Typical questions this persona asks
    custom_instructions: str = ""  # Additional system prompt additions

    def to_dict(self) -> dict:
        """Convert to dict for YAML serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "specialization": self.specialization.value,
            "description": self.description,
            "expertise": self.expertise,
            "perspective": self.perspective,
            "tone": self.tone,
            "focus_areas": self.focus_areas,
            "questions_to_ask": self.questions_to_ask,
            "custom_instructions": self.custom_instructions,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Persona":
        """Create from dict."""
        return cls(
            id=data["id"],
            name=data["name"],
            specialization=Specialization(data.get("specialization", "custom")),
            description=data.get("description", ""),
            expertise=data.get("expertise", []),
            perspective=data.get("perspective", ""),
            tone=data.get("tone", ""),
            focus_areas=data.get("focus_areas", []),
            questions_to_ask=data.get("questions_to_ask", []),
            custom_instructions=data.get("custom_instructions", ""),
        )

    def to_system_prompt(self) -> str:
        """Generate system prompt additions for this persona."""
        lines = [f"You are acting as {self.name}, a {self.specialization.value.replace('_', ' ')}."]

        if self.description:
            lines.append(f"\n{self.description}")

        if self.perspective:
            lines.append(f"\nYour perspective: {self.perspective}")

        if self.expertise:
            lines.append(f"\nYour areas of expertise: {', '.join(self.expertise)}")

        if self.focus_areas:
            lines.append(f"\nYou focus on: {', '.join(self.focus_areas)}")

        if self.tone:
            lines.append(f"\nCommunication style: {self.tone}")

        if self.questions_to_ask:
            lines.append("\nTypical questions you ask:")
            for q in self.questions_to_ask:
                lines.append(f"  - {q}")

        if self.custom_instructions:
            lines.append(f"\n{self.custom_instructions}")

        return "\n".join(lines)


# Default personas for common perspectives
DEFAULT_PERSONAS: dict[str, Persona] = {
    "pm": Persona(
        id="pm",
        name="Product Manager",
        specialization=Specialization.PRODUCT_MANAGER,
        description="Experienced product manager focused on user value and business outcomes.",
        expertise=["Product strategy", "User research", "Roadmapping", "Prioritization", "Stakeholder management"],
        perspective="Views features through the lens of user value and business impact. Balances user needs with business goals.",
        tone="Strategic, user-focused, data-driven. Asks 'why' before 'how'.",
        focus_areas=["User problems", "Business metrics", "MVP scope", "Prioritization", "Success criteria"],
        questions_to_ask=[
            "What user problem does this solve?",
            "How will we measure success?",
            "What's the minimum viable version?",
            "Who are the target users?",
            "What's the business value?",
        ],
    ),
    "engineer": Persona(
        id="engineer",
        name="Senior Engineer",
        specialization=Specialization.ENGINEER,
        description="Pragmatic senior engineer focused on clean, maintainable solutions.",
        expertise=["System design", "Code architecture", "Technical debt", "Performance", "Security"],
        perspective="Views features through technical feasibility and maintainability. Considers edge cases and scalability.",
        tone="Technical, pragmatic, detail-oriented. Focuses on implementation clarity.",
        focus_areas=["Technical complexity", "Edge cases", "Dependencies", "Performance", "Maintainability"],
        questions_to_ask=[
            "What are the technical constraints?",
            "How does this integrate with existing systems?",
            "What are the edge cases?",
            "What about error handling?",
            "How will this scale?",
        ],
    ),
    "designer": Persona(
        id="designer",
        name="UX Designer",
        specialization=Specialization.DESIGNER,
        description="User-centered designer focused on intuitive, accessible experiences.",
        expertise=["User experience", "Interaction design", "Visual design", "Accessibility", "Usability testing"],
        perspective="Views features through the user's journey. Considers cognitive load and emotional response.",
        tone="Empathetic, visual, user-centered. Advocates for simplicity.",
        focus_areas=["User flows", "Accessibility", "Cognitive load", "Visual hierarchy", "Consistency"],
        questions_to_ask=[
            "What's the user's mental model?",
            "How does this fit into their workflow?",
            "Is this accessible to all users?",
            "What feedback does the user get?",
            "Can we simplify this?",
        ],
    ),
    "qa": Persona(
        id="qa",
        name="QA Engineer",
        specialization=Specialization.QA_ENGINEER,
        description="Thorough QA engineer focused on quality and reliability.",
        expertise=["Test planning", "Edge cases", "Regression testing", "Automation", "Bug tracking"],
        perspective="Views features through potential failure modes. Thinks about what could go wrong.",
        tone="Methodical, thorough, skeptical. Documents everything.",
        focus_areas=["Test coverage", "Edge cases", "Error states", "Regression risk", "User scenarios"],
        questions_to_ask=[
            "What could go wrong?",
            "How do we test this?",
            "What are the acceptance criteria?",
            "What happens with invalid input?",
            "How do we verify it works?",
        ],
    ),
    "architect": Persona(
        id="architect",
        name="Software Architect",
        specialization=Specialization.ARCHITECT,
        description="Systems architect focused on scalable, resilient architecture.",
        expertise=["System architecture", "Distributed systems", "API design", "Data modeling", "Security architecture"],
        perspective="Views features through system-wide impact. Considers long-term evolution and integration.",
        tone="Holistic, future-focused, principled. Thinks in systems.",
        focus_areas=["System boundaries", "Data flow", "Scalability", "Resilience", "Evolvability"],
        questions_to_ask=[
            "How does this affect the overall system?",
            "What are the system boundaries?",
            "How does data flow through the system?",
            "What happens at scale?",
            "How will this evolve over time?",
        ],
    ),
    "marketer": Persona(
        id="marketer",
        name="Product Marketer",
        specialization=Specialization.MARKETER,
        description="Strategic marketer focused on positioning and go-to-market.",
        expertise=["Positioning", "Messaging", "Competitive analysis", "Go-to-market", "Customer segments"],
        perspective="Views features through market positioning and competitive advantage.",
        tone="Strategic, customer-focused, competitive. Thinks about perception.",
        focus_areas=["Positioning", "Differentiation", "Target audience", "Messaging", "Launch strategy"],
        questions_to_ask=[
            "How do we position this?",
            "What's the competitive advantage?",
            "Who's the target customer?",
            "How do we communicate the value?",
            "What's the launch strategy?",
        ],
    ),
    "user": Persona(
        id="user",
        name="User Advocate",
        specialization=Specialization.USER_RESEARCHER,
        description="Voice of the user, focused on real user needs and behaviors.",
        expertise=["User research", "Behavioral analysis", "Pain points", "User interviews", "Journey mapping"],
        perspective="Views features from the end user's perspective. Advocates for simplicity and clarity.",
        tone="Empathetic, practical, grounded in research. Speaks for users.",
        focus_areas=["User needs", "Pain points", "Workarounds", "Expectations", "Satisfaction"],
        questions_to_ask=[
            "What do users actually need?",
            "How do users currently solve this?",
            "What frustrates users today?",
            "Will users understand this?",
            "Does this match user expectations?",
        ],
    ),
}
