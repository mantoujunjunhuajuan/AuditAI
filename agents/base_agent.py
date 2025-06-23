"""Base class for all agents in the pipeline."""
from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseAgent(ABC):
    """Abstract base class for all agents in the pipeline."""

    @abstractmethod
    def process(self, input_data: Any) -> Any:
        """
        The main processing method for an agent.

        Args:
            input_data: The input data for the agent to process. The type will
              vary depending on the agent's position in the pipeline.

        Returns:
            The output data from the agent's processing. The type will also
            vary.
        """
        pass 