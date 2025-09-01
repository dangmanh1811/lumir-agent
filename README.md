# Lumir Agent Framework

A flexible framework for creating multi-agent systems using JSON configuration files. This framework allows you to load and orchestrate multiple agents in a chain with feedback loops and external data integration.

## Features

- **Agent Node System**: Create and manage multiple agents in a chain
- **JSON Configuration**: Define agents using intuitive JSON configuration files
- **Feedback Loop**: Built-in evaluation system with iterative improvement
- **External Data Integration**: Connect with external data sources
- **Multiple Agent Types**: Supports ChainOfThought, Predict, and ReAct patterns
- **Logging and Monitoring**: Comprehensive logging system

## Table of Contents

- [Setup](#setup)
  - [Environment Variables](#environment-variables)
  - [Installation](#installation)
- [Configuration](#configuration)
  - [JSON Config Structure](#json-config-structure)
  - [Agent Configuration Details](#agent-configuration-details)
- [Usage](#usage)
  - [Basic Usage](#basic-usage)
  - [Testing with Numerogy Workflow](#testing-with-numerogy-workflow)
- [Workflow](#workflow)
  - [Execution Flow](#execution-flow)
  - [Data Flow](#data-flow)
- [Examples](#examples)
- [License](#license)

## Setup

### Environment Variables

Create a `.env` file in the project root with the following configuration:

```env
# API Configuration
API_KEY='your_nvidia_api_key_here'
BASE_URL='https://integrate.api.nvidia.com/v1'
MODEL_NAME='moonshotai/kimi-k2-instruct'
TEMPERATURE=0.5
MAX_TOKENS=4096

# AWS Configuration (Optional for external data)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=ap-southeast-2
BUCKET_NAME=your_bucket_name
AWS_ENDPOINT_URL=https://s3.ap-southeast-2.amazonaws.com
```

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd lumir-agent
```

2. Set up conda environment:
```bash
conda create -n agent_env python=3.9
conda activate agent_env
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your actual API keys and configuration
```

## Configuration

### JSON Config Structure

The framework uses JSON configuration files to define agent chains. Each configuration file contains a list of agent dictionaries:

```json
[
  {
    "name": "analyze_agent_0",
    "objective_instruction": "Description of the agent's purpose",
    "input": {
      "field_name": "Field description"
    },
    "output": {
      "field_name": "Field description"
    }
  },
  {
    "name": "execute_agent_0",
    "objective_instruction": "Description of the agent's purpose",
    "input": {
      "field_name": "Field description"
    },
    "output": {
      "field_name": "Field description"
    }
  }
]
```

### Agent Configuration Details

Each agent has the following fields:

- **name**: Unique identifier for the agent
- **objective_instruction**: Clear description of the agent's purpose and behavior
- **input**: Dictionary defining input fields with descriptions
- **output**: Dictionary defining output fields with descriptions

## Usage

### Basic Usage

```python
from lumir.src.core.agent.agent_loader import AgentNode
import json

# Load configuration
with open('config/agent_node/your_config.json', 'r', encoding='utf-8') as f:
    config_data = json.load(f)

# Create agent node
agent_node = AgentNode(config_data)

# Display agent chain info
agent_node.get_agent_chain_info()

# Execute with input data
input_data = {
    "user_question": "Your question here"
}

# Execute with optional external function
result = agent_node.execute(input_data, external_function=your_external_function)
```

### Testing with Numerogy Workflow

The repository includes a numerology workflow example:

```bash
# Run the numerogy test
python -m test.test_numerogy_node
```

This demonstrates:
- Multi-agent execution with feedback loops
- External data integration (AWS S3)
- Agent chain orchestration

## Workflow

### Execution Flow

The framework executes agents in a sequential chain with the following pattern:

1. **Analyze Agent**: Analyzes user input and creates a plan
2. **External Data Retrieval**: If provided, fetches external data based on keywords
3. **Execute Agent**: Generates response based on plan and external data
4. **Checker Agent**: Evaluates response quality and provides feedback
5. **Iterative Improvement**: If feedback indicates missing steps, the execute agent tries again

### Data Flow

```
User Input → Analyze Agent → External Data → Execute Agent → Checker Agent -> Execute Agent
                                                ↑                    ↑
                                                └─── Feedback Loop ──┘
```

## Examples

### Numerogy Configuration Example

The `config/agent_node/numerogy_v2.json` file demonstrates a complete numerology workflow:

- **Analyze Agent**: Extracts relevant numerology keywords and creates a plan
- **Execute Agent**: Provides personalized numerology advice
- **Checker Agent**: Evaluates response quality and ensures completeness

### Configuration Files

- `config/agent_node/numerogy_v2.json`: Numerology workflow configuration
- `test/test_numerogy_node.py`: Test implementation
- `.env`: Environment configuration

## Demo Results

The numerogy workflow test produces comprehensive insights based on the user's question about trading recommendations. The framework successfully:

1. Analyzes the user's question and identifies relevant numerology indicators
2. Retrieves external data (though the example shows placeholder data)
3. Generates personalized advice with:
   - Specific daily trading guidance
   - Monthly context analysis
   - Attitude recommendations
   - Actionable trading strategies
4. Ensures response quality through iterative evaluation

## License

This project is licensed under the appropriate license terms.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

For issues and questions, please create an issue in the GitHub repository.