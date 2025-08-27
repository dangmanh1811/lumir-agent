# Lumir Agent - Numerology Workflow

Automatic numerology analysis system with AWS S3 integration and DSPy framework.

## 🌟 Key Features

- **Complete Numerology Analysis**: Calculate life path, soul, personality, balance, and maturity numbers
- **AWS S3 Integration**: Automatically retrieve detailed information from S3 for each number
- **Smart Workflow**: 3-step processing with analyze → execute → checker
- **Vietnamese Support**: Vietnamese alphabet and name processing
- **Quality Control**: Automatic evaluation and content moderation

## 📋 System Requirements

- Python 3.8+
- AWS S3 access (with configured credentials)
- DSPy framework

## 🚀 Installation

1. **Clone repository**:
```bash
git clone <repository-url>
cd lumir-agent
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure AWS credentials**:
```bash
# Create .env file
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=ap-southeast-1
```

4. **Configure DSPy**:
```python
import dspy
# Configure your LM
lm = dspy.OpenAI(model="gpt-3.5-turbo")
dspy.settings.configure(lm=lm)
```

## 💡 Quick Usage

### Basic Test
```bash
python test/test_numerology_workflow.py
```

### Use in Code
```python
from lumir.src.core.agent.agent_loader import NumerologyNodeAgentLoader

# Initialize agent
agent = NumerologyNodeAgentLoader()

# Input data
data = {
    "name": "John Doe",
    "birth_date": "15/05/1990",  # Format: dd/mm/yyyy
    "question": "What does my future hold?"
}

# Run workflow
analysis = agent.analyze_agent(data)
execution = agent.execute_agent(data)
checker = agent.checker_agent({
    "analysis_result": str(analysis),
    "execute_result": str(execution),
    "original_question": data['question']
})

print(f"Result: {execution}")
print(f"Status: {checker.states}")
```

## 📁 Project Structure

```
lumir-agent/
├── config/
│   ├── workflow.json          # Workflow configuration
│   └── agent_node/
│       └── numerogy.json      # Numerology agent configuration
├── lumir/
│   └── src/
│       ├── core/
│       │   └── agent/
│       └── utils/
├── test/
│   ├── test_numerology_workflow.py # Complete demo
│   └── test_signature.py
├── requirements.txt
└── README.md
```

## 🔧 Configuration

### Workflow Configuration (workflow.json)
```json
{
  "nodes": [
    {
      "id": "numerology",
      "type": "agent",
      "name": "Numerology Analysis",
      "description": "Comprehensive numerology analysis with S3 context integration",
      "config": {
        "agent_type": "numerology",
        "config_path": "config/agent_node/numerogy.json"
      },
      "inputs": ["name", "birth_date", "question"],
      "outputs": ["analysis_result", "execute_result", "checker_result"]
    }
  ]
}
```

### Agent Configuration (numerogy.json)
Contains DSPy signatures and prompts for:
- Analysis agent
- Execution agent  
- Checker agent

## 📊 Supported Numerology Numbers

| Number Type | Description | Calculation Method |
|-------------|-------------|--------------------|
| Life Path | Main life direction | Sum of birth date digits |
| Soul Number | Inner desires | Sum of vowels in name |
| Personality | External expression | Sum of consonants in name |
| Balance | Life balance | Sum of all name letters |
| Maturity | Later life development | Life Path + Soul Number |

## 🧪 Testing

### Simple Test
```bash
python test/test_numerology_workflow.py
```

### Full Demo with Multiple Test Cases
```bash
python demo_numerology_workflow.py
```

## 🔍 Troubleshooting

### Common Issues

1. **AWS S3 Connection Error**
   - Check AWS credentials in .env file
   - Verify S3 bucket permissions
   - Ensure correct region configuration

2. **DSPy Configuration Error**
   - Verify LM model configuration
   - Check API keys and quotas
   - Ensure proper DSPy version

3. **Import Errors**
   - Check Python path configuration
   - Verify all dependencies are installed
   - Ensure correct file structure

4. **Numerology Calculation Issues**
   - Verify name format (Vietnamese characters supported)
   - Check birth date format (dd/mm/yyyy)
   - Ensure proper encoding for special characters

## 📝 Changelog

### Version 1.0.0
- Initial release with complete numerology workflow
- AWS S3 integration for context sources
- Vietnamese name processing support
- Quality control with checker agent

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Contact

For questions or support, please contact the Lumir team.

---

**Note**: This system is designed for educational and entertainment purposes. Numerology interpretations should not be used as the sole basis for important life decisions.