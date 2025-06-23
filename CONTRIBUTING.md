# Contributing to AuditAI | 为AuditAI贡献代码

Thank you for your interest in contributing to AuditAI! We welcome contributions from the community.

感谢您对为AuditAI贡献代码的兴趣！我们欢迎社区的贡献。

## How to Contribute | 如何贡献

### Reporting Issues | 报告问题

**English:**
- Search existing issues before creating a new one
- Use the issue template when available
- Provide clear reproduction steps
- Include environment details (OS, Python version, etc.)

**中文:**
- 在创建新问题前搜索现有问题
- 如有可用模板请使用问题模板
- 提供清晰的重现步骤
- 包含环境详情（操作系统、Python版本等）

### Development Setup | 开发环境设置

```bash
# 1. Fork and clone the repository | 复制并克隆仓库
git clone https://github.com/your-username/AuditAI.git
cd AuditAI

# 2. Create virtual environment | 创建虚拟环境
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install development dependencies | 安装开发依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If available

# 4. Set up pre-commit hooks | 设置预提交钩子
pre-commit install

# 5. Run tests to ensure everything works | 运行测试确保一切正常
python -m pytest tests/
```

### Code Style | 代码风格

**English:**
- Follow PEP 8 Python style guide
- Use meaningful variable and function names
- Add docstrings to public functions and classes
- Keep functions small and focused
- Use type hints where appropriate

**中文:**
- 遵循PEP 8 Python风格指南
- 使用有意义的变量和函数名
- 为公共函数和类添加文档字符串
- 保持函数小而专注
- 适当使用类型提示

### Testing | 测试

**English:**
- Write tests for new features
- Ensure all tests pass before submitting PR
- Aim for good test coverage
- Test with different Python versions if possible

**中文:**
- 为新功能编写测试
- 提交PR前确保所有测试通过
- 力求良好的测试覆盖率
- 如可能，使用不同Python版本测试

### Pull Request Process | 拉取请求流程

**English:**
1. Create a feature branch from `main`
2. Make your changes
3. Add tests for new functionality
4. Update documentation if needed
5. Ensure all tests pass
6. Submit a pull request with a clear description

**中文:**
1. 从`main`分支创建功能分支
2. 进行修改
3. 为新功能添加测试
4. 如需要更新文档
5. 确保所有测试通过
6. 提交带有清晰描述的拉取请求

### Commit Messages | 提交信息

Use conventional commit format:

使用传统提交格式：

```
type(scope): description

feat(agents): add collaborative processing for InfoExtractAgent
fix(storage): resolve GCS authentication issue
docs(readme): update installation instructions
test(pipeline): add unit tests for multi-agent collaboration
```

### Agent Development | 智能体开发

**English:**
When contributing new agents:
- Inherit from `BaseAgent` class
- Implement required methods: `process()`
- Add collaborative methods if needed
- Include comprehensive docstrings
- Add unit tests for agent functionality

**中文:**
贡献新智能体时：
- 继承`BaseAgent`类
- 实现必需方法：`process()`
- 如需要添加协作方法
- 包含全面的文档字符串
- 为智能体功能添加单元测试

### Documentation | 文档

**English:**
- Update README.md for significant changes
- Add docstrings to new functions and classes
- Include examples in docstrings
- Update API documentation
- Maintain bilingual documentation (English/Chinese)

**中文:**
- 重大更改时更新README.md
- 为新函数和类添加文档字符串
- 在文档字符串中包含示例
- 更新API文档
- 维护双语文档（英语/中文）

## Community Guidelines | 社区准则

**English:**
- Be respectful and inclusive
- Help others learn and grow
- Provide constructive feedback
- Follow the code of conduct
- Focus on what's best for the community

**中文:**
- 保持尊重和包容
- 帮助他人学习和成长
- 提供建设性反馈
- 遵循行为准则
- 专注于对社区最好的事情

## Getting Help | 获取帮助

**English:**
- Check the documentation first
- Search existing issues and discussions
- Ask questions in GitHub Discussions
- Join our community channels

**中文:**
- 首先查看文档
- 搜索现有问题和讨论
- 在GitHub讨论中提问
- 加入我们的社区频道

## Recognition | 致谢

**English:**
All contributors will be recognized in our Contributors section. Thank you for helping make AuditAI better!

**中文:**
所有贡献者将在我们的贡献者部分得到认可。感谢您帮助改进AuditAI！

---

## Technical Requirements | 技术要求

### Minimum Requirements | 最低要求
- Python 3.8+
- Google Cloud SDK (for GCS features)
- Valid Gemini API key

### Recommended Development Tools | 推荐开发工具
- Visual Studio Code with Python extension
- Git for version control
- Docker (for containerized development)
- pytest for testing

---

Thank you for contributing! | 感谢您的贡献！ 